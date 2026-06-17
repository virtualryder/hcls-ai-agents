# Disaster Recovery Runbook
### HCLS AI Agent Suite — Regional Failure, Data Loss, and Catastrophic Recovery

---

## Scope and Objectives

This runbook covers recovery from events that impair the HCLS AI Agent Suite beyond normal incident response — regional AWS failure, catastrophic data loss, KMS key compromise, or infrastructure-level corruption. It defines the recovery time objective (RTO) and recovery point objective (RPO) targets, the recovery procedures, and the life-sciences obligations that apply during and after a DR event.

---

## RTO and RPO Targets

| Service tier | RTO (service restoration) | RPO (data loss tolerance) | Notes |
|---|---|---|---|
| Audit trail | 4 hours | Near-zero (DynamoDB PITR; S3 Object Lock snapshots) | Audit integrity is the highest priority; restore before resuming production agent operations |
| HITL queue | 4 hours | Near-zero (DynamoDB PITR) | Pending approvals must be preserved; no approvals can be lost |
| Agent workflow execution | 8 hours | 15 minutes (Step Functions execution state; last successful state is recoverable) | Agents may be re-invoked from the last known state |
| Bedrock inference | Dependent on AWS regional status | N/A (stateless) | No customer data; Bedrock recovers with the region |
| Connector integration | 24 hours | N/A (connectors are stateless adapters) | Live connector access resumes when the vendor system and network are restored |

These targets assume a single-region failure. Multi-region active-active is outside the standard deployment scope; if the customer requires multi-region DR, it requires a separate architecture engagement.

---

## DR Trigger Criteria

Escalate to this runbook when:

- The primary AWS region is confirmed unavailable by AWS Health Dashboard for more than two hours
- DynamoDB table recovery is required (data deletion, corruption, or table-level failure)
- KMS key compromise is confirmed and key rotation/replacement is required
- CloudFormation stack is in a DELETE_FAILED, ROLLBACK_FAILED, or unrecoverable state and cannot be repaired through standard incident response
- Two or more P1 platform components fail simultaneously in a pattern inconsistent with a normal service incident

---

## Pre-DR Requirements (Must Be in Place Before Production Go-Live)

### Data protection

- **DynamoDB Point-in-Time Recovery (PITR):** PITR must be enabled on the audit table, HITL queue table, and session state table. Verify in the AWS console: DynamoDB > Tables > [table-name] > Backups > Point-in-time recovery: Enabled.
- **S3 Object Lock:** The WORM document bucket must have Object Lock enabled in COMPLIANCE mode with a retention period appropriate to the regulatory jurisdiction's record-retention requirements (minimum seven years for most HIPAA and GxP contexts).
- **S3 Cross-Region Replication (CRR):** The document bucket should be replicated to a secondary region for disaster recovery. CRR is configured in the `data.yaml` CloudFormation template with the `DRRegion` parameter.
- **CloudFormation stack templates staged in S3:** All CloudFormation templates must be stored in a versioned S3 bucket in both the primary and DR regions, so the stack can be redeployed without internet access to the source repository.

### Infrastructure documentation

Maintain a current record of:
- Stack name and account ID for all deployed CloudFormation stacks
- KMS key ARNs (primary and, if applicable, DR region)
- DynamoDB table ARNs and PITR windows
- S3 bucket names for WORM store, CRR destination, and CFN template bucket
- Cognito User Pool ID and IdP federation endpoint URL
- AgentCore Gateway ID and registered target ARNs
- ECR repository URIs for container images (if using AgentCore Runtime)

---

## Recovery Procedure

### Step 1: Confirm DR trigger and notify

1. Confirm that the event meets the DR trigger criteria. If uncertain, treat it as a P1 incident and use `INCIDENT-RESPONSE.md` until the DR trigger is confirmed.
2. Notify: Platform Operations Lead, Customer Designated Contact, Quality / GxP Lead, CISO. For a production DR event affecting regulated workflows, additionally notify the Functional Escalation Point.
3. Open a DR incident ticket distinct from any related incident tickets. Record the DR trigger time (UTC) and the recovery start time.

### Step 2: Preserve the pre-DR state record

Before any recovery actions:
```bash
# Confirm the last known PITR timestamp for the audit table
aws dynamodb describe-continuous-backups \
  --table-name hcls-audit \
  --region [primary-region]

# Confirm S3 WORM bucket contents in DR region (if CRR is configured)
aws s3 ls s3://[dr-worm-bucket]/ --region [dr-region]

# Export the CloudTrail events for the DR window
aws cloudtrail lookup-events \
  --start-time [dr-trigger-time] \
  --end-time [current-time] \
  --region [primary-region] \
  > /tmp/dr-cloudtrail-[dr-incident-id].json
```

Record the PITR recovery point that will be used. This timestamp defines the RPO for the recovery — the point in time before which all audit records are confirmed intact.

### Step 3: Restore data layer (DynamoDB PITR)

If the audit or HITL queue tables are affected:

```bash
# Restore audit table to the last confirmed good point in time
aws dynamodb restore-table-to-point-in-time \
  --source-table-name hcls-audit \
  --target-table-name hcls-audit-restored-[timestamp] \
  --restore-date-time [recovery-point-iso8601] \
  --region [recovery-region]

# Restore HITL queue table
aws dynamodb restore-table-to-point-in-time \
  --source-table-name hcls-hitl-queue \
  --target-table-name hcls-hitl-queue-restored-[timestamp] \
  --restore-date-time [recovery-point-iso8601] \
  --region [recovery-region]
```

Wait for the restoration to complete (DynamoDB PITR restores typically complete in 10–30 minutes depending on table size). Verify record counts and spot-check records for the hour preceding the recovery point before proceeding.

**Critical:** The restored tables are separate resources with different ARNs. Before routing production traffic to the restored tables, update the Lambda environment variables or CloudFormation parameters to reference the new table ARNs. Do not delete the original tables until the restoration is verified and the DR event is closed.

### Step 4: Restore infrastructure (CloudFormation redeploy)

If the primary region is unavailable or the CloudFormation stack is unrecoverable:

```bash
# Deploy the master stack in the DR region
aws cloudformation deploy \
  --template-file quickstart.yaml \
  --stack-name hcls-dr-[timestamp] \
  --capabilities CAPABILITY_NAMED_IAM \
  --region [dr-region] \
  --parameter-overrides \
      Environment=prod \
      AgentId=[agent-id] \
      DeployMode=[native|container] \
      TemplateBaseUrl=https://[dr-cfn-bucket].s3.[dr-region].amazonaws.com/hcls \
      LambdaCodeBucket=[dr-code-bucket] \
      IdpMetadataUrl=[customer-idp-metadata-url] \
      AuditTableName=hcls-audit-restored-[timestamp] \
      HitlQueueTableName=hcls-hitl-queue-restored-[timestamp]
```

Note: The KMS key in the DR region must be pre-created (or the primary region key must be multi-region enabled) for the restored data to be accessible. Coordinate KMS key configuration with the Security Operations Engineer before the DR deploy.

### Step 5: Validate the restored environment

Before routing production traffic to the recovered environment:

1. **Audit trail validation:** Confirm that audit records from the PITR recovery point are present and readable. Spot-check at least five records for format integrity.
2. **HITL queue validation:** Confirm that all pending approvals from the PITR recovery point are present. Contact the Functional Escalation Point for any approvals that were in-flight at the time of the DR trigger.
3. **Authorization validation:** Run the gateway policy test suite against the restored environment to confirm that the authorization model is intact.
4. **Connectivity validation:** Confirm that connector tests (fixture mode) pass against the restored environment.
5. **Bedrock connectivity:** Confirm that Bedrock inference reaches the DR region endpoint via the VPC Interface Endpoint.

### Step 6: Resume operations and log the gap

When production is restored:

1. Document the recovery timeline: DR trigger → PITR recovery point → environment restore complete → validation complete → production traffic restored.
2. Calculate the actual RPO: time between the PITR recovery point and the DR trigger. Any audit records or HITL queue entries created between those two timestamps may be lost — the Quality / GxP Lead and Functional Escalation Point must assess whether any regulated outputs fall in the gap.
3. If any regulated outputs fall in the RPO gap: the Functional Escalation Point and Quality / GxP Lead must determine whether those outputs need to be reconstructed, re-executed, or reported as a deviation in the customer's QMS.

---

## Life-Sciences Obligations During DR

### Regulatory reporting status
If the DR event affects a system used for regulatory submissions (Agent 01), the Head of Regulatory Affairs must be notified immediately to confirm whether any submission deadlines are at risk. If a submission is pending and the RIM connector is unavailable, the submission timeline must be assessed against any regulatory commitment dates.

### Pharmacovigilance case reporting (Agent 02)
If the DR event occurs during a period when ICSR cases are approaching a 15-day expedited reporting deadline, the Head of Pharmacovigilance must be notified of the platform's unavailability. The backup PV case-processing procedure (manual, without the AI assistant) must be activated for any cases at risk of missing the regulatory deadline. The decision to activate backup procedures rests with the Head of Pharmacovigilance; the Platform Operations Lead provides the estimated restoration timeline to inform that decision.

### Audit trail gaps and GxP deviation
Any confirmed gap in the audit trail for a GxP-covered workflow session must be reported to the Quality / GxP Lead as a potential data-integrity deviation. The Quality / GxP Lead determines whether a formal deviation record in the QMS is required and what corrective action is necessary.

---

## Post-DR Review

Within ten business days of recovery completion:

1. Complete the DR post-incident review (same structure as `INCIDENT-RESPONSE.md` PIR)
2. Document actual RTO and RPO versus targets
3. Review the backup and replication configuration for gaps that contributed to the DR event or the recovery complexity
4. Update DR documentation if any procedure was found to be incorrect or incomplete during the recovery
5. Submit a formal deviation record in the customer's QMS if any regulated output was affected by an audit trail gap or RPO gap
6. Review whether the DR configuration requires an update to the customer's Business Continuity Plan (BCP) or IT Disaster Recovery Plan (IDRP)
