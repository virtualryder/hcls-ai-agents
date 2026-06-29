# Incident Response & Key Management — HCLS AI Agent Suite

> For the SI/customer security team operating the deployed suite. Pairs with `runbooks/INCIDENT-RESPONSE.md`
> (ops procedures) and `SECURITY.md` (vuln reporting). NIST IR-4/5/6/8 and SC-12/13/28.

## 1. Incident response

### Detect
- **Audit anomalies:** spikes in `DENY` / `PENDING_APPROVAL` / `ERROR` in the append-only audit table.
- **Guardrail blocks:** rising Bedrock Guardrail intervention rate (possible injection / PHI attempts).
- **Grounding failures:** rising grounding-rejection rate (possible poisoning / model drift).
- **Auth failures:** JWT verification failures, role-mapping mismatches.
- Wire CloudWatch alarms on these (customer-owned; thresholds per environment).

### Triage & classify
1. PHI exposure? → highest severity; engage privacy officer + BAA obligations.
2. Unauthorized action attempt? → check the audit lineage (actor, tool, decision, args_hash).
3. Integrity (hallucination/poisoning)? → quarantine the corpus; re-run grounding evals.

### Contain
- Revoke the affected IdP principal / Cognito session.
- Rotate the implicated secret/key (see §2) and the gateway token-signing secret.
- If a connector is implicated, set `ConnectorMode=fixture` to sever live SoR access while investigating.
- The **audit trail is append-only + WORM** — preserve it; it is the evidence.

### Evidence & notify
- Export the relevant append-only audit records (immutable; tamper-evident) and Guardrail logs.
- Notify per the customer's policy and BAA timelines; do not make confidentiality assurances the
  deployment cannot keep.

### Recover & learn
- Re-deploy from IaC (idempotent); restore from WORM where needed.
- Post-incident: bump the prompt manifest if prompts changed; add a red-team scenario for the new vector;
  update alarm thresholds.

## 2. Key & secret management (SC-12/13/28)

| Material | Where | Lifecycle |
|---|---|---|
| **KMS CMK per data class** | `infra/cloudformation/security.yaml` | Customer-owned; enable annual rotation; least-privilege key policy; audit via CloudTrail |
| **Connector / SoR credentials** | AWS Secrets Manager (`hcls/<system>_api_token`) | Customer-owned; rotate on schedule + on incident; never in code or prompts |
| **Gateway scoped-token secret** | `GATEWAY_TOKEN_SECRET` (HMAC, dev) → AgentCore Identity / STS (prod) | Ephemeral per-process in dev; managed/rotated in prod |
| **Approval-token secret** | `APPROVAL_TOKEN_SECRET` (HMAC) | Server-side only; the reviewer never holds it; rotate on incident |
| **Cognito / IdP signing keys** | Customer IdP + Cognito | Customer-owned; JWKS rotation honored automatically by `auth.py` |

**Rules:** no standing service accounts; tokens are short-lived and per-call; secrets resolve via Secrets
Manager (env fallback only in dev with `DISABLE_SECRETS_MANAGER=1`); KMS encrypts every data class at rest;
TLS 1.3 in transit; Bedrock inference stays in-VPC (no patient-data egress).
