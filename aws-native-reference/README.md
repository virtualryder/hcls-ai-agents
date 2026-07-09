# AWS-Native Reference Deployments

AWS-native deployment of every agent in the suite. The goal is **"keep LangGraph,
add AWS-native deployment and governance"** — not a rewrite. The reusable engine
lives in [`_shared/`](./_shared/); the headline IaC is CloudFormation in
[`../infra/cloudformation`](../infra/cloudformation).

## Two paths to AWS (per agent)

1. **Container lift** (all 9) — containerize the agent's compiled LangGraph and run
   it on **Amazon Bedrock AgentCore Runtime** (or ECS Fargate), implementing the
   AgentCore container contract (`/invocations`, `/ping`, port 8080, ARM64).
   Inference is served by **Bedrock + Guardrails**, reached over **AWS PrivateLink** (regional service, not in-VPC hosting). Fastest; code unchanged.
2. **Native rebuild** — deterministic core in Lambdas + **Strands Agents SDK**
   drafting on Bedrock + **Step Functions** orchestration with a `waitForTaskToken`
   HITL gate. Highest fidelity to the managed, serverless target.

The **MCP layer is Amazon Bedrock AgentCore Gateway + AgentCore Identity**
(`../infra/cloudformation/agentcore-gateway.yaml`); `platform_core/mcp_gateway` is
the deterministic reference for its authorize → token → audit semantics.

## Agent registry

| Agent | Folder | Source agent | Paths |
|---|---|---|---|
| 01 · Regulatory Writing | [`01-regulatory-writing/`](./01-regulatory-writing/) | `01-regulatory-writing-agent` | Container + Native |
| 02 · Pharmacovigilance | `02-pharmacovigilance/` | `02-pharmacovigilance-agent` | Container + Native |
| 03 · Clinical Trial Ops | `03-clinical-trial-ops/` | `03-clinical-trial-ops-agent` | Container + Native |
| 04 · Site & Patient Matching | `04-site-patient-matching/` | `04-site-patient-matching-agent` | Container + Native |
| 05 · Quality & CAPA | `05-quality-capa/` | `05-quality-capa-agent` | Container + Native |
| 06 · Protocol Design | `06-protocol-design/` | `06-protocol-design-agent` | Container + Native |
| 07 · RWE / HEOR | `07-rwe-heor/` | `07-rwe-heor-agent` | Container + Native |
| 08 · Medical Affairs / MSL | `08-medical-affairs-msl/` | `08-medical-affairs-msl-agent` | Container + Native |

## Deploy
- One agent: see its folder `DEPLOY.md` (01 is the worked reference).
- Everything: [`DEPLOY-ALL.md`](./DEPLOY-ALL.md) + `../infra/cloudformation`.

## Maturity
**All nine agents** ship both a container-lift path and a native rebuild (deterministic
core in Lambdas + Strands drafting on Bedrock + Step Functions with a `waitForTaskToken`
human gate). The native cores are **Demonstrated** — run and unit-tested without AWS (155
native tests pass across the nine rebuilds) — and **Deployable-by-design** (ARM64 runtime
+ CloudFormation + Step Functions). They become *Deployed* once an account builds/pushes
images and applies the IaC. Live Bedrock inference is wired and demonstrated for Agent 02
(`02-pharmacovigilance-agent/demo/`); a penetration test and full CSV are engagement steps.
