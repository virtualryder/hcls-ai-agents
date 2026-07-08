# Terraform & GovCloud status — HCLS Life Sciences AI Agent Suite

**Honest status.** CloudFormation/SAM is the **canonical, validated** IaC for this suite (all nine
golden paths were deployed and torn down in a live account — see
[`../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md) and
[`GOLDEN-PATH-DEPLOY-NOTES.md`](GOLDEN-PATH-DEPLOY-NOTES.md)). The Terraform under `infra/terraform/`
is **a reference skeleton, not at parity** with the CloudFormation deploy. Earlier docs said
"Terraform parity"; that overstated it and has been corrected. This document is the accurate picture.

## Coverage: Terraform vs the CloudFormation deploy

The Terraform reproduces ~7 AWS resource *types*; the CloudFormation templates use ~47. What the
skeleton covers vs. what it does not:

| Control / resource | CloudFormation | Terraform skeleton |
|---|---|---|
| VPC + subnets | ✅ (full network) | ⚠️ VPC + subnet only (no endpoints/NAT/flow logs) |
| KMS CMK | ✅ | ✅ |
| DynamoDB audit | ✅ (append-only) | ✅ (table only) |
| Bedrock Guardrail | ✅ | ✅ |
| Step Functions | ✅ | ✅ (state machine) |
| IAM roles | ✅ (least-privilege) | ⚠️ role scaffold |
| MCP gateway (API GW + Cognito JWT authorizer) | ✅ (portable) + AgentCore (experimental) | ❌ absent |
| Cognito user pool / IdP federation | ✅ | ❌ absent |
| Lambda functions | ✅ | ❌ absent |
| S3 WORM (Object Lock) | ✅ | ❌ absent |
| VPC interface endpoints (PrivateLink) | ✅ | ❌ absent |

**Bottom line:** the Terraform is a *minimal skeleton* (network + data + guardrail + a state machine).
The governed front door (gateway, identity, Lambdas, WORM) is **CloudFormation-only** today.

## GovCloud posture

- There is **no GovCloud Terraform overlay** in this repo (unlike the SLG suite). GovCloud is not
  currently addressed in HCLS Terraform.
- If pursued, the same constraint applies as elsewhere: Bedrock + Guardrails + Knowledge Bases are
  available in GovCloud, but AgentCore Gateway was not yet in GovCloud as of 2026-05, so a GovCloud
  deployment would use the **portable** API-Gateway-+-Cognito gateway path. This is engagement work
  and has not been built or deployed.

## What "done" would require (engagement-owned)

Grow the Terraform to the CloudFormation resource set (gateway + authorizer, Cognito + IdP federation,
Lambdas, WORM S3, VPC endpoints, append-only audit IAM deny), then `terraform validate` / `plan` /
`apply` in a commercial account. Until then, **deploy with CloudFormation/SAM** (the canonical path);
Terraform is reference only.
