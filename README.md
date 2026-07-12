# HCLS AI Agent Suite

> ### 🛡️ Part of the Aegis Governed-Agent Portfolio — one solution, five repositories
> This repository is **1 of 5 that form a single, review-as-one solution**: the **Aegis** governance
> platform (the control plane) plus four vertical agent packs. All five conform to one versioned
> governance contract — **AGP v1.0** — and one deploy pattern, so a CIO / CISO reviews and approves them
> **together** for pilot.
>
> | # | Repository | Role |
> |--:|---|---|
> | 1 | **`aegis-ai-governance-platform-aws`** | Governance **platform & pattern** (deny-by-default control plane) |
> | 2 | **`hcls-ai-agents`** | **Life sciences** — pharma / biotech / CRO |
> | 3 | **`slg-ai-agents`** | **State & local government** |
> | 4 | **`healthcare_ai_agents`** (**HPP**) | **Healthcare payer / provider** |
> | 5 | **`edu-ai-agents`** | **Education** — K-12 & higher-ed |
>
> **▶ You are here: `hcls-ai-agents`.**
>
> **New to the portfolio?** Start in the **`aegis-ai-governance-platform-aws`** repo:
> `PORTFOLIO-EXECUTIVE-SUMMARY.md` (10-minute front door) → `SA-DEPLOYMENT-RUNBOOK.md` (deploy the
> platform + heroes in a new AWS account) → `PORTFOLIO-MATURITY-SCORECARD.md` (what's proven) →
> `DO-NOT-CLAIM.md` (the honesty boundary).
>
> **Naming:** **`healthcare_ai_agents` = HPP** (payer / provider: claims, prior-auth, denials) and
> **`hcls-ai-agents` = life sciences** (pharmacovigilance, clinical, regulatory) are **distinct
> products**; the underscore-vs-hyphen naming is historical.
>
> ---


> ⚠️ **Before you cite anything here:** read [**What we will *not* claim**](NOT-CLAIMS.md) — this is an independent reference accelerator that runs on AWS. It is **not** an AWS service, **not** AWS-supported, **not** an official AWS solution, and **not** a compliance certification. That page governs if any wording elsewhere reads stronger.

> 📊 **Honest status, one source of truth:** per-agent maturity, clean-account evidence, connector tiers, and the test count live in machine-readable [`MATURITY.yaml`](MATURITY.yaml); the four connector-maturity terms are defined in [`docs/CONNECTOR-MATURITY.md`](docs/CONNECTOR-MATURITY.md). Prose defers to `MATURITY.yaml`; a portfolio drift-checker (`tools/check_maturity.py`) keeps them aligned.

> 🔗 **Conforms to the Aegis Governance Pattern (AGP) v1.0.** The 8 required controls (identity, deny-by-default gateway, least-privilege intersection, bound SoD approval, fail-closed masking, append-only+WORM audit, token budgets, model gateway+grounding) are mapped to their implementing module and proving test in [`AGP-CONFORMANCE.md`](AGP-CONFORMANCE.md).

> ™ **Brand & trademark:** collateral follows two tracks — an **internal-AWS** track (approved templates only) and a **customer-safe public** track (neutral branding, plain-text "Built on AWS", no AWS logo). Rules in [`BRAND-AND-TRADEMARK.md`](BRAND-AND-TRADEMARK.md). Nothing here implies AWS sponsorship or endorsement.

> 🧭 **Part of the governed-agent portfolio.** This pack conforms to the **Aegis Governance Pattern (AGP v1.0)**; **Aegis** (`aegis-ai-governance-platform-aws`) is the hub — see its `PORTFOLIO-START-HERE.md` (how the packs flow together) and `DEPLOY-EVERYTHING.md` (deploy everything end-to-end). Hero reviewer pack: [`02-pharmacovigilance-agent/ASSURANCE-PACKET.md`](02-pharmacovigilance-agent/ASSURANCE-PACKET.md) · [`PILOT-SOW`](02-pharmacovigilance-agent/PILOT-SOW.md).

> 📚 **Governance & readiness docs (this repo):** [`NOT-CLAIMS`](NOT-CLAIMS.md) · [`MATURITY.yaml`](MATURITY.yaml) · [`Connector maturity`](docs/CONNECTOR-MATURITY.md) · [`AGP conformance`](AGP-CONFORMANCE.md) · [`Operating model`](OPERATING-MODEL.md) · [`Release packet`](RELEASE-PACKET.md) · [`AWS run-cost`](AWS-RUN-COST.md) · [`Brand & trademark`](BRAND-AND-TRADEMARK.md)
### Governed AI Agents for Life Sciences — Built on AWS

[![CI](https://github.com/virtualryder/hcls-ai-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/virtualryder/hcls-ai-agents/actions/workflows/ci.yml)

> **The agents are not the product. The governed platform that makes them deployable, auditable, and compliant is.**

A large systems integrator deploying AI in a pharmaceutical, biotech, medtech, or CRO environment cannot hand a customer a collection of LLM calls and call it done. Every regulated artifact an agent touches — an ICSR report, a submission section, a CAPA record — carries data-integrity, e-signature, and accountability obligations that exist before the first line of agent code is written. This suite embeds those controls from the first commit: deny-by-default authorization, PHI masking, grounding verification, prompt version pinning, a human gate that is framework-enforced (not merely documented), and a tamper-evident audit trail **designed to support 21 CFR Part 11 controls** (subject to customer computer-system validation, identity integration, and quality-system approval).

The result is a deployable accelerator — not a certified product — that gives an SI engagement team a credible, compliant starting point across nine high-value life-sciences workflows.

**Repository status (current):** all 9 agents built to flagship depth · 9 AWS-native rebuilds (Strands + Step Functions) · a live Amazon Bedrock + real-connector reference path (Agent 02) · **580 automated tests passing** with no API key · one-command CloudFormation quick-deploy (connector Lambdas + a portable MCP gateway (AgentCore mode is experimental — see `infra/cloudformation/agentcore-gateway.yaml`) + native/container agent) deployable in a new customer account in **supported AWS Regions** (where the required Bedrock, model, PrivateLink, and — for AgentCore mode — AgentCore services are available) · **all 9 golden paths deployed and run end-to-end in a clean AWS account (us-east-1) — full Assemble→…→human gate→bound approval→Finalize to SUCCEEDED — then torn down** · Terraform reference skeleton (not at parity — see [`docs/TERRAFORM-AND-GOVCLOUD-STATUS.md`](docs/TERRAFORM-AND-GOVCLOUD-STATUS.md)) · executive deck, 5-slide customer teaser, and one-page leave-behind included · **external-review hardening (P0):** deployed-path human-approval enforcement (bound, single-use, separation-of-duties, args-bound tokens; `STRICT_APPROVAL` fails closed), authenticated-authorizer-only identity, immutable fail-closed audit, customer IdP (SAML/OIDC) federation, VPC PrivateLink isolation, and fail-closed CI.

> **On the test count:** **580** is the `scripts/run_all_tests.sh` green total across 20 suites run in isolated processes (equal to `MATURITY.yaml` `offline_total`, which is canonical). A plain root `pytest` collects **576** because the openFDA live-connector test skips without `RUN_LIVE_OPENFDA=1` and the suites share package names — expected, not a discrepancy.

---

## Positioning

| What this is | What this is not |
|---|---|
| A governed, auditable accelerator — bring your own LLM call without the compliance scaffolding and you still have a prototype | A certified, validated, production-ready SaaS product you can hand to a customer unchanged |
| Nine agents with shared platform controls that compound across the portfolio | Point tools built independently with no governance consistency |
| A reference for Amazon Bedrock AgentCore Gateway + Identity + Runtime semantics — testable locally, deployable on AWS | A vendor lock-in — the gateway semantics are replicated in `platform_core/` so the logic is readable and testable without an AWS account |
| Decision-support — drafts, assembles, monitors, flags — with humans owning every consequential decision | Autonomous execution in regulated workflows |

---

## Maturity Ladder

Every agent and platform component is positioned honestly against four levels:

| Level | Description | What it means |
|---|---|---|
| **Documented** | Architecture, workflow, and compliance design are written and reviewed | Useful for customer discovery and architecture review; not runnable |
| **Demonstrated** | Code runs end-to-end in `EXTRACT_MODE=demo` (no API key, deterministic fixtures) | Proof of concept; suitable for internal demos and early customer workshops |
| **Deployable** | CloudFormation templates, container contracts (ARM64, `/invocations`, `/ping`), and CI pass; requires customer AWS account and Bedrock access | Suitable for a customer pilot with SI-managed infrastructure |
| **Production-ready** | Customer computer-system validation (CSV) complete, IdP integrated, connectors tested against live systems, penetration test passed | Engagement milestone, not a day-one deliverable |

**All nine agents are built to flagship depth** — a full LangGraph workflow, governed tool access, deterministic fixtures, flagship-level test suites, a Streamlit dashboard, a four-document doc set, and a matching **AWS-native rebuild** (Strands + Step Functions with a `waitForTaskToken` human gate). Agent 02 (Pharmacovigilance) additionally ships a **live path**: real Amazon Bedrock inference and a real HTTP system-of-record connector, exercised end-to-end (see `02-pharmacovigilance-agent/demo/`). The suite sits at **Demonstrated + Deploy-validated**: 580 automated tests pass with no API key; **all nine golden paths were deployed into a clean AWS account, ran the full governed workflow (human gate + bound separation-of-duties approval + immutable audit) to `SUCCEEDED`, and were torn down** (see `docs/GOLDEN-PATH-DEPLOY-NOTES.md`); production-readiness (CSV/CSA, live system integration, penetration test) remains the engagement. (A tenth agent, 10 Scientific Intelligence & Target Discovery, is at roadmap/Documented maturity — cited deck + design spec.)

## Capability maturity matrix

✅ = evidence in this repo (code + tests, or the documented live AWS validation) · ◻ = not done here / engagement work.
Live-AWS cells reflect the 2026-06-29/30 clean-account run: all 9 golden paths (stacks `hcls-01…09-dev`) deployed, ran the full governed workflow (human gate → bound SoD approval → Finalize) to `SUCCEEDED`, and were torn down — see [`docs/GOLDEN-PATH-DEPLOY-NOTES.md`](docs/GOLDEN-PATH-DEPLOY-NOTES.md) and [`SUITE-STATUS.md`](SUITE-STATUS.md).

| Capability | Designed | Implemented (offline/tested) | Deployed on AWS (validated) | Integration-tested on AWS | Production-ready | Owner (Repo/Customer) |
|---|:--:|:--:|:--:|:--:|:--:|---|
| Identity / authN | ✅ | ✅ | ✅ | ◻ | ◻ | Repo (authenticated-authorizer-only identity deployed; federated IdP login not proven — Customer) |
| MCP / tool authorization gateway | ✅ | ✅ | ✅ | ✅ | ◻ | Repo (portable gateway is the supported default; AgentCore mode experimental) |
| Policy enforcement (deny-by-default) | ✅ | ✅ | ✅ | ✅ | ◻ | Repo |
| Human approval (SoD, single-use) | ✅ | ✅ | ✅ | ✅ | ◻ | Repo (bound, single-use, SoD approval exercised live to `SUCCEEDED`) |
| PII/PHI masking | ✅ | ✅ | ◻ | ◻ | ◻ | Repo (unit-tested; not runtime-verified on AWS) |
| Audit (append-only + WORM) | ✅ | ✅ | ✅ | ✅ | ◻ | Repo (immutable `INTENT → COMMITTED` audit written live; WORM retention configuration: Customer) |
| Bedrock + Guardrails | ✅ | ✅ | ◻ | ◻ | ◻ | Repo (Agent 02 real-Bedrock live path exercised locally; model invocation not asserted in the clean-account smoke) |
| IaC deploy (golden path) | ✅ | ✅ | ✅ | ✅ | ◻ | Repo (all 9 golden paths) |
| Live connectors | ✅ | ✅ | ◻ | ◻ | ◻ | Customer (fixtures + Agent 02 local live-HTTP reference; Veeva/Argus/QMS integration is engagement work) |
| CI/CD | ✅ | ✅ | ◻ | ◻ | ◻ | Repo (fail-closed CI: tests · compile · deck build · cfn-lint; no cloud deploys in CI) / Customer |
| Monitoring / alerts | ✅ | ◻ | ◻ | ◻ | ◻ | Customer (runbooks provided) |
| DR / backup | ✅ | ◻ | ◻ | ◻ | ◻ | Customer (`runbooks/DR-RUNBOOK.md` provided) |
| Compliance evidence | ✅ | ✅ | ◻ | ◻ | ◻ | Repo (Part 11-supporting design, TPRM packet) / Customer (CSV/CSA, HITRUST/SOC 2 evidence) |

Nothing in this repository is production-certified; see [`docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md) for the full RACI.

*Governance once, agents as add-ons: `platform_core` (`hcls-agent-platform` 0.1.0) **implements the Aegis Governance Pattern (AGP) v1.0** — the shared governance contract defined in the Aegis platform repo (`docs/14-GOVERNANCE-PATTERN-VERSIONING.md`). Conformance is declared in `platform_core/hcls_agent_platform/__init__.py` (`AEGIS_GOVERNANCE_PATTERN_VERSION`) and asserted by `platform_core/tests/test_agp_conformance.py`.*

> **Validation update (2026-07-07/08).** All nine golden-path deployments were independently re-verified against the validation account (CloudTrail, deleted-stack history). One teardown gap was found and fixed: the runs' Cognito user pools had survived stack deletion; all ten were removed on 2026-07-08 and the `destroy.sh` fix is documented in [`docs/GOLDEN-PATH-DEPLOY-NOTES.md`](docs/GOLDEN-PATH-DEPLOY-NOTES.md). Sanitized proof pack: [`evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](evidence/CLEAN-ACCOUNT-ACCEPTANCE.md).

---

## The Nine Agents

| # | Agent | Problem it solves | Primary systems | Key regulations |
|---|---|---|---|---|
| **01** | Regulatory Writing & Intelligence | Medical writers spend the majority of their time retrieving evidence and reconciling figures rather than reasoning; a hallucinated number in a submission is a data-integrity defect | Veeva Vault RIM, Veeva Vault DMS, FDA/EMA/PMDA guidance portals | 21 CFR Part 11, ICH M4 (CTD), GxP ALCOA+, FDA/EMA good-AI principles (Jan 2026) |
| **02** | Pharmacovigilance — ICSR Case Intake | Adverse-event volumes scale with portfolio breadth; triage, duplicate detection, MedDRA coding, and E2B narrative drafting are high-volume and time-critical | Argus Safety, Veeva Safety, MedDRA, WHO Drug | GVP/ICH E2B(R3), 21 CFR Part 314/600, EudraVigilance, HIPAA |
| **03** | Clinical Trial Ops & TMF | Trial Master File gaps surface late — after database lock; query backlogs on EDC slow enrollment; completeness is continuous, not periodic | Veeva Vault eTMF, Medidata Rave/Veeva CTMS, Medidata EDC | ICH E6(R3) GCP, 21 CFR Part 11, FDA/EMA TMF inspection readiness |
| **04** | Site Selection & Patient Matching | Feasibility studies rely on site-opinion surveys; historical performance data and real-world cohort sizing are rarely integrated at scale | CTMS, RWD/claims/registry databases | FDA Diversity Action Plan, ICH E17, HIPAA/de-identification (Safe Harbor/Expert Determination) |
| **05** | Quality / CAPA & Complaints | Product complaint volumes are large; CAPA root-cause consistency and on-time closure rates are recurring inspection findings | QMS (TrackWise, Veeva Quality), complaint databases | 21 CFR Part 211/820, FDA QMSR (effective Feb 2026), ISO 13485, EU MDR/IVDR |
| **06** | Clinical Protocol Design & Feasibility | First-draft protocols incorporate historical guidance and study data late; feasibility assumptions are not linked to RWD | RIM (guidance retrieval), RWD, CTMS historical data | ICH E8(R1) general principles, GCP, FDA/EMA protocol guidance |
| **07** | Real-World Evidence / HEOR | RWE/HEOR analyses require cohort definition, confounding control, and structured code translation; analyst time is disproportionately spent on data wrangling | Claims databases, registry data, RWD platforms | FDA RWE framework, HEOR methodological standards, HIPAA de-identification |
| **08** | Medical Affairs / MSL Copilot | Field medical teams need rapid, on-label, evidence-grounded responses for HCP interactions; off-label guardrails must be technical, not procedural | CRM (Veeva CRM), DMS/MSL portals, MLR workflow | FDA off-label promotion rules, OIG guidance, ABPI/EFPIA codes, MLR SOP |
| **09** | Manufacturing Batch-Review | Batch-record review and OOS/deviation investigation are slow, manual, and senior-labor-heavy; review by exception with a QA release gate | MES / electronic batch records, LIMS | cGMP 21 CFR 211, 21 CFR 211.192, 21 CFR Part 11, EU GMP Annex 11 |

### Cited highlights

One headline figure and the cost of doing nothing per agent — every stat is source-class-tagged and traces to **[`gtm/HCLS-DECK-SOURCES.md`](gtm/HCLS-DECK-SOURCES.md)** (with URLs). `[gov]` = gov/peer-reviewed · `[ind]` = industry-research · `[est]` = sector-press/estimate · `[mod]` = modeled · `[ven]` = vendor.

- **01 Regulatory Writing** — $2.6B per approved drug `[gov]` (DiMasi/Tufts); cost of inaction **~$60M lost per month of submission delay** `[ind]` (McKinsey). Outcome proxy: CSR first draft 180→80 hrs `[ven]` (Merck).
- **02 Pharmacovigilance** — ~28M cumulative FAERS reports `[gov]` (FDA); **~$2.0M/yr** modeled case-intake cost `[mod]`. Outcome: 40–70% data-entry-time cut `[gov]` (Schmider 2019).
- **03 Clinical Trial Ops & TMF** — **~$800K/day** lost sales + ~$40K/day direct per day of delay `[gov]` (Tufts 2024); **~$25.7M** per 30-day database-lock slip `[mod]`.
- **04 Site Selection & Patient Matching** — ~80% of trials miss their enrollment timeline `[est]`; **~$24M/launch** modeled from a 30-day pull-in `[mod]`. *(No independent AI ROI benchmark — labeled modeled.)*
- **05 Quality / CAPA** — CAPA (21 CFR 820.100) is the **#1-cited FDA device 483 clause** `[gov]`; **$10M–$100M per recall** `[ind]`.
- **06 Clinical Protocol Design** — ~57% of protocols amended, ~45% avoidable `[ind]` (Tufts); **~$535K per avoidable Phase III amendment** `[ind]`.
- **07 Real-World Evidence / HEOR** — ~45% of analyst time on data prep `[est]` (Anaconda); **~$1.3M/yr per 20-person team** of non-analytic labor `[mod]`.
- **08 Medical Affairs / MSL** — MLR review stretches weeks→months `[est]`; **billions in off-label FCA exposure** `[gov]` (GSK $3B, Pfizer $2.3B). Outcome: 50–70% MLR time reducible `[ind]` (McKinsey).
- **09 Manufacturing Batch-Review** — **62% of US drug shortages trace to manufacturing/quality** `[gov]` (FDA); **~$420K/yr** modeled investigation labor `[mod]`. Outcome: >50% deviation reduction at a benchmarked site `[ind]` (McKinsey).
- **10 Scientific Intelligence & Target Discovery** *(roadmap)* — **~86% of programs entering the clinic fail** `[gov]` (Wong/Siah/Lo 2019); **~$2.6B per drug** / ~$430M preclinical `[ind]`.

Monthly run-cost model (pilot vs production): [`offerings/TCO-MODEL.md`](offerings/TCO-MODEL.md)


---

## Shared Platform

![HCLS GxP data flow — connectors to named-human e-signature to WORM audit](docs/diagrams/hcls-gxp-data-flow.png)

The shared Aegis control-plane pattern — how every tool call is authenticated, authorized, human-approved, and audited, including the deny paths:

![Aegis MCP gateway authorization flow — shared control plane](docs/diagrams/mcp-gateway-auth-flow.png)

Editable source: the SVG in [`docs/diagrams/`](docs/diagrams/) (open in draw.io, Inkscape, or any text editor).

Every agent shares the same platform stack. Controls compound: a governance improvement to the PHI masker, the grounding checker, or the audit trail benefits all nine agents simultaneously.

### LLM Factory
A single abstraction layer routes inference to **Anthropic Claude** (API) or **Amazon Bedrock** (in-account) depending on deployment mode. With Bedrock and the customer-VPC deployment, model traffic stays on AWS via a **`bedrock-runtime` VPC interface endpoint** (PrivateLink) rather than the public internet — see [Network isolation](#network-isolation-no-public-egress-by-default). `EXTRACT_MODE=demo` bypasses the LLM entirely for local testing.

### PHI Masking
A deterministic Safe-Harbor pass (`phi.py`) masks the structured HIPAA identifier families — SSNs, MRN/subject/case IDs, dates more specific than a year, emails, phone/fax, payment cards, DEA/NPI — before any content enters a prompt or an audit record. The masking layer is stateless and runs before every gateway invocation. Free-text **patient names** (Safe Harbor #1) are **not** caught by the regex pass; masking them requires the ML NER pass (`MASK_ENGINE=ml` / Amazon Comprehend Medical). When `ALLOW_REAL_DATA` is set, that NER pass is **mandatory and fails closed** (the masker raises rather than emit regex-only output that could leave a name in the clear).

### MCP Authorization Gateway

### Secure MCP gateway — how every tool call is authorized

Every agent tool call passes through an **authenticated gateway**; there is no un-gated path to a system of record. The same controls apply everywhere in the portfolio (the [Aegis Governance Pattern](the Aegis platform repo `docs/14-GOVERNANCE-PATTERN-VERSIONING.md`)):

- **Inbound authorization — JWT or IAM.** A verified Cognito/IdP **JWT** (or SigV4/**IAM**) is required on every call; identity is taken only from the verified authorizer claim, never the request body. *"No authorization" is a development/testing mode only and is never used in production.*
- **Deny-by-default policy.** A tool is callable only if it is **registered in the allow-list** and the caller's effective permission = **grant ∩ entitlement** (the agent can never exceed the human it acts for). Unregistered tool or out-of-scope data class → **deny**.
- **Human approval for consequential actions.** Consequential tools are **withheld in code** and require a **bound, single-use, separation-of-duties** approval (approver ≠ requester; replay rejected).
- **Scoped outbound authorization.** The gateway issues **short-lived, least-privilege** downstream credentials (IAM / OAuth / token-exchange / on-behalf-of), so "the agent acts only within the human's authority" holds end to end.
- **Fail-closed masking.** PHI is masked before any model or audit write; on masker failure it **redacts rather than leaks**.
- **Append-only audit + revocation.** Every decision (allow / deny / approval) is written to an **append-only** sink (IAM denies `UpdateItem`/`DeleteItem`) with **WORM** evidence; tools can be revoked / deny-listed at the registry.
- **Failure modes are fail-closed.** Missing/invalid token → **401**; unregistered tool → **deny**; missing approval → **deny**; masker or audit-write failure → **deny, not proceed**.

In deployment this is **Amazon Bedrock AgentCore Gateway** (managed) or the **portable API-Gateway-+-Cognito-JWT** path; the portable path is the supported default and the one live-validated (the Aegis platform repo, Run 10; this suite deploys the same portable pattern).
The governed front door between every agent and every system of record. **No agent calls a vendor system directly.** Every tool call passes through one enforcement point implementing:

1. **Identity verification** — verified IdP claims; deny on missing `sub`
2. **Deny-by-default authorization with least-privilege intersection** — `permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]`. An agent can never do more than the human on whose behalf it acts.
3. **Human approval gate** — high-risk (write/irreversible) tools block until a verified reviewer identity is bound into the record (21 CFR Part 11 e-signature linkage)
4. **Short-lived scoped tokens** — minted per call via AgentCore Identity / STS; no standing service accounts
5. **PHI-masked append-only audit** — every attempt (ALLOW/DENY/PENDING_APPROVAL/ERROR) logged with lineage to the system of record

Reference logic: `platform_core/hcls_agent_platform/mcp_gateway/` — this is the testable Python model of **Amazon Bedrock AgentCore Gateway + AgentCore Identity**. Tool names (`connector_kind.operation`) map 1:1 to AgentCore Gateway targets. See `infra/cloudformation/agentcore-gateway.yaml` for the deployable registration.

> **See the whole chain run (60 seconds, no network):** `make auth-demo` executes [`demo/demo_auth.py`](demo/demo_auth.py) — IdP federation → token exchange → least-privilege intersection → human-authority commit with separation of duties → append-only audit — all five hops driven by the shipping gateway, with the deny paths (confused-deputy token, agent over-reach, self-approval, replay) shown live. CI-gated by [`governance/tests/test_auth_walkthrough.py`](governance/tests/test_auth_walkthrough.py). Captured output + shareable page: [`demo/DEMO-AUTH-TRANSCRIPT.md`](demo/DEMO-AUTH-TRANSCRIPT.md) · [`demo/demo-auth-walkthrough.html`](demo/demo-auth-walkthrough.html).

**New to positioning this layer with a customer?** `docs/WHY-THE-MCP-LAYER.md` is a plain-English explainer (with a talk track and objection handling) for why agents that *automate* systems need a governed access layer and why to fund it in Phase 1.

**Multi-agent / A2A?** The orchestration stance is recorded as ADR-001 in `ENTERPRISE-PLATFORM.md` (§5): in-process LangGraph today; A2A-through-AgentCore when multi-agent is needed. A runnable, governed reference hop is in `platform_core/hcls_agent_platform/a2a/`.

### Connector Framework
Adapter layer for each system category (RIM, DMS, Safety DB, EDC, CTMS, eTMF, RWD, QMS, CRM). Demo mode uses deterministic JSON fixtures; production connectors point at live Veeva, Medidata, and other vendor APIs. The connector interface is the same in both modes — the gateway does not know which backend is live.

### Governance & Evaluation Framework
Built in from the first commit, not added after a pilot:

| Control | Implementation |
|---|---|
| **Grounding verification** | Every number/entity in a regulated artifact is traceable to the source corpus; grounding fails fast rather than producing a hallucinated claim |
| **Prompt version registry** | Prompts are registered and hash-pinned in `governance/prompt_manifest.json`; CI fails on un-bumped drift (model-risk change control per SR 11-7 posture) |
| **Structural eval harness** | Golden artifact regression for CIOMS/E2B ICSR, benefit-risk section anatomy, CAPA completeness; runs in CI with no API keys |
| **HITL gate tests** | Framework-enforced human approval is tested, not merely documented — `governance/tests/test_hitl_gates.py` |
| **Red team** | Prompt injection, PHI exfiltration, and authorization bypass scenarios — `governance/redteam/` |
| **Fairness checks** | Demographic representativeness flags in proposed cohorts (FDA Diversity Action Plan posture) |

See `governance/README.md` for the full governance layer documentation.

---

### Canonical deployment path — the per-agent SAM golden path

**The nine per-agent SAM golden paths (`infra/golden-path-<agent>/`) are the canonical, fully-wired deploy path — all nine live-validated in a clean AWS account.** Deploy one agent from a single folder: `./deploy.sh` + `./smoke_test.sh` (exercises the human gate with a bound, separation-of-duties approval) + `./destroy.sh`. Index: [`infra/GOLDEN-PATHS.md`](infra/GOLDEN-PATHS.md). The shared CloudFormation quickstart below is the **multi-agent / scale-out reference** that nests the same control stacks; the AgentCore gateway template (`infra/cloudformation/agentcore-gateway.yaml`) is **experimental**, and `infra/terraform/` is a parity reference. Validation evidence: [`evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](evidence/CLEAN-ACCOUNT-ACCEPTANCE.md).

> **Validated live.** All nine golden paths were deployed into a clean AWS account, exercised end to
> end, and destroyed. **Before your first deploy, read [`docs/GOLDEN-PATH-DEPLOY-NOTES.md`](docs/GOLDEN-PATH-DEPLOY-NOTES.md)**
> — prereqs (SAM, Python 3.12 / or skip `sam build`, the `python-dateutil` gotcha, Bedrock optional) and
> the nine issues already found and fixed by deploying every agent.

```bash
cd infra/golden-path-02-pharmacovigilance          # any agent
bash prepare_layer.sh                                # stage platform_core + governance + agent modules
sam deploy --stack-name hcls-02-dev --region us-east-1 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --resolve-s3 --no-confirm-changeset --parameter-overrides Environment=dev ConnectorMode=fixture
python ../_smoke/resume_any.py <executionArn> "$PWD"  # start a run, approve the human gate, assert SUCCEEDED
aws cloudformation delete-stack --stack-name hcls-02-dev --region us-east-1   # + delete Retain-policy tables
```

## Security & Compliance (the CISO / CIO answer kit)

A security or architecture review can be answered entirely from these documents — each names the issue
and the control. The recurring principle: **controls are enforced in the gateway, outside the model**, so a
prompt cannot disable authorization, masking, approval, or audit; and the **legally consequential commit is
withheld from every agent** — only a bound human reviewer may commit (enforced by a test).

> **Auditors / GRC / TPRM reviewers:** the [`assurance/`](assurance/README.md) packet is a single
> curated cover sheet indexing every threat-model, NIST/GxP/Part-11 control-mapping, evidence,
> and shared-responsibility artifact under standard assurance headings.

| If they ask… | Point them at |
|---|---|
| "What's your threat model?" | [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) — STRIDE threats → control → file |
| "How do you map to NIST / HIPAA?" | [`docs/NIST-800-53-CONTROL-MATRIX.md`](docs/NIST-800-53-CONTROL-MATRIX.md) |
| "What about prompt injection / OWASP-LLM?" | [`docs/OWASP-LLM-ATLAS-MAPPING.md`](docs/OWASP-LLM-ATLAS-MAPPING.md) — OWASP LLM Top-10 + MITRE ATLAS |
| "Can the AI take an irreversible action?" | No — `policy.CONSEQUENTIAL_COMMITS` is withheld from every agent grant; a bound human reviewer commits ([`SECURITY.md`](SECURITY.md) §3) |
| "How is human approval tamper-proof?" | Bound tokens: single-use, separation-of-duties, args-bound (`mcp_gateway/approvals.py`); `STRICT_APPROVAL=1` in prod |
| "Does PHI leave our account?" | Masked before any model/audit write; Bedrock reached only over AWS PrivateLink (a regional AWS service, not in-VPC hosting); in-account AWS traffic kept on VPC endpoints, **configurable, on by default** in the customer-VPC deployment — no egress to external AI APIs ([`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) T4, `infra/cloudformation/network.yaml`) |
| "What's your incident response / key management?" | [`docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`](docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md) |
| "What's reference vs. what we must finish?" | [`docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md) |
| "How do we report a vulnerability?" | [`SECURITY.md`](SECURITY.md) |
| "How do we know it behaves?" | **580 automated tests** (incl. governance + red-team + the commit-withholding test), one command: `make test` |

For per-stakeholder talk tracks see [`docs/STAKEHOLDER-SECURITY-BRIEFINGS.md`](docs/STAKEHOLDER-SECURITY-BRIEFINGS.md) and the board deck `decks/HCLS-CIO-Adoption-Review.pptx`.

---

## AWS Deployment

> **Canonical path first.** The supported deploy path is the per-agent SAM golden path above
> ([`infra/GOLDEN-PATHS.md`](infra/GOLDEN-PATHS.md)); everything in this section is the
> **multi-agent / scale-out reference**, not the live-validated canonical path.

**New customer account → running agent in two commands.** Build the code bundles (deps
vendored in) and deploy the master CloudFormation stack:

```bash
scripts/build_lambdas.sh 02-pharmacovigilance
CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket \
  scripts/deploy.sh 02-pharmacovigilance dev portable native
#                   ^AgentId            ^env ^GatewayMode ^DeployMode
```

> **Read this first:** [`docs/DEPLOY-QUICKSTART.md`](docs/DEPLOY-QUICKSTART.md) is the
> copy-paste, empty-account-to-live-agent guide (prerequisites → build → deploy →
> create the agent → human-gate smoke test → go-live checklist). The deeper console
> click-through with screenshots is [`docs/DEPLOYMENT-HANDBOOK.md`](docs/DEPLOYMENT-HANDBOOK.md).

### CloudFormation Quick Deploy (multi-agent / scale-out reference)
One master template provisions a customer-isolated environment:

```
infra/cloudformation/
├── quickstart.yaml          # Master — nests all stacks; GatewayMode + DeployMode switch the variants
├── network.yaml             # VPC, private subnets, S3/DynamoDB + PrivateLink VPC endpoints, restricted egress SG, flow logs (NAT retained as fallback)
├── security.yaml            # KMS, Bedrock Guardrail, Cognito (pool + app client + optional IdP federation), least-privilege agent role
├── data.yaml                # Append-only DynamoDB audit, S3 Object Lock WORM, HITL table
├── connectors.yaml          # One connector Lambda per system of record (governed backend per gateway target)
├── gateway-portable.yaml    # MCP layer — Path A: API Gateway + Cognito JWT authorizer (ANY region)
├── agentcore-gateway.yaml   # MCP layer — Path B: Bedrock AgentCore Gateway + Identity (AgentCore regions)
└── agent-service.yaml       # The agent — native (Step Functions + Lambdas + human gate, VPC-attached) or container (ECS Fargate behind an internal ALB)
```

### Two MCP gateway paths, one policy (`GatewayMode`)
Both front doors route to the **same connector Lambdas** and enforce the **same**
deny-by-default decision (`platform_core`'s `MCPGateway`). Pick by region/posture:

| `GatewayMode` | Front door | Region support | Use when |
|---|---|---|---|
| `portable` (default) | API Gateway HTTP API + Cognito JWT authorizer | **any commercial Region** | a new customer account — deploys day one |
| `agentcore` | Bedrock AgentCore Gateway + Identity | AgentCore-enabled Regions | customer standardizing on AgentCore |

Migrating Path A → Path B later changes only the gateway stack — agent and connector code are untouched.

### Two ways to run the agent (`DeployMode`)
- **`native`** — deterministic core in Lambda, Strands/Bedrock drafting, **Step Functions**
  orchestration with a `waitForTaskToken` HITL gate. The state machine *is* the agent.
- **`container`** — lift the LangGraph agent unchanged onto **ECS Fargate** (ARM64, the
  AgentCore `/invocations` + `/ping` contract) **behind an internal Application Load Balancer**
  (target group + `/ping` health check + service-DNS output in `agent-service.yaml`); the running
  service *is* the agent, and the same image registers with AgentCore Runtime in an AgentCore Region.
  `scripts/deploy.sh` **requires `CONTAINER_IMAGE_URI`** in container mode and refuses otherwise (no
  silent broken stack). This path is a complete **reference / scale-out** pattern; the SAM golden path
  above is the canonical pilot path.

### Network isolation (two explicit modes: PrivateOnly / ApprovedExternalConnectors)

The deployment offers **two explicit network modes** (`NetworkMode` in `network.yaml`): **PrivateOnly** (default) creates **no NAT route at all** — private subnets reach AWS only through the VPC endpoints below, so no public egress path exists; **ApprovedExternalConnectors** adds a NAT route for dependencies without an in-region endpoint (e.g. an out-of-account live vendor connector), to be paired with an egress proxy / domain allowlist / Network Firewall and logged exceptions. In either mode:

- **Gateway VPC endpoints** for **S3** and **DynamoDB** (audit, review, WORM access stays on the AWS backbone).
- **Interface (PrivateLink) VPC endpoints** for **bedrock-runtime, Secrets Manager, KMS, CloudWatch Logs, SNS, Step Functions, and Lambda**, each locked to **443 from the app security group only** via a dedicated endpoint SG.
- **App security-group egress restricted to 443** (was previously all-protocols/all-destinations).
- **Lambdas are VPC-attached** (private subnets + app SG) in both the golden path and the shared service template when network params are supplied; the **container service runs in private subnets behind an internal ALB**.
- **VPC Flow Logs** record all ENI traffic (accepted + rejected) for audit.
- A **NAT gateway exists only in ApprovedExternalConnectors mode** (PrivateOnly creates no NAT and no `0.0.0.0/0` route). Even when present, in-account AWS-service traffic uses the endpoints, not the NAT.

> **Accurate framing.** With Bedrock + the customer-VPC deployment and these endpoints, in-account AWS service traffic does not egress to the public internet. This is **configurable** (the endpoints are part of `network.yaml`) and **on by default** in that deployment. In **PrivateOnly** mode there is no NAT route, so no public-egress path exists from the private subnets; **ApprovedExternalConnectors** mode intentionally adds one for vendor dependencies, which the customer fronts with an egress proxy / allowlist / firewall. Defined in `infra/cloudformation/network.yaml`.

**IdP federation.** `security.yaml` provisions an `AWS::Cognito::UserPoolIdentityProvider` (+ hosted-UI domain + federated app-client wiring), gated by the `FederationEnabled` condition (on when `IdpMetadataUrl` is non-empty; native Cognito otherwise). The reference template implements a **SAML** provider; **OIDC** is supported by the documented provider-type adaptation (not auto-selected by config). Okta and Microsoft Entra ID setup, the group→`custom:hcls_role` claim mapping, and the on/off switch are in [`docs/IDP-FEDERATION-RUNBOOK.md`](docs/IDP-FEDERATION-RUNBOOK.md).

### Terraform Parity
`infra/terraform/` provides equivalent IaC for customers whose platform engineering teams standardize on Terraform. Identical resource topology; different surface syntax.

See `aws-native-reference/README.md` for the per-agent native rebuilds.

---

## Running the Demo (No API Key Required)

```bash
# Clone and set up (Agent 01 is the reference)
cd 01-regulatory-writing-agent
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../platform_core

# Run in demo mode — deterministic, no LLM call
export EXTRACT_MODE=demo
streamlit run app.py                               # http://localhost:8501

# Run the full test suite (governance + platform + agent)
PYTHONPATH=platform_core pytest platform_core/tests governance tests/ -q

# Run the eval harness (grades golden artifacts, no API key)
python -m governance.evals.run_evals
```

### Live path (Agent 02 — Bedrock + real connector)

Agent 02 ships a customer-ready live demo. It runs end-to-end with no API key (deterministic), and flips to live Amazon Bedrock inference and a real HTTP safety-system connector by configuration — swap one URL from the bundled local reference service to the customer's Argus / Veeva Safety gateway.

```bash
cd 02-pharmacovigilance-agent
# runs the full ICSR workflow end-to-end against the live connector (local reference service);
# auto-selects Bedrock -> Anthropic -> deterministic demo
PYTHONPATH=.:../platform_core python demo/demo_live.py
# point at real systems:
#   export LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...
#   export CONNECTOR_MODE=live SAFETY_BASE_URL=https://safety.customer.example
```

See `02-pharmacovigilance-agent/demo/DEMO-LIVE.md` for the full runbook (Bedrock prerequisites, env vars, Argus/Veeva endpoint mapping, security talking points).

---

## Field Enablement Collateral

Ready-to-use GTM material lives at the repository root:

| Artifact | Use |
|---|---|
| `decks/HCLS-01..10-*.pptx` | **Per-agent professional decks** (9 built agents + 1 roadmap; 6-slide: issue → cost of doing nothing → governed pipeline → AWS architecture & traffic flow → proof/deploy). Every stat cited and source-class-tagged; speaker notes on every slide. |
| `decks/HCLS-Agentic-AI-Suite-Executive-Overview.pptx` | ~11-slide suite overview: thesis, shared architecture, 8-agent portfolio, governance spine, maturity ladder, land-and-expand, cost-of-inaction. |
| `decks/HCLS-CIO-Adoption-Review.pptx` | **Board-ready CIO / CISO / Director of Architecture deck** — honest-broker verdict, six gateway controls, shortfalls, shared-responsibility matrix, phased path, go/no-go. |
| `HCLS-Agentic-AI-Suite-Executive-Overview.pptx` | Original 16-slide executive deck (root) for sales, SAs, and delivery |
| `HCLS-Customer-Teaser-5slide.pptx` | 5-slide customer-facing teaser |
| `HCLS-One-Pager.pdf` | One-page leave-behind (print-ready; editable `.pptx` source included) |

The decks are generated from cited source-of-truth files and regenerate with `node decks/build-agent-decks.js` and `node decks/build-cio-deck.js` (see `decks/README.md`). Every figure traces to **`gtm/HCLS-DECK-SOURCES.md`** (each stat tagged `[gov/peer-reviewed]` · `[industry-research]` · `[sector-press/estimate]` · `[vendor]` · `[modeled]` with URLs). The GTM spine also includes `gtm/DECK-CONTENT-SPEC.md` (per-agent content contract), `gtm/DEMO-STORYBOARD.md` (a repeatable ~25-min customer demo), and `gtm/roi-calculator/` (an SA-fillable ROI workbook).

Beyond the eight core-lifecycle agents, the suite extends into the manufacturing and discovery ends of the lifecycle. **09 Manufacturing Batch-Review** (CMC/GxP) is **built to flagship depth** — the ninth agent above (`09-manufacturing-batch-review-agent/` + AWS-native rebuild). **10 Scientific Intelligence & Target Discovery** (R&D) is a **roadmap agent** at Documented maturity — a cited deck + design spec (`docs/specs/10-scientific-intelligence.md`), not yet built in code. **Both 09 and 10 carry fully cited entries in `gtm/HCLS-DECK-SOURCES.md`** (every stat source-class-tagged with URLs); the executive overview intentionally stays at the 8 core-lifecycle agents by design.

Per-agent **tailored deployment handbook PDFs** are in `deliverables/agent-handbooks/`, and all collateral regenerates from source with `make handbooks` (see `tooling/handbooks/`). Deeper written collateral: `offerings/` (POC, pilot, assessment, managed service, TCO/ROI calculator, battlecard, SOW template, objection-handling, competitive, TPRM), `runbooks/` (incident, DR, HITL queue, model degradation), and `docs/STAKEHOLDER-SECURITY-BRIEFINGS.md`.

### Positioning to a CIO, CSO/CISO, or Director of Architecture

The deck system is built around the buyer in the room — lead with the one sentence that lands for each:

- **CIO** — *"One governed control plane carries all nine workloads; this compresses an SI-led build instead of adding ungoverned shadow AI."* The platform is the asset; the agents are interchangeable, regulated workloads on top of it. Open with `Executive-Overview`, land on the maturity ladder and land-and-expand path.
- **CSO / CISO** — *"The controls are enforced in the gateway, outside the model — a prompt cannot disable deny-by-default, the HITL gate, PHI masking, or the audit trail."* Use the `CIO-Adoption-Review` "Why a CISO can say yes" slide and the red-team demo; the bright line (causality, reportability, what's submitted, what reaches an HCP) is never decided by the agent.
- **Director of Architecture** — *"The AWS reference is real and deployable — CloudFormation dual-gateway, private-connectivity Bedrock + Guardrails, Step Functions `waitForTaskToken` HITL — and the gaps are scoped honestly."* Drive the per-agent **architecture & traffic-flow** slide, `docs/SUITE-ARCHITECTURE.md`, `docs/WELL-ARCHITECTED-REVIEW.md`, and the shared-responsibility matrix, then a `docs/DEPLOY-QUICKSTART.md` walkthrough.

For the full run of show, see **`gtm/DEMO-STORYBOARD.md`**.

**AWS go-to-market mechanics** — the following docs answer the questions AWS sellers and SAs ask before a deal can progress:

| Document | Answers |
|---|---|
| `docs/AWS-FUNDING-AND-GTM.md` | Who pays for the pilot? MAP, PoA, ISV Accelerate |
| `docs/WELL-ARCHITECTED-REVIEW.md` | WAF + GenAI Lens pillar-by-pillar mapping for WAFR sessions |
| `docs/SHARED-RESPONSIBILITY-MATRIX.md` | AWS vs. SI vs. institution — what each party owns |
| `docs/AWS-ACCOUNT-PREREQUISITES.md` | Pre-flight checklist: Bedrock access, quotas, AgentCore, Cognito |
| `docs/AWS-MARKETPLACE-PATH.md` | Marketplace listing and private offer mechanics |
| `offerings/BATTLECARD.md` | Qualifying questions, discovery cheat-sheet, objection one-liners |
| `offerings/SOW-TEMPLATE.md` | Fill-in-the-blank POC/Pilot SOW shell |
| `offerings/TCO-MODEL.md` | Bedrock inference + infrastructure cost estimates + ROI worksheet |

`EXTRACT_MODE=demo` routes every gateway call through the fixture connectors and bypasses the LLM. The full workflow — intake, regulatory intelligence retrieval, evidence assembly, draft section, grounding/compliance check, human review gate, finalize — executes against deterministic data. Suitable for customer demonstrations before any AWS account is configured.

---

## Repository Structure

```
hcls-ai-agents/
├── README.md                            # This file
├── SUITE-STATUS.md                     # Current state + changelog of latest changes
├── SOLUTION-FIELD-GUIDE.md             # SI sales + SA qualification and adoption path
├── ENTERPRISE-PLATFORM.md              # Platform story — API modernization, MCP gateway, compliance layers
├── HCLS-Agentic-AI-Suite-Executive-Overview.pptx   # 16-slide field-enablement deck
├── HCLS-Customer-Teaser-5slide.pptx    # 5-slide customer-facing teaser
├── HCLS-One-Pager.pdf                  # One-page leave-behind (PDF) + .pptx source
│
├── 01-regulatory-writing-agent/        # Regulatory Writing & Intelligence (Demonstrated + Deployable reference)
├── 02-pharmacovigilance-agent/         # Pharmacovigilance — ICSR Case Intake (+ demo/ live Bedrock + real-connector path)
├── 03-clinical-trial-ops-agent/        # Clinical Trial Ops & TMF
├── 04-site-patient-matching-agent/     # Site Selection & Patient Matching
├── 05-quality-capa-agent/              # Quality / CAPA & Complaints
├── 06-protocol-design-agent/           # Clinical Protocol Design & Feasibility
├── 07-rwe-heor-agent/                  # Real-World Evidence / HEOR
├── 08-medical-affairs-msl-agent/       # Medical Affairs / MSL Copilot
│
├── decks/                              # GTM decks + generators (8 agent + overview + CIO/CISO board deck)
│   ├── build-agent-decks.js           # pptxgenjs: 8 professional agent decks + executive overview
│   └── build-cio-deck.js              # pptxgenjs: CIO / CISO / Architecture adoption-review deck
│
├── gtm/                                # Citation spine + demo + ROI
│   ├── HCLS-DECK-SOURCES.md            # Every deck stat, source-class-tagged, with URLs
│   ├── DECK-CONTENT-SPEC.md            # Per-agent deck content contract (auditable)
│   ├── DEMO-STORYBOARD.md              # Repeatable ~25-min customer demo run of show
│   └── roi-calculator/                # SA-fillable ROI workbook + generator
│
├── platform_core/                      # Shared platform — LLM factory, PHI masker, MCP gateway, connectors
│   └── hcls_agent_platform/
│       ├── mcp_gateway/                # Reference logic for Bedrock AgentCore Gateway + Identity
│       ├── llm_factory.py               # Anthropic / in-account Bedrock + Guardrails
│       ├── phi.py                        # PHI/PII masking (HIPAA Safe Harbor identifiers)
│       ├── secrets.py · auth.py · tracing.py
│       └── connectors/                   # fixture + live (incl. LiveSafetyConnector, real HTTP)
│
├── governance/                         # Governance & evaluation framework (grounding, evals, HITL tests, red team)
│
├── aws-native-reference/               # AWS-native deployment (container + native) for all 9 agents
│
├── scripts/
│   ├── build_lambdas.sh                # Package every agent + connector zip WITH deps vendored in
│   └── deploy.sh                       # Stage to S3 + deploy the quickstart stack (new account)
│
├── infra/
│   ├── cloudformation/                 # CloudFormation quick-deploy (connectors + 2 gateway modes + agent)
│   └── terraform/                      # Terraform reference skeleton (not parity)
│
├── docs/
│   ├── DEPLOY-QUICKSTART.md            # Copy-paste: empty account -> running agent (start here)
│   ├── DEPLOYMENT-HANDBOOK.md          # Console + CLI step-by-step deploy (deep walkthrough + screenshots)
│   ├── WHY-THE-MCP-LAYER.md            # Account-team explainer: why agents need a governed access layer
│   ├── SUITE-ARCHITECTURE.md           # 6-layer reference architecture + AWS service mapping
│   ├── STAKEHOLDER-SECURITY-BRIEFINGS.md  # Per-stakeholder security pitch (CIO/CISO/CMO/RegAffairs/PV/QA/ClinOps/CPO/MedAffairs/Procurement/IRB)
│   ├── AWS-FUNDING-AND-GTM.md          # MAP, PoA, ISV Accelerate — who pays for the pilot
│   ├── WELL-ARCHITECTED-REVIEW.md      # WAF + GenAI Lens pillar-by-pillar mapping
│   ├── SHARED-RESPONSIBILITY-MATRIX.md # AWS vs. SI vs. institution responsibility breakdown
│   ├── AWS-ACCOUNT-PREREQUISITES.md   # Pre-flight checklist: Bedrock, AgentCore, quotas, Cognito
│   └── AWS-MARKETPLACE-PATH.md        # Marketplace listing and private offer mechanics
│
└── offerings/                          # Consulting packaging
    ├── POC-OFFERING.md
    ├── PILOT-OFFERING.md
    ├── ASSESSMENT-OFFERING.md
    ├── MANAGED-SERVICE-OFFERING.md
    ├── COST-ROI-MODEL.md               # Narrative ROI framework
    ├── TCO-MODEL.md                    # AWS run costs + ROI worksheet (SA-ready numbers)
    ├── BATTLECARD.md                   # Qualifying questions, discovery, objection one-liners
    ├── SOW-TEMPLATE.md                 # Fill-in-the-blank POC/Pilot SOW shell
    ├── OBJECTION-HANDLING.md
    ├── COMPETITIVE-POSITIONING.md
    └── TPRM-DUE-DILIGENCE-PACKET.md
```

---

## Compliance Disclaimer

This suite is a **decision-support accelerator** for qualified life-sciences professionals. It is not a validated computer system, a certified medical device, or an approved regulatory submission tool. AI-generated content requires human review and approval by a qualified professional before any consequential action — submission, ICSR reporting, CAPA closure, or MLR approval. The AI never takes irreversible actions autonomously.

Customers are responsible for: computer-system validation (CSV/CSA) for the intended use; IdP integration and role mapping to their HR system; connector validation against live vendor systems; Bedrock Guardrail configuration appropriate to their product and patient population; and change-control procedures for prompt and model updates.

This accelerator provides the control design. The customer operationalizes, validates, and accepts accountability for it.
