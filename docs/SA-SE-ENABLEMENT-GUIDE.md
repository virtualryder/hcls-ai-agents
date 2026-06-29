# SA / SE Enablement Guide — HCLS AI Agent Suite

For AWS Solution Architects, partner Solution Engineers, and SI delivery architects who
need to **pitch, demo, and scope** the suite with a life-sciences customer. Read this once;
it points you at the right artifact for every moment of a deal.

## The one-sentence pitch

> *"The agent isn't the product — the governed platform that makes it 21 CFR Part 11 / GxP-defensible and deployable on AWS is. We hand your SI a compliant, auditable starting point across nine high-value life-sciences workflows, so you compress an SI-led build instead of fielding ungoverned shadow AI."*

## Know your room (lead with the right sentence)

| Persona | Their question | Your lead | Artifact |
|---|---|---|---|
| **CIO** | "Is this another point tool?" | One control plane, nine workloads; the platform is the asset. | `decks/HCLS-Agentic-AI-Suite-Executive-Overview.pptx` |
| **CSO / CISO** | "Can a prompt turn the controls off?" | No — controls live in the gateway, outside the model. | `decks/HCLS-CIO-Adoption-Review.pptx` (slide 4) + red-team demo |
| **Director of Architecture** | "Is it actually deployable?" | CloudFormation dual-gateway, in-VPC Bedrock, Step Functions HITL — and the gaps are scoped. | per-agent architecture slide + `docs/SUITE-ARCHITECTURE.md` |
| **VP Quality / Reg Affairs** | "Who owns the regulated decision?" | A named human, every time — enforced in the framework. | the bright-line callout on every agent deck |
| **CFO / procurement** | "What does inaction cost?" | The cited cost-of-doing-nothing, modeled to their volumes. | `gtm/roi-calculator/` |

## The deal flow and which artifact serves it

1. **Qualify** → `offerings/BATTLECARD.md` (qualifying questions, discovery cheat-sheet).
2. **First meeting** → `decks/HCLS-Agentic-AI-Suite-Executive-Overview.pptx`.
3. **Pick the wedge agent** → the per-agent deck closest to their pain (`decks/HCLS-0X-*.pptx`). Land-first set: **01 Regulatory Writing · 02 Pharmacovigilance · 03 Trial Ops/TMF · 08 Medical Affairs.**
4. **Demo** → `gtm/DEMO-STORYBOARD.md` (the ~25-min run of show; Agent 02 is the live path).
5. **Build the business case** → `gtm/roi-calculator/HCLS-AI-Suite-ROI-Calculator.xlsx` + `offerings/TCO-MODEL.md`.
6. **Win the security/architecture review** → `decks/HCLS-CIO-Adoption-Review.pptx`, `docs/WELL-ARCHITECTED-REVIEW.md`, `docs/SHARED-RESPONSIBILITY-MATRIX.md`, `docs/STAKEHOLDER-SECURITY-BRIEFINGS.md`.
7. **Fund it** → `docs/AWS-FUNDING-AND-GTM.md` (MAP / PoA / ISV Accelerate), `docs/AWS-MARKETPLACE-PATH.md`.
8. **Scope the engagement** → `offerings/POC-OFFERING.md`, `offerings/PILOT-OFFERING.md`, `offerings/SOW-TEMPLATE.md`.
9. **Pre-flight the account** → `docs/AWS-ACCOUNT-PREREQUISITES.md`.
10. **Deploy** → `docs/DEPLOY-QUICKSTART.md` then `docs/DEPLOYMENT-HANDBOOK.md`.

## The five claims you can make (and how to keep them honest)

1. **"503 automated tests pass with no API key."** Run them on screen — it's the single best credibility move. Governance is in code, not slideware.
2. **"Controls are enforced outside the model."** Show the red-team prompt-injection / authorization-bypass test denying.
3. **"Every figure on the deck is cited."** Point at the source tag on-slide and `gtm/HCLS-DECK-SOURCES.md`.
4. **"It deploys into a new account in any Region."** `make build-lambdas` + `make deploy` → CloudFormation quickstart (connectors + dual gateway + agent).
5. **"The consequential decision is always human."** The HITL gate is framework-enforced and *fails closed* — show it block as `PENDING_APPROVAL`.

## What NOT to say

- Do **not** claim it is production-ready, computer-system-validated (CSV/CSA), certified, or penetration-tested — those are the engagement (rung 4 of the maturity ladder).
- Do **not** lead with a `[vendor]` or `[modeled]` figure — flag them out loud and lead with `[gov/peer-reviewed]`.
- Do **not** promise an ROI for patient-matching (04), CAPA (05), or protocol-design (06) AI — independent benchmarks aren't established; use the labeled modeled math.

## Objection quick-reference

| Objection | Response |
|---|---|
| "It's not finished." | Correct — and that's normal for governed AI on regulated GxP records. The gaps are named on the shortfalls slide and scoped on the backlog slide. |
| "Why not just use a vendor SaaS?" | A SaaS can't take your GxP / Part 11 accountability, and your data shouldn't leave your VPC. Here Bedrock runs in-account and PHI is masked before any model call. |
| "Bedrock vs. best model of the week?" | The LLM factory abstracts the model — swap without re-architecting. VPC-private inference + IAM governance won the trade. |
| "This is a lot of work." | It's the same list for *any* governed AI build — the difference is here it's written down and scoped, not discovered mid-project. |

See `offerings/OBJECTION-HANDLING.md` for the full set.
