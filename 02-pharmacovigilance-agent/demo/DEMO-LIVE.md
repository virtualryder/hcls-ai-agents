# DEMO-LIVE — Customer-Ready Live Path Runbook

Pharmacovigilance ICSR Agent · Amazon Bedrock AgentCore + Real Safety Connector

---

## What this proves

| Dimension | Fixture mode (CI/demo) | **Live mode (this runbook)** |
|---|---|---|
| Inference | No API calls | **Amazon Bedrock in-account** (or Anthropic API) |
| Safety DB | Deterministic stubs | **Real HTTP → Argus / Veeva / local ref service** |
| Audit | In-process log | **Immutable trail per call, with JTI-bound token** |
| HITL | Simulated | **Gateway blocks submit until reviewer approves** |
| PHI | Never leaves agent | **Never leaves AWS VPC (Bedrock VPC endpoint)** |

---

## Prerequisites

### Option A — Full live (Amazon Bedrock + real Argus/Veeva gateway)

1. **Bedrock model access** — enable Claude Sonnet and Haiku in your AWS account:
   - AWS Console → Bedrock → Model access → enable `anthropic.claude-sonnet-4-6-20260601-v1:0`
   - Repeat for `anthropic.claude-haiku-4-5-20251001`

2. **Bedrock Guardrail** (REQUIRED for production PHI content):
   - AWS Console → Bedrock → Guardrails → Create guardrail
   - Enable: PII filter (PERSON, LOCATION, DATE), Denied topic: "off-label drug promotion"
   - Enable contextual grounding check (grounding threshold ≥ 0.7)
   - Note the Guardrail ID (e.g., `abc12345`)

3. **IAM role / credentials** scoped to:
   ```
   bedrock:InvokeModel
   bedrock:InvokeModelWithResponseStream
   bedrock:ApplyGuardrail
   secretsmanager:GetSecretValue  (if using Secrets Manager for tokens)
   ```

4. **Real safety endpoint** — your Argus/Veeva/Oracle Empirica REST gateway URL
   and a bearer token with read+write scopes.

### Option B — Local demo (no AWS, no vendor system needed)

Python 3.9+ with the repo dependencies installed. No AWS account required.
`demo/reference_safety_service.py` stands in for the real safety system.

---

## Environment variables

```bash
# ── LLM (choose one) ──────────────────────────────────────────────────────────
# Option A: Amazon Bedrock (in-account; PHI never leaves VPC)
export LLM_PROVIDER=bedrock
export BEDROCK_REGION=us-east-1
export BEDROCK_NARRATIVE_MODEL_ID=anthropic.claude-sonnet-4-6-20260601-v1:0
export BEDROCK_GUARDRAIL_ID=abc12345          # REQUIRED for production
export BEDROCK_GUARDRAIL_VERSION=DRAFT

# Option B: Anthropic API (dev/demo only; PHI leaves your network)
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# ── Connector ─────────────────────────────────────────────────────────────────
export CONNECTOR_MODE=live

# Option A: real Argus / Veeva Safety gateway
export SAFETY_BASE_URL=https://your-argus-gateway.example.com
export SAFETY_API_TOKEN=eyJ...                # or store in Secrets Manager

# Option B: local reference service (auto-started by demo_live.py if unset)
# Leave SAFETY_BASE_URL unset — demo_live.py starts reference_safety_service.py

# ── AWS Secrets Manager (optional; local env vars take priority) ──────────────
export SECRETS_PREFIX=hcls/                   # default; secret at hcls/safety_api_token
export DISABLE_SECRETS_MANAGER=1              # set to 1 for local demo (no boto3 needed)

# ── Demo fallback (always works, no credentials) ──────────────────────────────
export EXTRACT_MODE=demo
export ENVIRONMENT=dev
```

---

## How to run

### Local demo (deterministic — always works)

```bash
cd 02-pharmacovigilance-agent
pip install -r requirements.txt          # langgraph, langchain-anthropic, etc.

PYTHONPATH=.:../platform_core:.. \
CONNECTOR_MODE=live \
EXTRACT_MODE=demo \
DISABLE_SECRETS_MANAGER=1 \
python demo/demo_live.py
```

Expected output includes:
- `[connector] Started local reference safety service on http://127.0.0.1:<port>`
- `Provider : DEMO (deterministic; no LLM API key required)`
- `Connector type : LiveSafetyConnector`
- Full ICSR narrative, MedDRA/WHODrug codes, seriousness + clock, grounding report
- HITL approval + gateway submit with Audit ID and Token JTI

### With Anthropic API

```bash
cd 02-pharmacovigilance-agent
PYTHONPATH=.:../platform_core:.. \
ANTHROPIC_API_KEY=sk-ant-... \
CONNECTOR_MODE=live \
DISABLE_SECRETS_MANAGER=1 \
python demo/demo_live.py
```

### With Amazon Bedrock (in-account)

```bash
cd 02-pharmacovigilance-agent

# Ensure AWS credentials are available (IAM role, instance profile, or AWS_PROFILE)
export AWS_PROFILE=your-bedrock-profile     # or use IAM task role in ECS/EKS

PYTHONPATH=.:../platform_core:.. \
LLM_PROVIDER=bedrock \
BEDROCK_REGION=us-east-1 \
BEDROCK_GUARDRAIL_ID=abc12345 \
CONNECTOR_MODE=live \
DISABLE_SECRETS_MANAGER=1 \
python demo/demo_live.py
```

### Against a real Argus/Veeva gateway

```bash
cd 02-pharmacovigilance-agent
PYTHONPATH=.:../platform_core:.. \
LLM_PROVIDER=bedrock \
BEDROCK_REGION=us-east-1 \
BEDROCK_GUARDRAIL_ID=abc12345 \
CONNECTOR_MODE=live \
SAFETY_BASE_URL=https://your-argus-gateway.example.com \
SAFETY_API_TOKEN=eyJ... \
python demo/demo_live.py
```

### Run only the live connector test (no LLM needed)

```bash
cd 02-pharmacovigilance-agent
PYTHONPATH=.:../platform_core:.. \
EXTRACT_MODE=demo \
DISABLE_SECRETS_MANAGER=1 \
python -m pytest tests/test_live_connector.py -v
```

---

## Starting the reference service standalone

```bash
cd 02-pharmacovigilance-agent
python demo/reference_safety_service.py 8099
# Listening on http://127.0.0.1:8099/

# Smoke-test it:
curl http://127.0.0.1:8099/health
curl http://127.0.0.1:8099/cases/ICSR-2026-0002
curl -X POST http://127.0.0.1:8099/cases/search-duplicates \
     -H 'Content-Type: application/json' \
     -d '{"suspect_drug":"Lisinopril","meddra_pt":"renal failure"}'
curl -X POST http://127.0.0.1:8099/cases/drafts \
     -H 'Content-Type: application/json' \
     -d '{"case_id":"ICSR-TEST","meddra_pt":"Nausea"}'
curl -X POST http://127.0.0.1:8099/reports \
     -H 'Content-Type: application/json' \
     -d '{"case_id":"ICSR-TEST","is_serious":false}'
```

Customer swap: replace `http://127.0.0.1:8099` with your Argus/Veeva endpoint.
The LiveSafetyConnector speaks the same REST contract — no code changes needed.

---

## Pointing at a real Argus or Veeva Safety instance

The `LiveSafetyConnector` calls four endpoints. Your integration adapter must
expose them (or wrap the vendor API to expose them):

| Method | Path | Vendor mapping |
|---|---|---|
| GET | `/cases/{id}` | Argus: `GET /ArgusSafety/case/{id}`; Veeva Vault: `GET /vaults/{id}/objects/cases/{id}` |
| POST | `/cases/search-duplicates` | Argus: `POST /ArgusSafety/cases/search`; Veeva: custom search endpoint |
| POST | `/cases/drafts` | Argus: `POST /ArgusSafety/cases` (status=DRAFT); Veeva: `POST /vaults/{id}/objects/cases` |
| POST | `/reports` | Argus E2B gateway: `POST /ArgusSafety/icsrSubmission`; Veeva ESG: submission endpoint |

For E2B(R3) XML serialization, add it inside the connector's `submit_report`
method before the HTTP call — the agent does not produce XML directly.

---

## Security talking points

### 1. In-account inference (Bedrock)
Narrative drafting runs inside the customer's AWS VPC via a Bedrock VPC
interface endpoint. Source records (which contain patient PII) never leave the
account boundary. This is the key data-residency argument for regulated data.

### 2. Guardrails (PHI filter + off-label blocking)
`BEDROCK_GUARDRAIL_ID` wraps every Bedrock call. The guardrail is configured to:
- Block PII/PHI egress in model output (re-identification risk)
- Deny off-label drug promotion topics
- Apply contextual grounding checks (halucination resistance for regulatory text)

### 3. Scoped bearer tokens (no standing service accounts)
The MCP gateway mints a short-lived token (`tokens.mint_scoped_token`) scoped
to exactly one tool per invocation. The token carries the user's identity and
expires after the call. There are no standing service accounts with broad access
to the safety database.

### 4. HITL gate (GVP Module VI / ICH E2E)
`safety.submit_report` is marked `high_risk=True` in `policy.py`. The gateway
blocks execution and returns `PENDING_APPROVAL` unless a verified human reviewer
identity is bound into the approval record. This is the mandatory human oversight
control for ICSR submission.

### 5. Immutable audit trail (21 CFR Part 11)
Every gateway call (ALLOW / DENY / PENDING / ERROR) is recorded with:
- User identity (sub), roles, agent_id
- Scoped token JTI (proves the token was minted and verified)
- Connector kind + method (lineage to the system of record)
- Approved_by (for high-risk writes)
In production, route the audit log to CloudWatch Logs with Object Lock or QLDB
for tamper-evident retention.

---

## Limitations of the local reference service

| Limitation | Production resolution |
|---|---|
| In-memory only — data lost on restart | Argus/Veeva Safety database |
| No real E2B(R3) XML serialization | Implement in `LiveSafetyConnector.submit_report` |
| No real MedDRA/WHODrug coding | Implement `LiveMedDRA` / `LiveWHODrug` with licensed API |
| Bearer token not validated | Real IdP JWT validation in gateway + Cognito/Entra |
| Single process, no HA | AWS ECS/EKS + RDS + ALB |

---

## MedDRA / WHODrug note

MedDRA (MSSO) and WHODrug (Uppsala Monitoring Centre) require a commercial
license. In this demo both remain fixture-backed even in `CONNECTOR_MODE=live`.
To go live:

1. Implement `LiveMedDRA(CodingConnector)` in `connectors/live.py` calling the
   MSSO Browser REST API.
2. Implement `LiveWHODrug(CodingConnector)` calling the UMC WHODrug Global API.
3. Update `factory.get_connector` to return these for `meddra`/`whodrug` in live
   mode (see the comment block in `factory.py`).
