# HCLS AI Agent Suite — Deck Content Spec

> **Verified June 2026.** The deck builder ([`../decks/build-agent-decks.js`](../decks/build-agent-decks.js))
> is the executable source of truth — this spec documents the per-agent content contract so a
> reviewer can audit each claim without reading JavaScript. Every ROI figure cites an entry in
> [`HCLS-DECK-SOURCES.md`](HCLS-DECK-SOURCES.md) and is tagged on-slide `[gov/peer-reviewed]`,
> `[industry-research]`, `[sector-press/estimate]`, `[vendor]`, or `[modeled]`. Outcomes are
> *documented results applied to a reference sponsor* — modeled to the customer's baseline, never
> guaranteed. Lead each slide with the strongest source class; flag vendor and estimate figures
> on-slide.

## Shared platform (every agent inherits it)

CloudFront + WAF edge; Cognito / IAM Identity Center federation with reviewer-role scoping
(regulatory writer / safety physician / CRA / quality owner / MSL / MLR reviewer); MCP
authorization gateway (managed AgentCore Gateway **or** portable API Gateway + Cognito JWT) with
deny-by-default + least-privilege intersection + short-lived scoped tokens; Amazon Bedrock (Claude)
+ Guardrails in-VPC (PHI never egresses after masking); PHI masker; grounding verification; HITL
gate (AgentCore approval or Step Functions `waitForTaskToken`); S3 Object Lock + DynamoDB
append-only audit (21 CFR Part 11). Agent-specific blocks are called out per agent below.

## Per-agent content contract

Each agent object in the generator carries: `hero` (FROM X TO Y), `valueProp`, three `hookStats`,
four `issueBullets`, `costBig` + `costMath` + `costRisks` + `costTag`, a one-line `brightLine`, a
five-step `pipeline` (incl. the red HUMAN GATE and the audit step), the `arch` block
(users / system-of-record / external / runtime / data / 8-step legend), four `proofStats`, six
`deploySteps`, a `deployOneLiner`, and six speaker-note blocks.

| # | Agent | Headline (cited) | Cost of doing nothing | Bright line — AI never decides… |
|---|---|---|---|---|
| 01 | Regulatory Writing & Intelligence | $2.6B per approved drug `[gov/peer-reviewed]` | ~$60M / month delay `[industry-research]` | what gets submitted |
| 02 | Pharmacovigilance — ICSR Intake | ~28M FAERS reports `[gov/peer-reviewed]` | ~$2.0M / yr `[modeled]` | the reportable case |
| 03 | Clinical Trial Ops & TMF | ~$800K/day delay + ~$40K/day `[gov/peer-reviewed]` | ~$25.7M / 30-day slip `[modeled]` | the TMF / query disposition |
| 04 | Site Selection & Patient Matching | ~80% miss enrollment timeline `[sector-press]` | ~$24M / launch `[modeled]` | site selection & patient eligibility |
| 05 | Quality / CAPA & Complaints | CAPA = #1-cited 483 clause `[gov/peer-reviewed]` | $10M–$100M / recall `[industry-research]` | the CAPA disposition / reportability |
| 06 | Clinical Protocol Design | ~57% amended / ~45% avoidable `[industry-research]` | ~$535K / amendment `[industry-research]` | the protocol design |
| 07 | Real-World Evidence / HEOR | ~45% of analyst time on data prep `[sector-press]` | ~$1.3M / yr / team `[modeled]` | the analysis & conclusions |
| 08 | Medical Affairs / MSL Copilot | MLR weeks→months `[sector-press]` | Billions in FCA risk `[gov/peer-reviewed]` | what reaches an HCP |

## Agent-specific AWS blocks (shown on the architecture slide)

- **01** — Bedrock Knowledge Base (approved evidence) + grounding checker; Veeva Vault RIM/DMS connector.
- **02** — PHI masker before the model boundary; Argus/Veeva Safety + MedDRA/WHO Drug; **live Bedrock + real-connector path**.
- **03** — EventBridge-driven continuous TMF/EDC completeness monitoring; Veeva eTMF + CTMS + EDC.
- **04** — gateway-enforced de-identification on RWD; CTMS history; diversity surfaced as a first-class metric.
- **05** — RCA/CAPA drafting + similar-event clustering; TrackWise/Veeva Quality + complaint DB; MDR reportability flag.
- **06** — Bedrock Knowledge Base (guidance) + RWD feasibility linker; RIM + CTMS history.
- **07** — code-system translation (ICD/SNOMED/RxNorm) + lineage tracker; gateway-enforced de-identification; Redshift/Aurora cohort store.
- **08** — off-label content Guardrails (mandatory) + reference annotation; Veeva CRM/DMS; approved-label Knowledge Base.

## Lifecycle-extension agents (09 built, 10 roadmap)

Two agents extend the lifecycle beyond the core-8 land/expand narrative. **09 Manufacturing Batch-Review is built to flagship depth** (LangGraph app + 36 tests + AWS-native rebuild + 4-doc set; `09-manufacturing-batch-review-agent/`). **10 Scientific Intelligence & Target Discovery is roadmap** (Documented — cited deck + design spec). Both produce per-agent decks via the generator's `EXPANSION` array; the executive overview stays at the 8 core-lifecycle agents by design.

| # | Agent | Headline (cited) | Cost of doing nothing | Bright line — AI never decides… | Spec |
|---|---|---|---|---|---|
| 09 | Manufacturing Batch-Review **(built)** | 62% of drug shortages = mfg/quality `[gov]` | ~$420K/yr `[modeled]` | batch release | `09-manufacturing-batch-review-agent/` + `docs/specs/09-…` |
| 10 | Scientific Intelligence & Target Discovery | ~86% of programs fail `[gov/peer-reviewed]` | ~$2.6B/drug `[industry-research]` | the target hypothesis | `docs/specs/10-scientific-intelligence.md` |

New systems: 09 → MES / electronic batch records + LIMS; 10 → ELN + literature/omics/patents. Buyer note: 10 targets research informatics / computational biology, a different buyer than the built eight.

## Discipline rules (applied across all decks)

- The strongest **lead-safe** stats are Tufts day-of-delay (03/04/06), DiMasi $2.6B (01), FDA CAPA-is-top-cited (05), Tufts amendment economics (06), FAERS + Schmider (02).
- **Flag on-slide** as estimates: enrollment-failure %, screen-failure %, 40–85% of PV budget, and all MLR / medical-information figures.
- **Confirmed gaps — never fabricate an ROI:** independent AI ROI benchmarks for patient-matching (04), CAPA/complaints (05), and protocol design (06) are not established; use the labeled modeled math or labeled vendor figures only.
- No standalone Gilead/Moderna gen-AI-on-AWS case study is asserted; named AWS anchors are AstraZeneca / Pfizer / BMS / Sanofi `[vendor]`.
