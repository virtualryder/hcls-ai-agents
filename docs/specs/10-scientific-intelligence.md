# Agent 10 — Scientific Intelligence & Target Discovery (spec)

> **Status: roadmap / expansion agent — Documented maturity.** Design + cited business case
> (deck + `gtm/HCLS-DECK-SOURCES.md` §10). Code is a follow-up build per
> `docs/CREATE-A-NEW-AGENT.md`. It extends the suite to the **front of the lifecycle (R&D /
> discovery)**. Note the buyer is different — research informatics / computational biology, not
> the clinical/safety/quality/QA buyer of the built eight — and it is more "evidence synthesis
> with provenance" than "governed decision on a regulated artifact," so position it accordingly.

## Problem
Target evidence is spread across >35M papers (growing >1M/year), omics, patents, and internal
data — no team can synthesize it manually. Poor target validation is a leading cause of the ~86%
clinical failure rate, and the preclinical evidence base is shaky (Amgen reproduced only ~11% of
landmark cancer studies). Discovery-to-candidate runs ~3–6 years and hundreds of millions before
a single patient.

## What the agent does (and the bright line)
The agent retrieves and synthesizes literature, omics, patents, and internal data; extracts and
links claims to their source; and ranks candidate targets on evidence strength and tractability —
with full provenance. **A scientist owns the target hypothesis and the go/no-go decision** — the
agent never decides what to pursue. Provenance-by-design is the answer to the reproducibility pain.

## Governed pipeline
1. **Retrieve evidence** — literature / omics / patents / internal data via gateway + Knowledge Base.
2. **Synthesize & link** — extract claims, link each to its source, de-duplicate.
3. **Rank targets** — score on evidence strength + tractability; surface contradictions.
4. **HUMAN GATE (scientist)** — a named scientist owns the hypothesis and go/no-go.
5. **Append-only audit** — full provenance + decision lineage logged.

## AWS architecture (reuses the shared control plane)
- **Systems of record (new connectors):** ELN (e.g. Benchling), internal data lake; external
  literature (PubMed/Europe PMC), omics, and patent sources. Add connector kinds to `connectors.yaml`.
- **Model layer:** private-connectivity Bedrock + Guardrails; Bedrock Knowledge Base over the approved corpus (RAG).
- **Data tier:** Aurora/Redshift for evidence + ranking state; DynamoDB append-only audit; S3 Object
  Lock for ranked-target rationale; Secrets Manager scoped tokens.
- **Governance:** grounding = every claim links to a source (reproducibility by design); HITL =
  scientist owns the hypothesis; provenance/audit is the differentiator vs. an ungoverned literature bot.
- **IP / confidentiality:** internal data stays in-VPC; the gateway enforces least-privilege on
  internal sources; no internal evidence egresses to the model after masking of confidential identifiers.

## Cited business case (see deck + sources §10)
Headline ~86% of programs entering the clinic fail (Wong/Siah/Lo 2019); ~$2.6B/drug and ~$430M
preclinical (Tufts/PhRMA); 11% preclinical reproducibility (Begley & Ellis); >1M papers/yr (NLM).
Outcome anchors (company-/vendor-reported, never lead): Insilico ~18-month novel-target→candidate;
AstraZeneca ~50% tissue-analysis-time cut on AWS.

## To build (flagship depth)
LangGraph workflow with the scientist gate · ELN + literature/omics/patent gateway tools + a
claim-extraction/provenance linker + ranking · Bedrock Knowledge Base ingestion · 3 deterministic
fixtures · flagship test suite incl. provenance + gate tests · Streamlit dashboard · 4-doc set ·
AWS-native rebuild under `aws-native-reference/10-scientific-intelligence/`. Cited deck already built.
