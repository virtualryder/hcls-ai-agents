# Security Policy

## Status & scope
This repository is a **governed reference accelerator** for Healthcare & Life Sciences (HCLS) agentic
AI on AWS. It is **not** an AWS-authorized, computer-system-validated (CSV/CSA), SOC 2, or HITRUST-certified
production system. The Python control plane is a **reference implementation** of the authorization,
approval, token, audit, and PHI-masking semantics; production deployments substitute the managed AWS
equivalents (Amazon Bedrock AgentCore Gateway/Identity, API Gateway + Cedar/Verified Permissions, STS,
KMS, DynamoDB, S3 Object Lock). See `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.

## Reporting a vulnerability
Report suspected vulnerabilities privately to the maintainer: **ryderdavid75@gmail.com** (subject:
`SECURITY — hcls-ai-agents`). Include affected file/commit, reproduction, and impact. Do **not** open a
public issue for an unfixed vulnerability. Target: acknowledgement within 5 business days; triage and
remediation plan within 15 business days. Coordinated disclosure is appreciated.

## In scope
- The Python control plane (`platform_core/`, `governance/`, `aws-native-reference/`).
- Infrastructure-as-code (`infra/`) — CloudFormation, the per-agent SAM golden paths, Terraform.
- The deny-by-default authorization model, the human-approval gate, scoped tokens, append-only audit,
  and PHI/PII masking.

## Out of scope (customer / deployer responsibility)
- The customer's identity provider (IdP) federation and entitlement source of truth.
- Live connectors to systems of record (Veeva Vault, Argus/Veeva Safety, Medidata, QMS, MES/LIMS).
- CSV/CSA validation, third-party penetration testing, SOC 2 / HITRUST, and continuous monitoring.
- Production secret material (KMS keys, token-signing keys), retention schedules, and DR.

## Security model (summary) — defense in depth, fail-closed by default
1. **Cryptographic identity** — RS256/JWKS JWT verification (`platform_core/hcls_agent_platform/auth.py`);
   client-supplied roles are never trusted in production.
2. **Deny-by-default authorization** — least privilege as the intersection *agent grant ∩ user entitlement*
   (`mcp_gateway/policy.py`).
3. **Consequential commits withheld from agents** — the irreversible regulated act (submit an ICSR, close a
   CAPA, release a batch) is **absent from every agent grant** (`policy.CONSEQUENTIAL_COMMITS`); only a bound
   human reviewer identity may commit. Enforced by a test.
4. **Bound human approval** — tamper-evident, single-use, separation-of-duties, args-bound approval tokens
   for high-risk writes (`mcp_gateway/approvals.py`); set `STRICT_APPROVAL=1` to require them in production.
5. **Scoped, short-lived tokens** — per-call, tool-scoped, ephemeral (`mcp_gateway/tokens.py`).
6. **Append-only audit + WORM** — DynamoDB append-only + S3 Object Lock (`infra/cloudformation/data.yaml`);
   every ALLOW/DENY/PENDING_APPROVAL/ERROR recorded with lineage (21 CFR Part 11 evidence).
7. **Fail-closed PHI/PII masking** (`phi.py`) **before** any model call or audit write; **Bedrock Guardrails**
   on input and output; **in-account inference** via VPC endpoint — no patient-data egress.
8. **Grounding verification** — every regulated figure/entity in an output must trace to the source corpus,
   or the step fails closed (`governance/grounding.py`).

Full threat model: `docs/THREAT-MODEL.md`. Control-to-NIST mapping: `docs/NIST-800-53-CONTROL-MATRIX.md`.
OWASP-LLM / MITRE ATLAS mapping: `docs/OWASP-LLM-ATLAS-MAPPING.md`. IR & key management:
`docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`.

## Supported versions
Pre-1.0 reference accelerator: only the latest `main` is supported. See `SUITE-STATUS.md`.
