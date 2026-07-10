# HITL Queue Operations Runbook
### HCLS AI Agent Suite — Human-in-the-Loop Review Queue Management

---

## Purpose

The Human-in-the-Loop (HITL) review queue is the operational heart of the platform's regulated workflow. Every agent graph that reaches a write or finalize node — submitting an ICSR, creating a submission draft, closing a CAPA, submitting for MLR review — suspends at the HITL gate and places an item in the queue for a qualified reviewer to approve, reject, or escalate.

This runbook covers: normal queue operations, monitoring, SLA management, stalled approval handling, queue failure scenarios, and the audit requirements for queue management actions.

---

## Queue Architecture

The HITL queue is implemented as an Amazon DynamoDB table (`hcls-hitl-queue`) with a Step Functions `waitForTaskToken` integration. When an agent workflow reaches the `human_review_gate` node:

1. The workflow writes a queue item to DynamoDB with:
   - `session_id` (partition key)
   - `task_token` (Step Functions callback token)
   - `agent_id` (which agent created the item)
   - `workflow_type` (the specific review type, e.g., `pv_icsr_review`, `regulatory_draft_review`)
   - `payload_summary` (PHI-masked summary of the draft/output requiring review)
   - `grounding_report_ref` (S3 reference to the full grounding report)
   - `compliance_flags` (list of any flags from the compliance gate)
   - `created_at_utc`
   - `sla_deadline_utc` (calculated from the workflow type's SLA)
   - `status` (`PENDING_REVIEW`)
   - `required_role` (the IdP role required to approve, e.g., `PV_MEDICAL_REVIEWER`)

2. The Step Functions execution waits (paused) until the task token is returned with an approval or rejection decision.

3. The reviewer's UI (Streamlit dashboard or embedded Vault panel) queries the DynamoDB table for items matching the reviewer's role, displays the draft and grounding report, and captures the approval decision.

4. On approval, the UI calls the gateway's `submit_approval(session_id, task_token, decision, reviewer_sub, roles, timestamp)` endpoint, which: (a) validates the reviewer's IdP claims, (b) writes the approval record to the append-only audit table, and (c) returns the task token to Step Functions to resume the workflow.

---

## SLA Schedule

| Workflow type | Required reviewer role | SLA from queue entry | Regulatory basis |
|---|---|---|---|
| `pv_icsr_expedited` | `PV_MEDICAL_REVIEWER` | 12 hours | 15-day regulatory clock; 12-hour internal SLA provides buffer |
| `pv_icsr_non_expedited` | `PV_MEDICAL_REVIEWER` | 5 business days | Standard case processing targets |
| `regulatory_draft_review` | `REGULATORY_APPROVER` | 3 business days | Internal RA workflow SLA |
| `capa_draft_review` | `QUALITY_REVIEWER` | 5 business days | QMS SLA per customer SOP |
| `capa_closure_review` | `QUALIFIED_PERSON` | 2 business days | QMS escalation for irreversible action |
| `mlr_review_submission` | `MEDICAL_AFFAIRS_APPROVER` | 3 business days | MLR cycle time target |
| `edc_query_review` | `CLINOPS_LEAD` | 1 business day | EDC query resolution SLA |

SLA deadlines are written to the queue item at creation and are the basis for escalation alarms.

---

## Daily Operations

### Morning queue review (for managed service teams: daily at 08:00 customer local time)

1. Check the CloudWatch HITL Queue dashboard:
   - Items with status `PENDING_REVIEW` and `sla_deadline_utc` within the next 4 hours
   - Items with status `PENDING_REVIEW` and `sla_deadline_utc` in the past (SLA breach)
   - Total queue depth by agent and workflow type

2. For each SLA-at-risk item:
   - Identify the required reviewer role
   - Check whether a reviewer with the required role has been active in the system in the past 24 hours (Cognito last-sign-in check)
   - If no reviewer has been active: escalate to the Functional Escalation Point (see escalation procedure below)

3. Record the daily queue state in the operations log (queue depth by type, items at SLA risk, escalations triggered).

### CloudWatch alarms (must be configured in production)

| Alarm | Threshold | Action |
|---|---|---|
| `HITLQueueDepth-PV-Expedited` | Any item with SLA deadline < 4 hours | Page Platform Operations Lead |
| `HITLQueueDepth-SLABreach` | Any item with SLA deadline in the past | Page Platform Operations Lead AND send email to Functional Escalation Point |
| `HITLQueueDepth-Total` | > 20 items pending | Notify Platform Operations Lead (non-urgent) |
| `HITLApprovalLatency-p95` | > 8 hours for PV expedited type | Alert Platform Operations Lead |

---

## Escalation Procedure

### SLA at risk (4+ hours remaining)

1. Platform Operations Lead sends a queue alert to the Functional Escalation Point:
   - Queue item ID, workflow type, agent, SLA deadline, required reviewer role, payload summary (PHI-masked)
   - Request confirmation that a qualified reviewer will action the item before the deadline
2. Functional Escalation Point confirms reviewer assignment or requests an alternative reviewer be authorized
3. Platform Operations Lead updates the queue item with the `escalated_to` field (reviewer name and timestamp of escalation)

### SLA breached

1. Platform Operations Lead escalates immediately to the Functional Escalation Point AND the Quality / GxP Lead
2. For PV expedited items: also notify the Head of Pharmacovigilance immediately. If the 15-day regulatory deadline is at risk, the Head of PV determines whether the backup manual reporting process must be activated.
3. Document the SLA breach in the incident ticket system. If the breached item covers a GxP-regulated workflow, open a quality deviation ticket in the customer's QMS.
4. Do not abandon or expire queue items to clear the backlog. All queue items must be reviewed by a qualified reviewer or explicitly rejected with a documented rationale.

### Reviewer unavailable (out of office, access issue)

1. Confirm that the reviewer's IdP account is active (Cognito: check user status)
2. If account is active but reviewer is unavailable (OOO): the Functional Escalation Point nominates a backup reviewer with the required role. The backup reviewer must have the IdP role assigned — the gateway will not accept an approval from a user without the required role, regardless of seniority.
3. If account is inactive (access issue): engage IT/IAM team to resolve. Functional Escalation Point nominates a backup reviewer.
4. Do not attempt to assign the task token to a different user outside the standard approval flow — that would bypass the role check and create an invalid audit record.

---

## Queue Failure Scenarios

### Scenario A: DynamoDB write failure (queue item not created)

**Symptoms:** The agent workflow reaches the `human_review_gate` node but no queue item appears in the table; the Step Functions execution is in a `FAILED` state.

**Impact:** The write operation has not occurred. The system is in a safe state (the HITL gate failed closed, not open).

**Recovery:**
1. Check the Step Functions execution history for the failed execution; identify the error in the `human_review_gate` Lambda logs in CloudWatch
2. If the DynamoDB table is healthy (connectivity issue, transient error): re-invoke the agent workflow from the last saved checkpoint state. The workflow will re-attempt the queue write.
3. If the DynamoDB table is unhealthy: follow the DR runbook for DynamoDB recovery before re-invoking.
4. Confirm the queue item is created and visible before closing the recovery.

### Scenario B: Task token expired (Step Functions execution timed out waiting for callback)

**Symptoms:** A reviewer attempts to submit an approval, but the API returns an error indicating the task token is no longer valid; the Step Functions execution has timed out.

**Impact:** The workflow must be restarted. The approved draft must be re-created. The previous draft and its grounding report are in the audit trail but the approval action was not recorded for a valid workflow execution.

**Recovery:**
1. Notify the reviewer that their approval could not be recorded due to a timeout and that they will need to re-review the draft.
2. Update the queue item status to `EXPIRED` (do not delete).
3. Re-invoke the agent workflow to regenerate the draft. The new workflow will create a new Step Functions execution and a new queue item.
4. If the workflow was for a PV expedited case: immediately notify the Head of Pharmacovigilance and check whether the regulatory deadline is at risk.
5. Document the timeout in the incident log. Review the Step Functions timeout configuration — the human gate is bounded by the task state's **`TimeoutSeconds`** (e.g. 14 days / `1209600` for the PV Medical Reviewer gate on Agent 02), which should be set to the longest plausible review time for the workflow type. Do **not** re-introduce a `HeartbeatSeconds` on the `waitForTaskToken` gate: nothing in the workflow calls `SendTaskHeartbeat`, so a heartbeat would expire the gate in roughly an hour regardless of the `TimeoutSeconds` value. On timeout the execution routes to the terminal `PipelineFailed` state (the gate fails closed; nothing finalizes without an approval).

### Scenario C: Queue item in PENDING_REVIEW but no active Step Functions execution

**Symptoms:** Queue monitoring shows a pending item but there is no corresponding active Step Functions execution with a matching task token.

**Impact:** Approving this item would fail (the task token is from a completed or failed execution). The item is orphaned.

**Recovery:**
1. Do not approve or reject the orphaned item — approving it will produce an error and a confusing audit trail.
2. Update the orphaned item status to `ORPHANED` with a note explaining the condition.
3. Investigate the Step Functions execution that created the token: did it fail? Was it stopped manually? Was there a duplicate invocation?
4. If the underlying workflow was meaningful (an active ICSR case or submission), re-invoke the workflow to create a fresh queue item with a valid task token.
5. Report the orphaned item to the Quality / GxP Lead if it was associated with a regulated output.

---

## Audit Requirements for Queue Operations

All queue management actions — status updates, escalations, re-invocations, expiries, orphan handling — must be recorded in the queue item's `operations_log` field and in a corresponding entry in the incident log system. Queue management actions taken by operations staff are not the same as reviewer approvals; they must not be confused with or recorded as reviewer decisions.

Operations staff do not have the authority to approve queue items on behalf of reviewers. If an operations action is misinterpreted as an approval (e.g., a `PUT` to the queue table that inadvertently sets the `status` field to `APPROVED`), this constitutes a data-integrity event and must be reported to the Quality / GxP Lead immediately.

The DynamoDB append-only policy (IAM `Deny` on `UpdateItem`/`DeleteItem` for the audit partition) protects the audit table but does not prevent updates to the HITL queue table (which uses a different partition). Operations teams have update access to the queue table for operational management; this access must be used carefully and every update must be logged in the operations log.
