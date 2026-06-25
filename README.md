# HCLS AI Agent Suite
### Governed AI Agents for Life Sciences — Built on AWS

[![CI](https://github.com/virtualryder/hcls-ai-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/virtualryder/hcls-ai-agents/actions/workflows/ci.yml)

> **The agents are not the product. The governed platform that makes them deployable, auditable, and compliant is.**

A large systems integrator deploying AI in a pharmaceutical, biotech, medtech, or CRO environment cannot hand a customer a collection of LLM calls and call it done. Every regulated artifact an agent touches — an ICSR report, a submission section, a CAPA record — carries data-integrity, e-signature, and accountability obligations that exist before the first line of agent code is written. This suite embeds those controls from the first commit: deny-by-default authorization, PHI masking, grounding verification, prompt version pinning, a human gate that is framework-enforced (not merely documented), and a tamper-evident audit trail that satisfies 21 CFR Part 11.

The result is a deployable accelerator — not a certified product — that gives an SI engagement team a credible, compliant starting point across nine high-value life-sciences workflows.

**Repository status (current):** all 9 agents built to flagship depth · 9 AWS-native rebuilds (Strands + Step Functions) · a live Amazon Bedrock + real-connector reference path (Agent 02) · **488 automated tests passing** with no API key · one-command CloudFormation quick-deploy (connector Lambdas + two interchangeable MCP gateway modes + native/container agent) deployable in a new customer account in any Region · Terraform parity · executive deck, 5-slide customer teaser, and one-page leave-behind included.

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

**All nine agents are built to flagship depth** — a full LangGraph workflow, governed tool access, deterministic fixtures, flagship-level test suites, a Streamlit dashboard, a four-document doc set, and a matching **AWS-native rebuild** (Strands + Step Functions with a `waitForTaskToken` human gate). Agent 02 (Pharmacovigilance) additionally ships a **live path**: real Amazon Bedrock inference and a real HTTP system-of-record connector, exercised end-to-end (see `02-pharmacovigilance-agent/demo/`). The suite sits at **Demonstrated + Deployable-by-design**: 488 automated tests pass with no API key; production-readiness (CSV/CSA, live integration, penetration test) is the engagement. (A tenth agent, 10 Scientific Intelligence & Target Discovery, is at roadmap/Documented maturity — cited deck + design spec.)

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

---

## Shared Platform

Every agent shares the same platform stack. Controls compound: a governance improvement to the PHI masker, the grounding checker, or the audit trail benefits all nine agents simultaneously.

### LLM Factory
A single abstraction layer routes inference to **Anthropic Claude** (API) or **Amazon Bedrock** (in-account, no data leaves the customer VPC) depending on deployment mode. `EXTRACT_MODE=demo` bypasses the LLM entirely for local testing.

### PHI Masking
Structured entity recognition (NER) replaces patient identifiers, dates of birth, and case-linkable fields with stable pseudonyms before any content enters a prompt or an audit record. The masking layer is stateless and runs before every gateway invocation.

### MCP Authorization Gateway
The governed front door between every agent and every system of record. **No agent calls a vendor system directly.** Every tool call passes through one enforcement point implementing:

1. **Identity verification** — verified IdP claims; deny on missing `sub`
2. **Deny-by-default authorization with least-privilege intersection** — `permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]`. An agent can never do more than the human on whose behalf it acts.
3. **Human approval gate** — high-risk (write/irreversible) tools block until a verified reviewer identity is bound into the record (21 CFR Part 11 e-signature linkage)
4. **Short-lived scoped tokens** — minted per call via AgentCore Identity / STS; no standing service accounts
5. **PHI-masked append-only audit** — every attempt (ALLOW/DENY/PENDING_APPROVAL/ERROR) logged with lineage to the system of record

Reference logic: `platform_core/hcls_agent_platform/mcp_gateway/` — this is the testable Python model of **Amazon Bedrock AgentCore Gateway + AgentCore Identity**. Tool names (`connector_kind.operation`) map 1:1 to AgentCore Gateway targets. See `infra/cloudformation/agentcore-gateway.yaml` for the deployable registration.

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

## AWS Deployment

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

### CloudFormation Quick Deploy (primary path)
One master template provisions a customer-isolated environment:

```
infra/cloudformation/
├── quickstart.yaml          # Master — nests all stacks; GatewayMode + DeployMode switch the variants
├── network.yaml             # VPC, subnets, NAT, security groups
├── security.yaml            # KMS, Bedrock Guardrail, Cognito (pool + app client), least-privilege agent role
├── data.yaml                # Append-only DynamoDB audit, S3 Object Lock WORM, HITL table
├── connectors.yaml          # One connector Lambda per system of record (governed backend per gateway target)
├── gateway-portable.yaml    # MCP layer — Path A: API Gateway + Cognito JWT authorizer (ANY region)
├── agentcore-gateway.yaml   # MCP layer — Path B: Bedrock AgentCore Gateway + Identity (AgentCore regions)
└── agent-service.yaml       # The agent — native (Step Functions + Lambdas + human gate) or container (ECS Fargate)
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
  AgentCore `/invocations` + `/ping` contract). The running service *is* the agent; the same
  image registers with AgentCore Runtime in an AgentCore Region. No code changes.

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
| `decks/HCLS-01..10-*.pptx` | **Per-agent AWS-style decks** (9 built agents + 1 roadmap; 6-slide: issue → cost of doing nothing → governed pipeline → AWS architecture & traffic flow → proof/deploy). Every stat cited and source-class-tagged; speaker notes on every slide. |
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
- **Director of Architecture** — *"The AWS reference is real and deployable — CloudFormation dual-gateway, in-VPC Bedrock + Guardrails, Step Functions `waitForTaskToken` HITL — and the gaps are scoped honestly."* Drive the per-agent **architecture & traffic-flow** slide, `docs/SUITE-ARCHITECTURE.md`, `docs/WELL-ARCHITECTED-REVIEW.md`, and the shared-responsibility matrix, then a `docs/DEPLOY-QUICKSTART.md` walkthrough.

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
│   ├── build-agent-decks.js           # pptxgenjs: 8 AWS-style agent decks + executive overview
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
│   └── terraform/                      # Terraform parity
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
