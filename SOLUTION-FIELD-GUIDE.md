# Solution Field Guide
### HCLS AI Agent Suite — SI Sales & Solution Architect Reference

> **Internal use only. Not for distribution to customers or prospects without SI review.**

This guide equips sales executives, account teams, and solution architects with the qualification criteria, discovery questions, adoption roadmap, and per-agent positioning needed to open, shape, and win an HCLS AI Agent Suite engagement.

---

## 1. Who This Is For

The suite is designed for **mid-to-large pharmaceutical, biotech, medtech, and CRO organizations** that:

- Have an existing AWS footprint or an active cloud migration underway
- Are under pressure to accelerate regulatory timelines, contain pharmacovigilance costs, or improve inspection readiness
- Have a CISO or compliance function that will not approve a generic AI tool without data-residency guarantees, PHI masking, and an auditable authorization layer
- Have qualified AI skeptics in Regulatory Affairs, Quality, or Drug Safety who will ask hard questions about hallucination, validation, and autonomy

The primary **economic buyer** is typically the CTO, CIO, or CDO. The primary **technical authority** is the platform or data engineering lead. The primary **functional champion** is the Head of Regulatory Affairs, Head of Clinical Operations, VP of Quality, or Head of PV/Drug Safety. Security and privacy sign-off comes from the CISO and Chief Privacy Officer/DPO.

---

## 2. Qualification Framework

Run these questions in discovery. A "yes" on three or more signals a real opportunity.

### Business pressure
- Is your regulatory affairs team spending more than 30% of writer time on evidence retrieval, cross-document reconciliation, or guidance search — rather than authoring and strategy?
- Has PV case volume grown faster than headcount in the last 18 months? Are you at risk of missing 15-day expedited reporting windows?
- Have you received an FDA Form 483 or a Warning Letter in the last three years citing data-integrity, CAPA, or TMF completeness issues?
- Are you launching a new compound or indication in the next 18 months where submission quality and speed materially affect time-to-market?

### Platform readiness
- Do you have AWS as a primary or secondary cloud? Can inference run in-account (Bedrock) rather than calling an external API?
- Is there an enterprise IdP (Okta, Entra, Ping) with role-based groups that map to functional roles (Regulatory Approver, PV Medical Reviewer, Qualified Person)?
- Are your core systems of record (Veeva Vault RIM, Argus Safety, Medidata, TrackWise) accessible via API, or is integration largely manual/FTP?

### AI readiness
- Has the organization already deployed AI-assisted tooling (Copilot, generative search) in non-regulated functions? Is there executive appetite to extend to regulated workflows?
- Does the risk management function (legal/compliance) have a framework for accepting AI recommendations in clinical and regulatory contexts, or is that the first conversation to be had?

### Disqualifiers
- The customer is not willing to perform computer-system validation for the intended use of a regulated AI tool (non-negotiable for GxP functions)
- The customer insists on no human review gate ("the AI should just submit it") — this is a misalignment with FDA/EMA good-AI principles and a program risk
- There is no executive sponsor with authority over both IT and the functional department

---

## 3. The Six-Step Adoption Path

Regulate the autonomy level to match organizational trust, not just technical capability. The framework below maps to the FDA/EMA Joint Good-AI Principles (January 2026) framing of credibility controls proportional to risk.

| Step | Autonomy level | What the agent does | Human role | Typical entry point |
|---|---|---|---|---|
| **1 — Search & Summarize** | Monitor, retrieve, surface | Regulatory intelligence monitoring; TMF completeness gap lists; complaint trend summaries | Reviews output; no action taken without human decision | Day-one; zero integration required |
| **2 — Recommend** | Analyze, rank, advise | Site feasibility scoring; duplicate ICSR detection; CAPA root-cause similarity; protocol feasibility heat map | Reviews ranked options; selects and acts | After step 1 demonstrates value |
| **3 — Draft** | Generate regulated content | Submission section drafts (grounded to evidence); ICSR E2B narratives; CAPA investigation summaries | Reviews draft, grounding report, compliance flags; approves or rejects | Core pilot scope |
| **4 — Task after approval** | Act on confirmed instruction | Create submission draft in RIM (after human approves); write ICSR case to Safety DB (after Medical Reviewer approves); open CAPA (after QP approves) | Approves before any write; gateway enforces the gate | Pilot exit; production entry |
| **5 — Reversible low-risk action** | Act with post-hoc review | EDC query creation; HCP briefing document routing to MLR; non-PII cohort queries | Reviews exception queue; corrects reversible errors | Mature production |
| **6 — Higher autonomy** | Multi-step autonomous | Full ICSR triage-to-case (with periodic Reviewer sampling); continuous TMF monitoring with auto-escalation | Oversight and escalation; not step-by-step approval | Post-validation, specific low-risk sub-tasks only |

**Guidance for SAs:** Propose Step 1–3 for the initial pilot. Step 4 is the first production milestone. Steps 5–6 require customer-side change control and, in most cases, additional CSV scope. Do not over-promise autonomy in initial positioning — it is the single most common reason a regulated AI engagement stalls at a customer's quality function.

---

## 4. Per-Agent Pitch One-Liners

Use these in executive conversations to establish relevance before going deep.

| Agent | One-liner |
|---|---|
| **01 Regulatory Writing & Intelligence** | "Cut time-to-first-draft of a benefit-risk summary from three days to four hours — with every claim grounded and traceable before a human sees it." |
| **02 Pharmacovigilance — ICSR Case Intake** | "Process ten times the adverse-event volume without adding headcount, and catch duplicates and MedDRA coding gaps before the 15-day clock expires." |
| **03 Clinical Trial Ops & TMF** | "Turn TMF completeness from a pre-inspection sprint into a continuous live view — with EDC queries drafted and routed in minutes rather than days." |
| **04 Site Selection & Patient Matching** | "Replace feasibility surveys with a data-driven site-performance and cohort-size model that accounts for real patient demographics, not optimistic site estimates." |
| **05 Quality / CAPA & Complaints** | "Close CAPAs faster, with consistent root-cause language and a similarity engine that surfaces precedent before every investigation starts." |
| **06 Clinical Protocol Design & Feasibility** | "Reduce first-draft protocol cycles by linking historical guidance, precedent study designs, and real-world feasibility data in a single authoring session." |
| **07 Real-World Evidence / HEOR** | "Let your epidemiologists spend time on methods, not on translating clinical criteria into database code — and ground every cohort definition in the source data before the analysis runs." |
| **08 Medical Affairs / MSL Copilot** | "Give your field medical team an on-label, evidence-grounded response to any HCP question in seconds — with a technical off-label guardrail and MLR routing built in." |

---

## 5. Deployment Pattern Selection

Not every agent belongs on every deployment topology. Use this matrix to shape the architecture conversation.

| Pattern | Description | Best for |
|---|---|---|
| **In-account AWS (Bedrock)** | All inference and storage runs inside the customer's AWS account. No PHI or model context leaves their VPC. | Any function involving identified PHI, HIPAA data, or confidential submission content. Default recommendation for regulatory, PV, and clinical functions. |
| **SaaS/shared infrastructure** | Shared compute; per-customer logical isolation; customer-managed KMS keys. | HEOR/RWE with de-identified data; Medical Affairs briefing retrieval with no PHI. Requires careful TPRM review and CPO sign-off. |
| **Hybrid (edge + cloud)** | Local cache of reference data (guidance, MedDRA, coding dictionaries) with cloud inference. | Field Medical (MSL Copilot) where offline resilience matters; site-selection analysis with sensitive feasibility data. |
| **Air-gapped / private cloud** | Fully on-premises or isolated VPC; Bedrock not available. | Defense/government biotech; maximum-classification environments. Requires model download approval. |

Agents 01, 02, 03, 05 should default to **in-account AWS**. Agents 04, 06 can be hybrid. Agent 07 can be SaaS with de-identified data contractually guaranteed. Agent 08 is typically hybrid (cloud inference, local HCP record cache).

---

## 6. Context of Use and Risk Framing (FDA/EMA Good-AI Principles)

The FDA/EMA Joint Statement on Good Machine Learning Practices (January 2026) introduces a "context of use + credibility controls proportional to risk" framework. Use this with Regulatory Affairs and Quality stakeholders to frame why the platform design is the right approach.

> **Positioning the MCP layer:** for the plain-English "why do agents need a governed access layer, and why fund it first" conversation — with a 60-second talk track and objection handling — use `docs/WHY-THE-MCP-LAYER.md`. It's written for a new account person to deliver to a customer.

| Context of use dimension | How to frame it | How the platform addresses it |
|---|---|---|
| **What decision does the AI inform?** | Is it a search/summarize (low risk) or a submission/report (high risk)? | The six-step adoption path calibrates autonomy to the risk level; write tools require human approval regardless of step |
| **Who is accountable?** | A qualified human is always named and the decision is attributed to them, not the AI | The HITL gate binds reviewer identity (IdP sub, roles, timestamp) to every approval; the audit trail is immutable |
| **What are the failure modes?** | Hallucinated dose/endpoint (grounding controls it); incorrect MedDRA code (checked against dictionary); off-label claim (Guardrails + prohibited-language gate) | Grounding verification, structural eval harness, Bedrock Guardrails, prohibited-language checks — all pre-human-review |
| **How is performance monitored?** | The model is part of the regulated system; prompt changes require change control | Prompt version registry, hash-pinning, CI eval regression |
| **What is the scope boundary?** | The agent does exactly one job; a PV agent cannot touch RIM; a Medical Affairs agent cannot write case reports | Agent-level tool grants in policy.py enforce job-description-as-code at the gateway |

---

## 7. Competitive Quick Reference

**vs. build-it-yourself:** Internal AI teams underestimate the compliance scaffolding — PHI masking, audit trails, HITL gates, grounding verification, prompt change control — by a factor of three to five. This is the platform work; the agent logic itself is the smaller part. The accelerator buys six to twelve months of compliance engineering.

**vs. point-tool vendors (Veeva Vault AI, etc.):** Vendor-embedded AI is locked to one system of record. This suite integrates across the full data estate (RIM + Safety + EDC + CTMS + QMS + RWD + CRM) under one governance model. The SI owns the integration layer; the customer is not locked to a single vendor's AI roadmap.

**vs. general-purpose AI platforms (Microsoft Copilot for Healthcare, Google Cloud Healthcare AI):** General platforms offer horizontal capability; this suite offers vertical domain controls (GVP/E2B structural checks, 21 CFR Part 11 e-signature linkage, MedDRA coding enforcement, CAPA root-cause similarity, protocol feasibility grounding). The difference surfaces in the first compliance review.

See `offerings/COMPETITIVE-POSITIONING.md` for the full competitive narrative.

---

## 8. Common Objections and Rapid Responses

| Objection | Response |
|---|---|
| "AI hallucinates — we can't use it in regulated submissions" | "You're right to start there. The grounding verification layer ensures every number and claim in a regulated draft is traceable to its source document before a human sees it. A hallucinated dose doesn't survive the grounding check. That's by design." |
| "We'll need to validate this under GxP / 21 CFR Part 11 before we can use it in production" | "Correct — and the platform is designed to be validated. The control structure (audit trail, e-signature linkage, version-pinned prompts, human gate) maps directly to the CSV/CSA requirements. We provide the control design; your validation team operationalizes it." |
| "Our data can't leave our environment" | "It never touches the public internet or an external AI API. Inference runs on HIPAA-eligible Amazon Bedrock — a regional AWS service your VPC reaches only over AWS PrivateLink, under your AWS BAA. The MCP gateway short-circuits any path from agent to external API." |
| "We'd rather build this ourselves" | "You can. And you'd spend the first six months building the compliance scaffolding — PHI masking, audit trails, deny-by-default authorization, HITL gates — before writing a single line of domain logic. That's exactly what this accelerator gives you, so your engineering team can focus on your data integrations and workflow customization." |
| "We're not comfortable with autonomous AI in regulated workflows" | "We're not proposing autonomous AI in regulated workflows. The platform enforces a human approval gate at every consequential action — submission creation, ICSR filing, CAPA closure. The AI drafts and checks; your qualified professionals decide." |

See `offerings/OBJECTION-HANDLING.md` for extended responses.

---

## 9. Engagement Entry Points

| Entry point | Recommended starting agent | Typical duration | Success metric |
|---|---|---|---|
| Regulatory submissions backlog or NDA/MAA in flight | 01 Regulatory Writing | 8–12 week POC | Time-to-first-draft reduction; grounding accuracy vs. baseline |
| PV case volume spike / resourcing constraint | 02 Pharmacovigilance | 8–12 week POC | Triage time per case; duplicate detection rate |
| TMF inspection readiness / audit finding | 03 Clinical Trial Ops | 6–10 week POC | TMF gap coverage; query turnaround time |
| CAPA on-time closure rate / Form 483 finding | 05 Quality / CAPA | 6–10 week POC | CAPA closure rate improvement; root-cause consistency |
| Platform / AI strategy engagement | Full 8-agent architecture review | 4–6 week assessment | Architecture blueprint + prioritized roadmap |

---

## 10. Field Collateral & Live Proof

What you can put in front of a customer today:

- **All nine agents are built to flagship depth** and run end-to-end with no API key (`EXTRACT_MODE=demo`) — useful for live working sessions before any AWS account exists.
- **Live proof point:** Agent 02 (Pharmacovigilance) runs on **real Amazon Bedrock inference + a real HTTP safety connector** end-to-end (`02-pharmacovigilance-agent/demo/demo_live.py`; runbook in `demo/DEMO-LIVE.md`). Swap one URL to the customer's Argus/Veeva gateway. This is the demo that answers "does it actually work against our systems?"
- **Decks & leave-behinds (repo root):** `HCLS-Agentic-AI-Suite-Executive-Overview.pptx` (16-slide enablement deck), `HCLS-Customer-Teaser-5slide.pptx` (customer teaser), `HCLS-One-Pager.pdf` (one-page leave-behind).
- **Proof of rigor:** 503 automated tests pass across platform, governance, agents, and AWS-native rebuilds — cite this when Quality or Security asks "how do we know it behaves?"

---

*For offering scopes, pricing structures, and delivery methodology, see `offerings/` directory. For security and compliance positioning by stakeholder, see `docs/STAKEHOLDER-SECURITY-BRIEFINGS.md`.*
