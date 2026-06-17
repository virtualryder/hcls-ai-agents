# Deploy — Regulatory Writing (native)

## Prerequisites
- AWS account with Amazon Bedrock model access (Claude) + a Guardrail.
- Step Functions, Lambda, DynamoDB, ECR permissions.

## 1. Package Lambdas
```bash
cd aws-native-reference/01-regulatory-writing
zip -r build/lambdas.zip core.py strands_agent.py lambdas/ requirements.txt
```

## 2. Deploy the stack (CloudFormation)
The agent-level resources (state machine, 5 Lambdas, review table, IAM) are
provisioned by the suite CloudFormation with `AgentId=01-regulatory-writing`:

```bash
aws cloudformation deploy \
  --template-file ../../infra/cloudformation/quickstart.yaml \
  --stack-name hcls-regwriting \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=01-regulatory-writing Environment=dev \
    DeployMode=native BedrockGuardrailId=$GID
```

## 3. Run an execution
```bash
aws stepfunctions start-execution \
  --state-machine-arn <arn> \
  --input file://sample_input.json
```

## 4. Approve at the human gate
The execution pauses at `HumanReviewGate`. The review UI reads the task token from
the review table; a Regulatory Approver approves with their verified identity:

```bash
aws stepfunctions send-task-success \
  --task-token <token> \
  --task-output '{"approved": true, "reviewer": {"sub": "approver-1"}}'
```

`Finalize` then creates the RIM submission draft (gateway-authorized) and locks
the audit trail.
