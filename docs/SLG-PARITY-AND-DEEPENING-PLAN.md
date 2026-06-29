# HCLS Parity-and-Deepening Plan (benchmarked against SLG-AI-Agents)

**Goal:** make the HCLS suite *at least* as deep and broad as `slg-ai-agents` — deployable by an AWS SA, CloudFormation-verified, fully tested, and able to answer every CISO/CIO question with a document that names each security issue. This plan is the gap analysis + the phased work to get there.

## Progress (live)
- ✅ **Phase 1 — CISO/CIO security doc kit** (SECURITY.md + THREAT-MODEL + NIST 800-53 matrix + OWASP-LLM/ATLAS + IR & key-mgmt + production-readiness + README question index).
- ✅ **Phase 2 — defense-in-depth in code** (consequential commits withheld from agents + enforcing test; bound approval tokens with SoD/single-use/args-binding).
- ✅ **Phase 4 — one-command test harness** (`make test` → 503 tests across 20 suites; CI updated).
- ✅ **Phase 3 — deploy ergonomics:** `edge.yaml` + **9 per-agent SAM golden paths** (cfn-lint clean) + `infra/GOLDEN-PATHS.md`.
- ✅ **Phase 5+6 — hygiene + combined leave-behind:** VERSION/SOURCES.md/CHANGELOG.md + a 77-page combined PDF leave-behind (`decks/leave-behinds/`).

## Verdict up front
HCLS is **already ahead of SLG** on: **9 built agents** (vs. 8) including a **live Bedrock + connector path** (Agent 02), **cited AWS-style per-agent decks + CIO board deck + ROI calculator**, a beginner deploy cheat sheet, and **503 tests** (vs. ~224 SLG test functions). The gap is **not** agents or GTM — it's **security/CISO documentation, deploy ergonomics, defense-in-depth in code, and a one-command test harness**, where SLG is meaningfully deeper. Close those five areas and HCLS exceeds SLG on every axis.

---

## Gap analysis (SLG has it · HCLS today · priority)

| Area | SLG has | HCLS today | Priority |
|---|---|---|---|
| **Threat model** | `docs/THREAT-MODEL.md` | ❌ none | **P1** |
| **NIST 800-53 control matrix** | `docs/NIST-800-53-CONTROL-MATRIX.md` | ❌ none | **P1** |
| **OWASP-LLM Top-10 + MITRE ATLAS mapping** | `docs/OWASP-LLM-ATLAS-MAPPING.md` | ❌ none | **P1** |
| **Incident response + key management** | `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md` | partial (runbooks/INCIDENT-RESPONSE.md, no key-mgmt) | **P1** |
| **Production-readiness + shared responsibility** | `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` | partial (`SHARED-RESPONSIBILITY-MATRIX.md`) | **P1** |
| **Top-level SECURITY.md** | `SECURITY.md` (vuln reporting, scope, security-model summary) | ❌ none | **P1** |
| **Consequential action withheld *in code* + test** | irreversible commit absent from agent grant; `test_consequential_actions_withheld_from_agents` | ❌ HCLS *grants* `submit_report`/`close_capa`/`record_disposition` to the agent (approval-gated) | **P1** (strong CISO story) |
| **Edge layer in IaC** | `infra/cloudformation/edge.yaml` (CloudFront/WAF/ACM) | ❌ flagged as a known gap in the CIO deck | **P2** |
| **Per-agent golden-path deploy** | `infra/golden-path-<agent>/` = SAM `template.yaml` + `deploy.sh` + `destroy.sh` + `smoke_test.sh` + `mint_approval.py` + `DEPLOY-GOLDEN-PATH.md` (+ a `-secure` variant) | ❌ only the shared `scripts/deploy.sh` quickstart | **P2** (the "SA can deploy it" ask) |
| **One-command test harness** | root `conftest.py` (module-isolation hook) + `pytest.ini` → `pytest` runs **all** agents at once | ❌ must run per-agent (dup `agent`/`tools`/`core` package names) | **P2** (the "verified with all the tests" ask) |
| **Integration test tier** | `tests/integration/` with a `@pytest.mark.integration` marker against a deployed stack | ❌ none | **P3** |
| **Hardened platform security modules** | dedicated `jwt_verify.py` (+test), `mcp_gateway/approvals.py` (single-use/SoD/tamper-evident), `audit_sinks.py` (conditional write), `reviewer/service.py`+`store.py` | partial (`auth.py` has RS256/JWKS; approval logic inline in gateway; no reviewer service module) | **P2** |
| **Governance controls-in-code** | `governance/controls/control_mappings.py`, `governance/evals/run_evals.py` | partial (grounding/evals/redteam/fairness, no controls map / eval runner) | **P3** |
| **Repo hygiene** | `CHANGELOG.md`, `VERSION`, root `SOURCES.md`, `RELEASE.md`, self-review docs | ❌ (uses SUITE-STATUS changelog) | **P3** |
| **Combined all-in-one deck + leave-behinds folder** | `SLG-Agentic-AI-Suite-COMBINED.pptx`, `decks/leave-behinds/` | per-agent + overview + CIO (no single combined) | **P3** |

> **Not applicable to HCLS:** SLG's WCAG/ADA accessibility gate and Whole-of-Government life-event orchestrator are government-specific. HCLS's governance equivalents are grounding + GxP audit + diversity/fairness posture, which are already present.

---

## The plan (phased, with acceptance criteria)

### Phase 1 — The CISO/CIO "answer kit" *(the headline — directly answers your ask)*
Create the security documents an architecture/security review demands, **each naming the specific issue and the specific control**:
1. `SECURITY.md` — scope, what's in/out of scope, the 7-point security model, how to report a vuln, supported versions.
2. `docs/THREAT-MODEL.md` — STRIDE-style threats for an agentic, PHI-touching, regulated workflow (prompt injection, data exfiltration, authorization bypass, audit tampering, model/prompt drift, supply chain) → each with the mitigating control + where it lives in code/IaC.
3. `docs/NIST-800-53-CONTROL-MATRIX.md` — control family → how the suite satisfies it (AC, AU, IA, SC, SI, CM, IR…) mapped to concrete files/stacks; gaps flagged as customer-owned.
4. `docs/OWASP-LLM-ATLAS-MAPPING.md` — OWASP LLM Top-10 (LLM01 prompt injection … LLM10) + relevant MITRE ATLAS techniques → mitigation in this suite, with the red-team test that proves it.
5. `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md` — IR runbook (detect/contain/evidence/notify) + KMS CMK lifecycle, rotation, token-signing keys, secret rotation.
6. `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` — what's reference vs. production, the CSV/CSA gate, and AWS-vs-SI-vs-sponsor responsibility per control.
7. **README "CISO/CIO question index"** — a table: *"If they ask X, point at doc Y."* covering data residency, PHI egress, audit integrity, model risk, authorization, IR, validation.

**Acceptance:** a CISO can walk the threat model + NIST matrix + OWASP mapping and find every concern answered with a named control and a file path.

### Phase 2 — Defense-in-depth *in code* (the strongest CISO proof)
1. **Withhold the irreversible commit from the agent.** Remove `safety.submit_report`, `qms.close_capa`, `mes.record_disposition` (and peers) from `AGENT_TOOL_GRANTS`; they remain in the human reviewer's entitlement only. The agent can *draft/propose*; only a bound human identity can *commit*.
2. **Enforcing test** `test_consequential_actions_withheld_from_agents` — fails CI if any agent is ever granted an irreversible commit. (Mirror SLG.)
3. Add `platform_core/.../reviewer/` service + store (the HITL reviewer backend the decks reference) and `mcp_gateway/approvals.py` (single-use, separation-of-duties, tamper-evident) + tests.
4. `test_jwt_verify.py` and `test_audit_append_only.py` to prove the crypto + WORM semantics.

**Acceptance:** the suite *cannot* finalize a regulated action from agent code alone, and a test enforces it.

### Phase 3 — Deploy ergonomics so an SA can actually ship it
1. `infra/cloudformation/edge.yaml` — CloudFront + WAF + ACM (closes the honestly-flagged "edge not in IaC" gap), wired into `quickstart.yaml`.
2. **Per-agent golden path** `infra/golden-path-<agent>/`: a self-contained SAM `template.yaml` + `deploy.sh` + `destroy.sh` + `smoke_test.sh` + `mint_approval.py` + `DEPLOY-GOLDEN-PATH.md`, so an SA runs `cd infra/golden-path-02-pharmacovigilance && ./deploy.sh` and gets a working, human-gated agent + a smoke test that proves the gate. Start with 02 (live path) and 09; template the rest.
3. `infra/GOLDEN-PATHS.md` index.

**Acceptance:** an SA clones the repo and stands up one agent end-to-end from a single folder, with a smoke test that exercises the human gate.

### Phase 4 — One-command test harness ("verified with all the tests")
1. Root `conftest.py` with the module-isolation hook (purge cached `agent`/`tools`/`core` between agent test dirs) + `pytest.ini` (`--import-mode=importlib`) so **`pytest` from the repo root runs all ~520 tests** in one shot.
2. Add the `integration` marker + `tests/integration/` (skipped offline).
3. Update `.github/workflows/ci.yml` to run the single command and publish one green number.

**Acceptance:** `pytest` at the root prints one passing total (no per-agent juggling).

### Phase 5 — Decks: confirm AWS-style + cited; add combined + leave-behinds
Decks are already AWS-palette and source-cited. Add a single `HCLS-Agentic-AI-Suite-COMBINED.pptx` (all agents in one file) and a `decks/leave-behinds/` folder of PDFs; re-verify the AWS look and that every figure still traces to `gtm/HCLS-DECK-SOURCES.md`.

### Phase 6 — Thorough README + repo hygiene
`CHANGELOG.md`, `VERSION`, a top-level `SOURCES.md` pointer, `RELEASE.md`, and a README expansion: a **Security & Compliance** section linking the Phase-1 docs, the CISO/CIO question index, and a one-line "parity with SLG" statement.

---

## Suggested sequencing & effort
- **Phase 1 (security docs)** — highest value for your stated goal; ~1 focused pass. *Do first.*
- **Phase 2 (code defense-in-depth)** — ~1 pass; small code change + tests; big CISO payoff.
- **Phase 3 (golden-path deploy)** — ~1–2 passes (edge.yaml + 2 golden paths, then template the rest).
- **Phase 4 (test harness)** — ~half a pass; mechanical.
- **Phases 5–6 (decks combined + hygiene)** — ~half a pass.

**Definition of done:** an AWS SA can (a) deploy one agent from a single folder with a smoke test, (b) run all tests with one command, and (c) hand a CISO/CIO a document that names every security issue and its control — and HCLS is then deeper than SLG on every axis.
