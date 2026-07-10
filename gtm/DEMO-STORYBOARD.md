# HCLS AI Agent Suite — Demo Storyboard

> A repeatable, ~25-minute customer demo that proves the thesis: **the agent isn't the
> product — the governed platform is.** It pairs the decks with a live run of the suite so a
> pharma CIO / CISO / Director of Architecture sees both the business case and the controls
> working. Designed to run with **no customer AWS account** (demo mode) and to escalate to a
> **live AWS path** (Agent 02) when one is available.

## Audience & goal

| Persona | What they need to leave believing |
|---|---|
| **CIO** | One governed control plane carries all nine workloads; this compresses an SI build rather than adding shadow AI. |
| **CISO / CSO** | Controls are enforced in the gateway, outside the model — a prompt cannot disable deny-by-default, the HITL gate, PHI masking, or the audit trail. |
| **Director of Architecture** | The AWS reference is real and deployable (CloudFormation, dual MCP gateway, private-connectivity Bedrock, Step Functions HITL), and the gaps are scoped honestly. |
| **VP Quality / Head of Regulatory** | Every consequential decision stays human; everything is traceable and 21 CFR Part 11 / GxP-defensible. |

## Pre-flight (the day before)

1. `make build-lambdas` then `make deploy` into a sandbox account **(optional — only for the live segment)**, or run everything in `EXTRACT_MODE=demo` locally with no API key.
2. Open the decks: `HCLS-Agentic-AI-Suite-Executive-Overview.pptx`, `HCLS-02-Pharmacovigilance.pptx`, and `HCLS-CIO-Adoption-Review.pptx`.
3. Have `docs/SUITE-ARCHITECTURE.md` and `docs/DEPLOY-QUICKSTART.md` open in a second window.
4. Run the test suite once on screen as a credibility opener: **575 tests, no API key.**

## Run of show (~25 min)

### 1 · Frame the thesis — 3 min  *(Executive Overview, slides 1–2)*
Open on "Everyone's moving, few are governed." Land the McKinsey value ($60–110B/yr), the ~5% who've realized it, and the FDA Jan-2025 AI guidance. **Message:** the gap between adoption and governance is the opportunity, and in a workflow where a hallucinated number is a data-integrity defect, governance is the product.

### 2 · The shared control plane — 4 min  *(Executive Overview, slide 3 — architecture)*
Trace the eight numbered flow steps once. Emphasize: per-customer VPC + dedicated validated account; Cognito federation; the **MCP authorization gateway** as the single governed front door; private-connectivity Bedrock + Guardrails (PHI masked first); S3 Object Lock + DynamoDB append-only audit. **Message:** every agent inherits this — improve a control once, all nine benefit.

### 3 · Live governed run — 8 min  *(Agent 02 — Pharmacovigilance)*
The flagship live segment. Walk an inbound adverse-event case through the pipeline:
- **Ingest & mask** — show PHI replaced with stable pseudonyms *before* anything reaches the model.
- **Triage / dedupe / MedDRA code / draft E2B narrative** — the agent does the high-volume work.
- **Human gate** — attempt to finalize the reportable case; the framework **blocks as PENDING_APPROVAL** until a safety-physician identity is bound. Show the deny on a wrong-role attempt.
- **Audit** — open the append-only record: actor, timestamp, sources, model+prompt version, ALLOW/DENY/PENDING lineage.

> If running live on AWS, this is the real Bedrock + real HTTP-connector path (`02-pharmacovigilance-agent/demo/`). If running in demo mode, it's deterministic fixtures — say so; the *control behavior* is identical.

### 4 · Prove a control can't be bypassed — 3 min  *(red-team)*
Run a prompt-injection / authorization-bypass attempt from `governance/redteam/`. Show the gateway denies it because authorization lives **outside** the model. **Message:** this is what a CISO signs off on.

### 5 · The business case for one agent — 3 min  *(any agent deck, slides 2–3 + ROI calculator)*
Pick the agent closest to the customer's pain (e.g. 03 Trial Ops for a sponsor with enrollment delays). Show the cited headline, the cost of doing nothing with the arithmetic visible, then plug their real volumes into `gtm/roi-calculator/HCLS-AI-Suite-ROI-Calculator.xlsx`.

### 6 · The honest close — 4 min  *(CIO Adoption Review, slides 5, 9, 11–12)*
Show the **shortfalls** slide (you name the gaps first), the **shared-responsibility matrix** (who owns what — GxP accountability stays with them), the **phased adoption path**, and the **go/no-go decision**. Ask for the specific next step: a funded Phase-1 pilot on Agents 01/02/03/08.

## The three things the customer must say yes to (the ask)
1. A **funded SI-led engagement**, not a product purchase.
2. They own the **GxP / 21 CFR Part 11 quality program, the IdP, and the reviewer roster**.
3. Budget for **CSV/CSA validation and a penetration test** before any GxP go-live.

## Fallback asks
- **Smallest viable yes:** a single-agent pilot on **Agent 02** (the live path) — most concrete, fastest to demonstrate value.
- **Architecture-led buyer:** offer the deep-dive on `docs/SUITE-ARCHITECTURE.md` + `docs/WELL-ARCHITECTED-REVIEW.md` and a deploy walkthrough from `docs/DEPLOY-QUICKSTART.md`.

## Do / don't
- **Do** lead every metric with its source class and flag vendor/modeled figures out loud.
- **Do** show the human gate failing closed — it's the most persuasive moment in the demo.
- **Don't** claim production-readiness, CSV validation, or any certification the suite doesn't have.
- **Don't** let "Deployable" be heard as "in production" — that's the engagement.
