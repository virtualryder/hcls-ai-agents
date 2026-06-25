# Cost and ROI Model
### HCLS AI Agent Suite — Illustrative Framework for Business Case Development

> All figures in this document are illustrative ranges intended to guide business-case conversations. They are not guarantees of specific outcomes. Customers should populate the model with their own process metrics and capacity data before presenting to a finance or executive audience.

---

## How to Use This Model

Work left to right through the framework:

1. **Identify the target process** (which agent, which workflow)
2. **Measure the current-state cost** (FTE time, error/rework rate, cycle time)
3. **Estimate the agent-assisted state** (time savings, quality improvement, avoided costs)
4. **Calculate the net benefit** (gross benefit minus platform and engagement costs)
5. **Assess the risk-adjusted payback period**

Each agent's ROI model is independent but they share the platform cost — the marginal cost of each additional agent is significantly lower than the first.

---

## Platform Cost Structure

### One-time costs (per customer deployment)
- **Assessment** (if preceding the POC): fixed-fee engagement (see `offerings/ASSESSMENT-OFFERING.md`)
- **POC**: T&M with NTE ceiling; typically 8–12 weeks of SI professional services
- **Pilot**: T&M with NTE ceiling; typically 12–20 weeks; includes infrastructure provisioning, connector integration, validation package, and UAT support
- **AWS infrastructure setup**: one-time CloudFormation stack deployment; estimated AWS professional services hours if the customer's platform team is not familiar with AgentCore / Bedrock

### Recurring costs (annual, per customer)
- **AWS infrastructure**: Bedrock inference (pay-per-token), DynamoDB, S3, CloudWatch, KMS, Cognito, AgentCore Gateway — cost varies with invocation volume; at moderate use, infrastructure costs for a single agent are in the range of low-to-mid five figures (USD) annually. Scale to nine agents with shared platform adds marginal cost per additional agent.
- **Managed service** (if applicable): recurring monthly SI fee per scope agreed in `offerings/MANAGED-SERVICE-OFFERING.md`
- **Connector maintenance**: ongoing SI support for vendor API changes; can be in-sourced once the customer's engineering team is familiar with the connector interface

---

## Per-Agent ROI Illustrations

### Agent 01 — Regulatory Writing & Intelligence

**Target process:** benefit-risk summary authoring for a marketing application section

| Metric | Current state (illustrative) | Agent-assisted state (illustrative) | Improvement |
|---|---|---|---|
| Time to first complete draft | 20–30 hours (medical writer + regulatory scientist) | 4–8 hours | 70–80% reduction |
| Cross-document consistency findings caught pre-review | Manual, periodic | Automated grounding check on every draft | Consistent coverage |
| Regulatory intelligence monitoring lag | 2–5 business days | Near-real-time | Continuous |
| Revision cycles (due to unsupported claims) | 1–2 per submission section | Reduced by grounding gate | Fewer late-stage rework hours |

**Annual value drivers:**
- Regulatory writing labor reallocation: if a team of eight medical writers spends 35% of time on evidence retrieval and cross-document reconciliation, a 70% reduction in that segment represents approximately 2 FTE-equivalents of reallocation to higher-value work
- Submission cycle compression: if earlier first-draft delivery compresses the review cycle by two to four weeks on a regulatory submission, the revenue-recognition impact (days to market × product revenue per day) can be material for late-stage programs

### Agent 02 — Pharmacovigilance (ICSR Case Intake)

**Target process:** ICSR triage, duplicate detection, MedDRA coding, E2B narrative draft

| Metric | Current state (illustrative) | Agent-assisted state (illustrative) | Improvement |
|---|---|---|---|
| Time per ICSR from intake to Medical Reviewer queue | 4–8 hours | 1–2 hours | 60–75% reduction |
| Duplicate detection rate (manual) | Variable; misses estimated at 5–15% of case volume | Systematic search on every intake | Consistent coverage |
| MedDRA coding errors requiring rework | Manual; dependent on coder experience | Dictionary-validated with confidence scoring | Reduced rework |
| 15-day expedited reporting compliance | At-risk during volume spikes | Volume-elastic without adding headcount | Risk reduction |

**Annual value drivers:**
- PV headcount leverage: triage and drafting automation allows PV processors to focus on case review and exception handling; headcount can remain flat while case volume grows
- Regulatory risk avoidance: a missed 15-day expedited report can result in Warning Letter, consent decree, or product impact; the value of systematic compliance assurance is asymmetric

### Agent 03 — Clinical Trial Ops & TMF

**Target process:** TMF completeness monitoring and EDC query generation

| Metric | Current state (illustrative) | Agent-assisted state (illustrative) | Improvement |
|---|---|---|---|
| TMF completeness review frequency | Monthly or pre-inspection sprint | Continuous | Inspection-ready at all times |
| Time to identify and log a TMF gap | Manual CRA review; days to weeks | Automated; hours | Significant |
| EDC query drafting time (per query) | 30–60 minutes (CRA) | 5–10 minutes with agent draft | 70–85% reduction |
| Pre-inspection TMF remediation cost | High (sprint, external resources) | Reduced (continuous monitoring avoids backlog) | Cost avoidance |

### Agent 05 — Quality / CAPA & Complaints

**Target process:** complaint intake, root-cause investigation, CAPA drafting

| Metric | Current state (illustrative) | Agent-assisted state (illustrative) | Improvement |
|---|---|---|---|
| Time from complaint receipt to investigation summary | 5–10 hours | 1–3 hours | 60–80% reduction |
| CAPA root-cause consistency (across sites) | Variable; dependent on investigator | Similarity-search-assisted; consistent precedent retrieval | Improved |
| CAPA on-time closure rate | Below target (common Form 483 finding) | Improved by earlier investigation start and draft quality | Measurable improvement |

---

## Business Case Template

### Revenue impact (use where applicable)
- Submission cycle compression: `[days compressed] × [product revenue per day at launch]`
- Trial enrollment acceleration (Site Selection / Patient Matching): `[weeks compressed] × [trial operating cost per week]`

### Cost avoidance
- Regulatory action avoidance (PV): estimated cost of a Warning Letter or consent decree (internal legal, remediation, potential product hold); probability-weighted
- Inspection finding avoidance (TMF, CAPA): remediation cost of a Form 483 citation; probability-weighted
- Headcount containment: `[FTE-equivalent hours saved] × [all-in FTE cost]`

### Direct cost reduction
- Labor reallocation: see per-agent illustrations above
- Rework reduction: `[hours of current rework per cycle] × [number of cycles per year] × [hourly cost]`

### Platform cost (net against benefits)
- One-time engagement fees (Assessment + POC + Pilot)
- Annual recurring: AWS infrastructure + managed service (if applicable)

### Payback period
For most engagements, the business case for Agent 01 or Agent 02 reaches payback within twelve to twenty-four months at moderate scale. The platform investment (gateway, audit trail, identity) is shared; the marginal payback period for Agents 03–08 is significantly shorter because the platform cost is already absorbed.

---

## Notes for the Finance Conversation

- Do not present specific ROI numbers without populating the model with the customer's actual process metrics; illustrative ranges are useful for initial qualification but will not survive a CFO review without customer data
- Frame the platform cost as infrastructure investment, not application cost — it serves all nine agents and has a multi-year useful life
- The risk-avoidance benefits (regulatory action, missed 15-day report) are real but asymmetric; a probability-weighted expected-value approach is appropriate, not zero probability
- The model should be reviewed with the customer's finance business partner and the relevant functional head jointly — the functional head provides the process metrics; the finance business partner validates the financial assumptions
