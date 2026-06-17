# Operational Runbooks
### HCLS AI Agent Suite — Operations Reference

---

## Purpose

These runbooks govern the day-to-day and incident-driven operations of the HCLS AI Agent Suite in production. They are written for the operations team responsible for the deployed platform — whether that is the SI's managed service team, the customer's internal IT operations team, or a hybrid. They are not tutorials; they assume familiarity with the platform architecture described in `docs/SUITE-ARCHITECTURE.md`.

In a regulated life-sciences environment, operations procedures have compliance implications: a mishandled incident can affect the integrity of the audit trail, the completeness of a regulatory record, or the safety of patients and subjects. These runbooks are therefore written with life-sciences operational obligations in mind, not only with IT operations best practices.

---

## Runbook Index

| Runbook | Purpose | Trigger |
|---|---|---|
| `INCIDENT-RESPONSE.md` | Detect, contain, investigate, and recover from security, data-integrity, and service incidents | Alert, user report, automated detection |
| `DR-RUNBOOK.md` | Recover the platform from regional failure, data loss, or catastrophic infrastructure event | DR trigger, RTO/RPO breach |
| `HITL-QUEUE-OPERATIONS.md` | Manage the human-in-the-loop review queue: monitor depth, escalate stalled approvals, handle queue failures | Daily operations, SLA breach |
| `MODEL-DEGRADATION-RESPONSE.md` | Detect and respond to LLM performance degradation, grounding regression, or prompt drift | Eval harness regression, anomaly alert |

---

## Roles Referenced in These Runbooks

| Role | Description |
|---|---|
| **Platform Operations Lead** | SI or customer IT: primary on-call for platform incidents; owns incident ticket; coordinates with functional and security teams |
| **Security Operations Engineer** | SI or customer CISO function: leads security incident response; determines data exposure scope |
| **Life Sciences Domain Advisor** | SI domain SME: assesses functional impact of incidents (which regulated outputs were affected; which studies/products/jurisdictions are in scope) |
| **Functional Escalation Point** | Customer-side: Head of PV, Head of Regulatory Affairs, Head of Quality, or Head of Clinical Operations — the person who must be notified if a regulated output is suspected to have been affected |
| **Quality / GxP Lead** | Customer-side: owns the regulated-system incident handling process; determines whether a deviation report or CAPA is required |
| **CISO / CPO** | Customer-side: notified for data-security incidents; holds the decision on regulatory notification |

---

## Key Operational Concepts

### The audit trail is primary
In a production incident, the audit trail in DynamoDB is the most important record. It is append-only and cannot be modified. Operations actions must not attempt to modify or delete audit records — doing so would constitute a GxP data-integrity violation.

### Preserve before you act
For any incident that may have affected the integrity of regulated outputs, preserve the state before taking remediation actions. This means: snapshot the DynamoDB table, export relevant CloudTrail logs to S3, and document the platform state at the time of detection before making configuration or code changes.

### Human approval records are binding
The HITL approval records in the review queue are electronic signatures under 21 CFR Part 11. If a system error creates a spurious approval record, that record must be documented and challenged through the customer's deviation process — not silently deleted. Contact the Quality / GxP Lead before modifying any approval record.

### Scoped escalation
Not every incident requires the same escalation path. A platform availability incident that does not affect the integrity of regulatory outputs escalates to IT Operations and the Platform Operations Lead. An incident that may have affected a regulated output (draft, ICSR case, CAPA record) additionally escalates to the Functional Escalation Point and the Quality / GxP Lead within the timeframe defined in the customer's quality management system.

---

## SLA Reference

| Priority | Definition | Initial response | Functional escalation |
|---|---|---|---|
| P1 | Production outage or confirmed data-integrity risk | 30 minutes (24/7) | Immediately on confirmation |
| P2 | Degraded function, no data-integrity risk | 2 hours (business hours) | Within 4 hours |
| P3 | Non-urgent operational issue | Next business day | As applicable |

---

## Regulated Incident Determination

Before closing any incident, the Platform Operations Lead must answer the following questions. If the answer to any question is "yes" or "unknown," the incident must be escalated to the Functional Escalation Point and the Quality / GxP Lead.

1. Did the incident affect the availability, integrity, or confidentiality of any regulated output (submission draft, ICSR case, CAPA record, clinical query)?
2. Did the incident affect the completeness or accuracy of the audit trail for any regulated workflow session?
3. Did the incident expose PHI or PII to unauthorized parties?
4. Did the incident affect the operation of the HITL gate for any workflow that was active during the incident window?
5. Were any write tools (high-risk tools) invoked during the incident window in a way that may have bypassed the authorization model?

If all answers are "no," the incident is classified as an IT operations incident and closed through the standard IT incident management process. If any answer is "yes" or "unknown," the incident must also be documented in the customer's regulated-system deviation process.
