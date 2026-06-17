# HCLS AI Agent Proof of Concept
### Consulting Offering — Scope, Deliverables, and Engagement Structure

---

## Offering Summary

An eight-to-twelve week, fixed-scope proof of concept that demonstrates one agent from the HCLS AI Agent Suite running end-to-end in a representative use case, with the full platform governance stack in place. The POC produces a working demonstration against the customer's own representative data (or SI-managed demo data if customer data is not yet available), a compliance architecture review, and a go/no-go recommendation for a production pilot.

The POC is the standard entry point for customers who have completed an assessment (or who have a clearly identified priority use case) and want to validate technical feasibility and organizational fit before committing to a full pilot.

---

## Scope

### In scope

**Agent selection (one of the following, customer-determined):**
- Agent 01: Regulatory Writing & Intelligence — benefit-risk section draft or regulatory intelligence monitoring
- Agent 02: Pharmacovigilance — ICSR triage and E2B narrative draft
- Agent 03: Clinical Trial Ops — TMF completeness monitoring and EDC query generation
- Agent 05: Quality / CAPA — complaint triage and CAPA draft

**Platform stack (installed in demo or customer AWS environment):**
- LangGraph agent graph with full workflow (intake → retrieval → draft/analyze → compliance gate → HITL queue → finalize)
- MCP authorization gateway (policy, HITL gate, scoped token model)
- PHI masking layer
- Grounding verification
- Prompt version registry
- Eval harness with customer-reviewed golden test cases
- CloudFormation deployment to customer AWS account (if environment is ready)

**Integration:**
- Fixture connectors (demo mode) — no live system integration required for POC
- Optional: one live read-only connector to the customer's primary system of record (e.g., Veeva Vault RIM document retrieval), if feasible within the timeline

**Governance validation:**
- HITL gate demonstration (human-in-the-loop enforced, not bypassed)
- Grounding report walkthrough with the customer's regulatory, PV, or quality SME
- Prompt change control demonstration (hash-pinned prompt registry, CI failure on drift)

### Out of scope
- Computer-system validation (validation scoping note delivered; customer performs validation)
- Live write-tool connectors (read-only or fixture for POC)
- IdP integration (Cognito federation with customer IdP requires live infrastructure — typically addressed in Pilot)
- Additional agents beyond the single agreed scope
- Penetration testing

---

## Duration and Team

**Typical duration:** 8–12 weeks

**SI team composition:**
- 1 Senior Solution Architect (technical lead)
- 1 Life Sciences Domain Architect (regulatory, PV, or quality — matched to agent)
- 1 AI/ML Engineer (LangGraph, Bedrock, Python)
- 0.5 Security / Compliance Architect
- 0.5 Project Manager

**Customer time commitment:** approximately 40–60 hours, including kickoff, weekly working sessions, SME review of agent output quality, and final demonstration review.

---

## Deliverables

1. **Running POC** — the selected agent executing end-to-end in `EXTRACT_MODE=demo` (no API key required) or against live Bedrock in the customer's AWS account; demonstrated in a live walkthrough with stakeholders
2. **Output quality assessment** — SI and customer SME review of agent output quality (grounding accuracy, draft quality, structural completeness) against agreed success criteria
3. **Platform architecture document** — customer-specific adaptation of the six-layer architecture, AWS service selections, and IdP integration design for the subsequent Pilot
4. **Compliance architecture review** — 21 CFR Part 11 and GxP control mapping for the demonstrated agent; validation scoping note
5. **Eval harness with customer golden test cases** — a minimum of five customer-reviewed golden artifacts for the CI regression harness
6. **POC Findings and Pilot Recommendation Report** — summary of what worked, what requires further development, effort estimate and timeline for the Pilot, and a go/no-go recommendation

---

## Entry Criteria

- Priority agent identified and stakeholder sponsor confirmed
- Customer AWS account available or in procurement (demo mode can proceed without an account; CloudFormation deployment requires one)
- If live Bedrock is in scope: Bedrock access enabled in the target AWS region, model access approved for Claude
- Customer SME available for output quality review (typically 4–6 hours across the engagement)

## Exit Criteria

- POC demonstration accepted by the customer's sponsor and functional stakeholder
- Output quality meets agreed acceptance criteria (defined at kickoff against customer's domain-specific success metrics)
- Pilot scope, timeline, and resourcing agreed

---

## Pricing Approach

Time-and-materials with a not-to-exceed ceiling, or fixed fee for a standardized scope (Agent 01 or Agent 02 with fixture connectors). The not-to-exceed ceiling protects the customer; the T&M structure accommodates the discovery-driven nature of the integration work. Expenses (travel, if applicable) billed separately at cost.

---

## Risk Factors

| Risk | Mitigation |
|---|---|
| Customer system-of-record API not available within POC timeline | POC proceeds with fixture connectors; live integration deferred to Pilot |
| Customer data not available for representative test cases | SI provides domain-representative synthetic cases; customer SME reviews for realism |
| Bedrock model access not approved in time | POC runs in `EXTRACT_MODE=demo`; Bedrock integration demonstrated in Pilot |
| Stakeholder availability for SME review | Pre-book review sessions in week one; protect against scheduling drift |
