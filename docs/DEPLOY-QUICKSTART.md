# HCLS Agent Suite — Deploy Quickstart

### From an empty customer AWS account to a running, governed, human-gated agent

> **Who this is for:** the systems-integrator engineer standing the suite up in a
> **brand-new customer AWS account**. Follow it top to bottom and you will have one
> agent live, behind a governed MCP gateway, with a working human-approval gate and a
> tamper-evident audit trail. Everything is copy-paste.
>
> **Time:** ~30–60 minutes once Bedrock model access is granted.
> **Cost:** a few dollars/day in dev (serverless + pay-per-request); see `offerings/TCO-MODEL.md`.

This is the short, opinionated path. For the deep console click-through with screenshots,
per-control explanations, and the full per-agent appendix, use
[`DEPLOYMENT-HANDBOOK.md`](DEPLOYMENT-HANDBOOK.md). For operations after go-live, use
[`../runbooks/`](../runbooks/).

---

## 0. What you are about to deploy

One CloudFormation master stack (`infra/cloudformation/quickstart.yaml`) provisions a
**customer-isolated environment** from nested stacks:

| Layer | Stack | What it is |
|---|---|---|
| Network | `network.yaml` | VPC, private/public subnets, NAT, app security group |
| Security | `security.yaml` | KMS CMK, **Bedrock Guardrail** (PHI + off-label), **Cognito** (IdP federation + app client), least-privilege agent role |
| Data | `data.yaml` | Append-only **DynamoDB audit**, **S3 Object Lock** WORM store, HITL review table |
| **Connectors** | `connectors.yaml` | One **connector Lambda per system of record** — the governed backend behind every gateway target |
| **MCP gateway** | `gateway-portable.yaml` **or** `agentcore-gateway.yaml` | The governed front door (you pick the path — see §3) |
| **The agent** | `agent-service.yaml` | The agent itself: **native** (Step Functions + Lambdas + human gate) or **container** (ECS Fargate) |

Two independent choices you will make:

- **`GatewayMode`** — `portable` (any region, recommended for a new account) or `agentcore` (managed, AgentCore regions only). Both enforce the **same** deny-by-default policy. See §3.
- **`DeployMode`** — `native` (serverless workflow with a framework-enforced human gate) or `container` (lift the LangGraph agent onto ECS Fargate). See §5.

---

## 1. Prerequisites

On your machine:

```bash
aws --version            # AWS CLI v2
python3 --version        # 3.11+
docker version           # only for DeployMode=container
aws sts get-caller-identity   # confirm you're in the CUSTOMER account
```

In the customer account (one-time):

1. **Enable Amazon Bedrock model access** for Claude in your target Region
   (Bedrock console → *Model access* → enable the Anthropic Claude models). Without this,
   every inference call returns `AccessDenied`.
   ```bash
   aws bedrock list-foundation-models --region us-east-1 \
     --query "modelSummaries[?contains(modelId,'anthropic.claude')].modelId" --output table
   ```
2. **Pick a Region.** For `GatewayMode=portable` any commercial Region works. For
   `GatewayMode=agentcore`, choose an AgentCore-enabled Region (e.g. `us-east-1`).
3. **Have the customer IdP metadata URL** ready (Okta/Entra/AD SAML or OIDC) if you are
   wiring federation now — optional in dev, required for prod.

---

## 2. Build the deployable artifacts (one command)

The agent and connector code must travel to AWS **with their dependencies vendored in**
(this is the step people miss — function source alone hits `ImportError` on cold start).
One script does it for every agent plus the shared connector:

```bash
scripts/build_lambdas.sh                 # all agents + connector
# or just one agent:
scripts/build_lambdas.sh 02-pharmacovigilance
```

Outputs:

```
aws-native-reference/_shared/connector/build/connector.zip      # backs every gateway target
aws-native-reference/<AgentId>/build/lambdas.zip                # the native workflow Lambdas
```

> Container mode instead needs an image — see §5b.

---

## 3. Choose your MCP gateway path

Both paths put **every** system-of-record call through the same governed connector
Lambda (deny-by-default authorization, least-privilege intersection of *agent grant ∩ user
entitlement*, human-approval gate on writes, scoped tokens, PHI-masked append-only audit).
They differ only in the front door.

| | **Path A — Portable** (`GatewayMode=portable`) | **Path B — Managed** (`GatewayMode=agentcore`) |
|---|---|---|
| Front door | API Gateway (HTTP API) + Cognito JWT authorizer | Amazon Bedrock **AgentCore Gateway + Identity** |
| Region support | **Any commercial Region** | AgentCore-enabled Regions only |
| New-account friction | None — deploys day one | Requires AgentCore availability |
| Call shape | `POST {endpoint}/mcp/<kind>` with a Cognito JWT | Native MCP target invocation |
| When to use | **Default. Start here in a new account.** | Customer standardizing on AgentCore managed runtime |

You can migrate Path A → Path B later without touching agent or connector code — only the
gateway stack changes.

---

## 4. Deploy (one command)

```bash
CFN_BUCKET=<your-templates-bucket> CODE_BUCKET=<your-code-bucket> \
  scripts/deploy.sh 02-pharmacovigilance dev portable native
#                   ^AgentId            ^env ^GatewayMode ^DeployMode
```

`deploy.sh` creates the buckets if needed, stages the templates and the zips to S3, and
deploys the master stack with `CAPABILITY_NAMED_IAM`. It prints the stack **Outputs**
(`GatewayId`, `GatewayEndpoint`, `AuditTable`, `GuardrailId`) when done.

<details>
<summary>Prefer raw CloudFormation? The equivalent CLI call</summary>

```bash
aws s3 cp infra/cloudformation/ s3://$CFN_BUCKET/hcls/ --recursive --exclude "*" --include "*.yaml"
aws s3 cp aws-native-reference/_shared/connector/build/connector.zip s3://$CODE_BUCKET/connector.zip
aws s3 cp aws-native-reference/02-pharmacovigilance/build/lambdas.zip s3://$CODE_BUCKET/02-pharmacovigilance/lambdas.zip

aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-dev-02-pharmacovigilance \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      Environment=dev AgentId=02-pharmacovigilance \
      GatewayMode=portable DeployMode=native ConnectorMode=fixture \
      TemplateBaseUrl=https://$CFN_BUCKET.s3.amazonaws.com/hcls \
      LambdaCodeBucket=$CODE_BUCKET LambdaCodeKey=02-pharmacovigilance/lambdas.zip \
      ConnectorCodeKey=connector.zip
```
</details>

> Deploy starts in **`ConnectorMode=fixture`** (deterministic demo data) so you can validate
> the whole pipeline before touching a real vendor system. Switch to `live` in §7.

---

## 5. "Creating the agent itself"

The **agent** is the `agent-service.yaml` resource — what it *is* depends on `DeployMode`.

### 5a. Native (default) — the agent is a governed Step Functions workflow

`scripts/deploy.sh ... native` creates five Lambdas and a state machine
`hcls-<env>-<AgentId>`:

```
Assemble → Draft (Strands/Bedrock) → Check → RouteChoice → HumanReviewGate → Finalize
```

`HumanReviewGate` is a **`waitForTaskToken`** step: the workflow **pauses** there until a
qualified human approves. Nothing finalizes without it. This is the agent — no extra step
to "create" it; the stack did it. Go to §6.

### 5b. Container — the agent is an ECS Fargate service running your LangGraph graph

Use this to lift an agent's existing LangGraph code unchanged. Build and push the ARM64
image (the shared runtime implements the `/invocations` + `/ping` contract), then deploy
with `DeployMode=container`:

```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text); REGION=us-east-1
aws ecr create-repository --repository-name hcls-02-pharmacovigilance --region $REGION || true
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

# Build context = the agent folder + shared runtime + platform_core
docker buildx build --platform linux/arm64 \
  -t $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/hcls-02-pharmacovigilance:latest \
  -f aws-native-reference/_shared/runtime/Dockerfile . --push

CFN_BUCKET=... CODE_BUCKET=... scripts/deploy.sh 02-pharmacovigilance dev portable container
# deploy.sh passes ContainerImageUri / AgentModule through to agent-service.yaml
```

The resulting ECS service `hcls-<env>-<AgentId>` **is** the agent. In an AgentCore-enabled
Region you may register the same image with AgentCore Runtime instead — no code change.

---

## 6. Smoke-test the agent + the human gate (native)

```bash
SM_ARN=$(aws cloudformation describe-stacks --stack-name hcls-dev-02-pharmacovigilance \
  --query "Stacks[0].Outputs[?contains(OutputKey,'StateMachine')].OutputValue" --output text)

# 1) Start a run with the sample case
aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --input file://aws-native-reference/02-pharmacovigilance/sample_input.json

# 2) It PAUSES at HumanReviewGate (this is correct). The hitl_notify Lambda wrote the
#    task token + draft to the review table hcls-dev-review. Approve as the reviewer:
aws stepfunctions send-task-success \
  --task-token "<token-from-review-table>" \
  --task-output '{"approved": true, "reviewer": {"sub": "pv-physician-1", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}}'
```

The workflow resumes to `Finalize`, performs the gateway-authorized write with the
**approver bound into the record**, and seals the audit trail. Confirm it:

```bash
aws dynamodb scan --table-name hcls-dev-audit --max-items 5
```

You should see append-only entries with PHI masked, decisions (`ALLOW`/`PENDING_APPROVAL`),
and lineage to the system of record — your 21 CFR Part 11 evidence.

---

## 7. Connect a real system of record (when ready)

Still fixture-backed? Flip one agent to live without code changes:

1. Store the vendor credential:
   ```bash
   aws secretsmanager create-secret --name hcls/safety_api_token \
     --secret-string '<customer-safety-API-token>'
   ```
2. Redeploy with `ConnectorMode=live` and set the endpoint env var (e.g. `SAFETY_BASE_URL`)
   on the connector/Lambda. Point it at the bundled reference service first
   (`02-pharmacovigilance-agent/demo/reference_safety_service.py`) to validate the pipeline,
   then swap to the customer's Argus/Veeva gateway — a one-variable change.

Per-agent systems, high-risk tools, and approver roles are tabulated in
`DEPLOYMENT-HANDBOOK.md` §11.

---

## 8. Go-live checklist

Do not promote to prod until every box is checked:

- [ ] Bedrock model access granted; Guardrail attached and **tested** (submit a PHI string → blocked/anonymized).
- [ ] IdP federation live; approver group maps to `custom:hcls_role`; a non-approver is correctly **denied** a high-risk tool.
- [ ] `ConnectorMode=live` against the real system; a read and a (test) write both appear in the audit trail.
- [ ] HITL gate verified: the run pauses; finalize only runs after `send-task-success` with a verified reviewer.
- [ ] Audit trail is append-only (attempt an update/delete → denied); WORM retention set.
- [ ] `pytest` + `governance` evals captured as validation evidence; prompt manifest matches.
- [ ] `Environment=prod` set (forces the Guardrail mandatory); WAF enabled on any public endpoint.
- [ ] Runbooks reviewed with ops (`runbooks/`).

---

## 9. Deploy more agents

Shared stacks are reused; only the agent service + its gateway targets are per-agent:

```bash
for A in 01-regulatory-writing 03-clinical-trial-ops 05-quality-capa 08-medical-affairs-msl; do
  scripts/build_lambdas.sh $A
  CFN_BUCKET=... CODE_BUCKET=... scripts/deploy.sh $A dev portable native
done
```

---

## 10. Teardown (dev only)

```bash
aws cloudformation delete-stack --stack-name hcls-dev-02-pharmacovigilance
```

The **audit DynamoDB table** and the **S3 Object Lock (WORM) bucket** are created with
`Retain` deletion policies on purpose — regulated records must survive a stack deletion.
Remove them deliberately (dev only) after exporting anything you need. The WORM bucket
enforces COMPLIANCE-mode retention; objects cannot be deleted before the retention period.

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `AccessDeniedException` on Bedrock | Model access not granted in this Region | §1 step 1 |
| Stack fails on `AWS::BedrockAgentCore::*` | Region lacks AgentCore | Deploy `GatewayMode=portable` |
| Lambda `ImportError` on cold start | zip missing vendored deps | Re-run `scripts/build_lambdas.sh` (it `pip install -t`s deps) |
| Run stuck at `HumanReviewGate` | Working as designed | Send `send-task-success` with a verified reviewer (§6) |
| Tool call unexpectedly `DENY` | User role lacks entitlement, or agent isn't granted the tool | Check `AGENT_TOOL_GRANTS` / `ROLE_ENTITLEMENTS` in `platform_core/.../mcp_gateway/policy.py` and the Cognito role mapping |
| Connector raises `NotImplementedError` | `ConnectorMode=live` but that system's live adapter isn't wired | Implement the typed methods in `platform_core/.../connectors/live.py` (mirror `LiveSafetyConnector`); use `fixture` for the demo |
| `LLM factory refuses to start` | `Environment=prod` without a Guardrail ID | Set `BedrockGuardrailId` (this guard is intentional) |
