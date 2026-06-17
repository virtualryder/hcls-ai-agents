# Incident Response Runbook
### HCLS AI Agent Suite — Detection, Triage, Containment, and Recovery

---

## Scope

This runbook covers security incidents, data-integrity incidents, and service incidents affecting the HCLS AI Agent Suite in production. It applies to SI managed service operations and should be adopted (or adapted) by any customer IT operations team managing the platform independently.

---

## Phase 1 — Detection

### Detection sources

| Source | Mechanism | First responder |
|---|---|---|
| CloudWatch alarm | HITL queue depth spike, error rate threshold, Guardrail trigger rate anomaly, DynamoDB write capacity alarm | Platform Operations Lead (paged via on-call rotation) |
| CloudTrail alert | Unauthorized IAM action, KMS key usage anomaly, cross-account access attempt | Security Operations Engineer |
| User report | Functional user reports unexpected agent behavior, wrong output, missing HITL gate, or data not matching system of record | Platform Operations Lead via support ticket |
| Bedrock alarm | Model invocation failure rate spike, Guardrail PHI detection rate anomaly | Platform Operations Lead |
| Automated governance check | CI eval harness regression (if integrated into production monitoring); grounding accuracy drop | Life Sciences Domain Advisor + Platform Operations Lead |

### Initial detection record

Upon receiving an alert or report, the Platform Operations Lead opens an incident ticket immediately with:
- Timestamp of detection (UTC)
- Detection source
- Initial symptom description
- Affected agent(s) (01 through 08, or "platform" if cross-agent)
- Preliminary priority assessment (P1/P2/P3)

---

## Phase 2 — Triage

### Triage questions (answer within 30 minutes for P1, 2 hours for P2)

**Service impact:**
- Is the agent or platform returning errors? If so, which operations (read tools, write tools, HITL gate, audit)?
- Are functional users blocked from completing regulated workflows?
- Is the HITL queue processing normally?

**Data integrity:**
- Were any write-tool calls (high-risk tools) attempted or completed during the incident window?
  - Check DynamoDB audit table: `SELECT * FROM audit WHERE timestamp BETWEEN [incident_start] AND [detection_time] AND decision IN ('ALLOW') AND tool IN [HIGH_RISK_TOOLS]`
- Are the audit records for the incident window complete and consistent?
- Did any workflow reach the finalize node during the incident window without a corresponding HITL approval record?

**Security:**
- Is there evidence of unauthorized access (CloudTrail: unauthorized IAM actions, unexpected Cognito sign-ins, KMS decrypt calls from unexpected principals)?
- Is there evidence of PHI egress (Bedrock Guardrail PHI detections above baseline; S3 access from unexpected principals; VPC flow logs showing outbound traffic to unexpected destinations)?
- Is there evidence of prompt injection (Guardrail topic-filter blocks on unusual topics; grounding check failures on inputs that should not contain external instructions)?

**Life-sciences scope determination:**
- Which regulated workflows were active during the incident window? (check DynamoDB session records)
- Which studies, products, or jurisdictions are associated with those workflows?
  - Agent 01: which submissions or regulatory products were in scope?
  - Agent 02: which ICSR cases were being processed? Which products? Which reporting jurisdictions?
  - Agent 03: which studies? Which sites? Which TMF sections?
  - Agent 05: which QMS records were in the CAPA workflow? Which products? Which facilities?
- Were any outputs from the incident window used to take a regulatory action (submission filed, ICSR submitted, CAPA closed)?

### Priority determination

| Condition | Priority |
|---|---|
| PHI potentially exposed to unauthorized parties | P1 |
| Audit trail integrity uncertain (missing records, unexpected records) | P1 |
| HITL gate may have been bypassed for a write operation | P1 |
| Production outage — agents not responding | P1 |
| Write operations succeeded but correctness of the authorization is uncertain | P1 |
| Bedrock inference errors — agents functional for reads, not writes | P2 |
| HITL queue processing slowly (approval latency high but gate not bypassed) | P2 |
| Grounding accuracy degraded (eval harness regression, no production write affected) | P2 |
| Connector error — specific system of record unavailable, reads failing | P2 |
| Non-blocking operational anomaly | P3 |

---

## Phase 3 — Containment

### For P1 incidents

**Step 1: Preserve the state**

Before any remediation action:
```bash
# Export audit table records for the incident window to S3
aws dynamodb export-table-to-point-in-time \
  --table-arn arn:aws:dynamodb:[region]:[account]:table/hcls-audit \
  --s3-bucket [incident-evidence-bucket] \
  --s3-prefix incidents/[incident-id]/audit-export/ \
  --export-time [detection-time-iso8601]

# Export relevant CloudTrail events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=bedrock.amazonaws.com \
  --start-time [incident-start] \
  --end-time [detection-time] \
  > /tmp/cloudtrail-bedrock-[incident-id].json

aws s3 cp /tmp/cloudtrail-bedrock-[incident-id].json \
  s3://[incident-evidence-bucket]/incidents/[incident-id]/cloudtrail/
```

**Step 2: Contain the risk**

If PHI exposure is suspected:
- Disable the affected agent's IAM role (remove the `sts:AssumeRole` permission from the Lambda or ECS task principal) — this stops new invocations without affecting the audit trail
- Do not delete any logs, records, or S3 objects
- Notify the Security Operations Engineer and CISO immediately

If HITL gate bypass is suspected:
- Disable the Step Functions state machine or AgentCore Runtime endpoint for the affected agent
- Review the HITL approval queue table for the incident window: confirm that all finalize-node executions have a corresponding valid approval record

If unauthorized IAM access is suspected:
- Revoke the suspicious session tokens via STS
- Review and, if necessary, rotate the affected KMS key (will not affect already-encrypted records; will prevent new encryption/decryption with the compromised key)
- Engage the Security Operations Engineer for credential rotation scope assessment

**Step 3: Escalate**

Immediately escalate to:
- Functional Escalation Point (Head of PV, Regulatory Affairs, Quality, or ClinOps — per the affected agent)
- Quality / GxP Lead (for any incident where a regulated output or audit trail may be affected)
- CISO / CPO (for any security or PHI incident)
- Legal / Compliance (for any incident that may trigger regulatory notification obligations)

Provide the escalation notification with:
- Incident timestamp (detection UTC)
- Affected agent(s) and preliminary scope (studies, products, jurisdictions)
- Nature of the incident (service, data-integrity, security)
- Containment actions taken
- Current status

---

## Phase 4 — Investigation

### Root cause investigation

The investigation must address:

1. **What failed?** (service component, authorization logic, connector, model, audit layer)
2. **When did it start?** (earliest CloudTrail/CloudWatch evidence; not just when it was detected)
3. **What was the blast radius?** (which sessions, which tools, which workflow steps were affected)
4. **Were any regulated outputs affected?** (complete the life-sciences scope determination from triage)
5. **Was the audit trail complete for the incident window?** (cross-check session IDs in the workflow execution log against audit table records)
6. **Was the HITL gate functioning for all finalize operations during the incident window?**
7. **Is there evidence of malicious intent, or is this an operational failure?**

### Life-sciences scope investigation (detailed)

For any regulated output that was active during the incident window:

**Agent 02 (PV):** Query the safety database to determine if any ICSR cases were submitted during the window. Identify the case IDs, products, reporting countries, and Medical Reviewer identities. Determine whether the cases are in a completed or pending state. Notify the Head of Pharmacovigilance of the specific cases so they can assess whether the Medical Reviewer's approval was made with complete information.

**Agent 01 (Regulatory Writing):** Identify any submission drafts created in RIM during the window. Determine whether those drafts have been forwarded to a health authority. If so, notify the Head of Regulatory Affairs and the regulatory submission team immediately.

**Agent 05 (Quality):** Identify any CAPAs closed during the window. Notify the Head of Quality / Qualified Person. Determine whether the closure should be suspended or reviewed under the deviation process.

**Agent 03 (Clinical Trial Ops):** Identify any EDC queries created during the window. Determine whether any queries affected subject data at a site. Notify the Head of Clinical Operations and the relevant study team.

---

## Phase 5 — Recovery

### Service restoration

1. Verify the root cause is resolved or mitigated before restoring service
2. For stopped agents: re-enable the IAM role or state machine only after the Security Operations Engineer confirms the threat is contained
3. Perform a targeted test of the restored agent in a staging environment before enabling production traffic
4. Monitor CloudWatch metrics and DynamoDB audit records for 30 minutes post-restoration before declaring recovery complete

### Audit trail integrity restoration

If audit records are missing for a session that completed during the incident window:
- Reconstruct the audit record from CloudTrail API logs and CloudWatch execution logs
- Document the reconstruction in the incident ticket with a timestamped note
- Submit a deviation report in the customer's QMS if the reconstruction is required for a GxP-covered session
- Do not write fabricated audit records to the append-only table

### Data-integrity remediation

If a regulated output was affected and may have reached a downstream system of record:
- The Quality / GxP Lead and Functional Escalation Point determine the appropriate regulatory action
- The SI provides technical evidence (audit export, CloudTrail, incident timeline) to support the regulated investigation
- If a regulatory notification is required (e.g., ICSR correction, submission retraction), the customer's regulatory function owns that action; the SI provides technical support

---

## Phase 6 — Post-Incident Review

### PIR requirements

Every P1 incident and every incident affecting a regulated output requires a post-incident review (PIR) within five business days of recovery. The PIR documents:

1. Incident timeline (detection → containment → recovery, with UTC timestamps)
2. Root cause (technical and, if applicable, process)
3. Life-sciences scope (regulated outputs affected; studies/products/jurisdictions)
4. Actions taken
5. Corrective and preventive actions (CAPA) — including platform changes, runbook updates, alarm tuning, and process improvements
6. Whether a formal QMS deviation record is required (Quality / GxP Lead decision)
7. Whether regulatory notification was made or assessed and determined not required (Functional Escalation Point decision)

The PIR is submitted to: Platform Operations Lead, Customer Designated Contact, Quality / GxP Lead, and CISO (for security incidents). It is retained in the incident management system and referenced in the customer's regulated-system change-control process if platform changes are implemented.
