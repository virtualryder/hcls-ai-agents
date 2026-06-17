# Model Degradation Response Runbook
### HCLS AI Agent Suite — LLM Performance Monitoring, Grounding Regression, and Prompt Drift

---

## Purpose

The LLM's behavior can change without any code change: Bedrock model versions are updated, prompt drift accumulates through small unreviewed edits, or a model update alters performance on domain-specific tasks. In regulated life-sciences workflows, a degradation in output quality — reduced grounding accuracy, structural incompleteness, increased prohibited-language rate — is not merely a product quality issue; it is potentially a data-integrity and patient-safety issue.

This runbook defines how to detect, assess, contain, and remediate model degradation events.

---

## Detection Mechanisms

### Mechanism 1: Eval harness regression (primary)

The governance eval harness in `governance/evals/run_evals.py` runs against reviewed golden artifacts — outputs that have been accepted as correct by qualified domain reviewers. The harness measures:

- **Grounding accuracy:** percentage of claims in the output traceable to the grounding corpus
- **Structural completeness:** percentage of required structural elements present (E2B fields, CTD section anatomy, CAPA report elements)
- **Prohibited language rate:** rate of compliance-gate failures on clean inputs (should be near zero for correct prompts)
- **Consistency score:** variance in outputs across identical inputs (high variance suggests model instability)

**Regression threshold (recommended):**
- Grounding accuracy: alert if p50 drops more than 5 percentage points from the established baseline
- Structural completeness: alert if any required-field miss rate exceeds 2%
- Prohibited language on clean inputs: alert if rate exceeds 0.5% (should be near zero)

The eval harness should run in CI on every pull request, and on a scheduled basis (weekly minimum) in production against the live deployed model and prompt configuration.

### Mechanism 2: Grounding check failure rate (production monitoring)

The grounding check runs on every agent output before it enters the HITL queue. A rising rate of grounding failures for previously clean input types signals model degradation (the model is producing claims it did not before, or is producing weaker grounding-corpus traceability).

**CloudWatch metric:** `hcls/grounding/failure_rate` by agent and workflow type
**Alarm threshold:** Alert if the 7-day rolling average exceeds 2x the baseline established in the first 30 days of production

### Mechanism 3: Compliance gate failure rate (production monitoring)

The compliance gate checks for structural completeness and prohibited-language patterns. An unexpected spike in compliance-gate failures — particularly on workflow types that were previously clean — signals prompt degradation or model behavior change.

**CloudWatch metric:** `hcls/compliance_gate/failure_rate` by agent and workflow type
**Alarm threshold:** Alert if the 7-day rolling average exceeds 3x the baseline

### Mechanism 4: HITL reviewer rejection rate (human signal)

HITL reviewers explicitly reject drafts that do not meet their quality bar. A rising rejection rate in the HITL queue is the strongest human-quality signal. It should be monitored monthly.

**DynamoDB query:** `SELECT COUNT(*) FROM hcls-hitl-queue WHERE decision='REJECTED' AND created_at_utc > [30-days-ago]` grouped by agent and workflow type

**Review threshold:** If the monthly rejection rate for any workflow type is more than 2x the prior month, investigate.

### Mechanism 5: Prompt hash drift detection (CI enforcement)

The prompt registry (`governance/prompt_registry.py`) compares the hash of every deployed prompt against the hash-pinned manifest. If a prompt file has changed without a manifest update, CI fails. In production, a periodic hash verification job should confirm that deployed prompts match the pinned manifest.

**Alarm:** If the prompt hash verification job detects drift in a deployed environment, this is a P2 incident (potential unauthorized prompt change).

---

## Degradation Classification

| Severity | Definition | Example |
|---|---|---|
| **Critical** | Output quality degradation is sufficient to cause a regulated output to reach the HITL queue that a qualified reviewer would not be able to reliably catch as defective | Grounding accuracy drops below 60%; structured E2B fields systematically missing; prohibited-language gate fails to catch promotional claims |
| **Significant** | Output quality is degraded but the HITL gate and reviewer provide a reliable catch | Grounding accuracy drops 10–20%; structural completeness drops for optional elements; increased revision rate in HITL |
| **Minor** | Degradation is detectable in the eval harness but not observable in human-reviewed outputs | Small variance increase; marginal grounding accuracy change below threshold |

---

## Response Procedure

### Step 1: Confirm degradation

Upon receiving a degradation alert:

1. Run the full eval harness against the current production configuration:
   ```bash
   cd [repo-root]
   PYTHONPATH=platform_core BEDROCK_REGION=[region] python -m governance.evals.run_evals
   ```
2. Compare results against the baseline (stored in `governance/evals/baselines/[agent-id]-baseline.json`)
3. Identify the specific metrics that have degraded and the magnitude of the change
4. Check the prompt manifest for any unreviewed drift:
   ```bash
   python -m governance.prompt_registry  # verify; fails if drift detected
   ```
5. Check the Bedrock model version in use against the version pinned in the CloudFormation template. If AWS has automatically updated the model endpoint, this is a likely cause.

### Step 2: Classify and escalate

- **Critical:** Immediately notify Platform Operations Lead, Life Sciences Domain Advisor, Functional Escalation Point, and Quality / GxP Lead. Move to containment (Step 3) before further investigation.
- **Significant:** Notify Platform Operations Lead and Life Sciences Domain Advisor. Notify Functional Escalation Point within 4 hours if the degradation affects an active regulated workflow type.
- **Minor:** Notify Life Sciences Domain Advisor. Schedule investigation within 5 business days. No containment required.

### Step 3: Containment (Critical and Significant)

**Option A: Suspend write-tool access**
If the degradation affects a regulated output workflow and the severity is Critical, suspend the write-tool grant for the affected agent by updating the gateway policy. The agent continues to function for read and draft operations; the HITL gate still activates; but the finalize node cannot invoke the high-risk connector. This prevents any degraded output from reaching a system of record until the root cause is identified and remediated.

```python
# In platform_core/hcls_agent_platform/mcp_gateway/policy.py
# Temporarily remove write tools from the affected agent's grant set
# This change requires the standard prompt/policy change control process
```

**Option B: Increase HITL review intensity**
If the degradation is Significant but the HITL reviewer is reliably catching the degraded outputs, the containment may be increasing the HITL review checklist requirements rather than suspending write access. The Life Sciences Domain Advisor and Functional Escalation Point must agree that the HITL gate is sufficient containment.

**Option C: Rollback the model version**
If the root cause is identified as a Bedrock model version change, roll back to the pinned model version in the CloudFormation template:
```bash
aws cloudformation update-stack \
  --stack-name hcls-prod \
  --parameter-overrides BedrockModelId=[previous-model-id] \
  --use-previous-template
```
Confirm the eval harness passes against the rolled-back model before restoring write access.

### Step 4: Root cause investigation

Investigate across four potential causes:

**Cause 1: Bedrock model version change**
- Check `bedrock:GetFoundationModel` API for the model version currently resolving at the deployed endpoint
- Compare to the model version in the CloudFormation `BedrockModelId` parameter
- If changed: determine whether AWS updated the model version automatically (check AWS announcements) or whether the CloudFormation parameter was changed

**Cause 2: Prompt drift**
- Run `python -m governance.prompt_registry` to detect hash mismatches
- If drift is detected: identify what changed, by whom, and when (git log of the prompt files)
- Unauthorized prompt changes are a P2 security incident and must be reported to the Quality / GxP Lead

**Cause 3: Grounding corpus quality change**
- If the knowledge base or document store has been updated (new guidance documents, updated source files), the grounding accuracy for existing prompts may change
- Review Bedrock Knowledge Base update timestamps against the degradation onset
- If a corpus update is the cause: re-evaluate golden test cases against the updated corpus; update the eval baselines if the corpus change is intentional and the new outputs are correct

**Cause 4: Input distribution shift**
- If the customer's workflows are producing inputs with different characteristics than the golden test cases (e.g., a new therapeutic area, a new document type), the prompt may not generalize well
- Review the workflow inputs that produced the highest grounding failure rates
- If input distribution shift is the cause: extend the eval harness with representative inputs from the new distribution; update the prompt with a reviewed change

### Step 5: Remediation and validation

Once the root cause is identified:

1. Implement the fix (model rollback, prompt update, corpus update, or prompt tuning)
2. Run the full eval harness against the fixed configuration — results must meet or exceed the baseline before restoring write access
3. Document the change in the prompt registry (if a prompt was changed) or the model configuration (if the model version was updated)
4. For prompt changes: require a second reviewer's sign-off before deploying to production
5. Restore write-tool access or reduce the HITL review intensity once the eval harness confirms the fix

### Step 6: Post-remediation review

Within ten business days of recovery:

1. Complete a model degradation post-incident review:
   - Root cause and timeline
   - Regulated outputs affected (if any — identify which workflow sessions were active during the degradation window; contact the Functional Escalation Point)
   - Containment effectiveness
   - Remediation actions and validation evidence
   - Corrective actions: improved monitoring, baseline adjustments, eval harness extensions, change-control improvements

2. Submit a quality deviation record in the customer's QMS if any GxP-regulated output was produced during the degradation window, unless the Functional Escalation Point and Quality / GxP Lead confirm that the HITL gate provided adequate catch for all affected outputs.

3. Update the eval harness baseline to reflect the validated post-remediation performance level.

---

## Prompt Change Control (Non-Degradation Context)

Any intentional prompt change — for capability improvement, domain expansion, or error correction — follows this procedure:

1. The change is proposed as a pull request against the prompt files in the agent's `agent/prompts/` directory
2. The PR includes: the proposed change, the rationale, and the diff against the current hash-pinned version
3. A Life Sciences Domain Advisor reviews the change for domain accuracy and safety implications
4. The eval harness runs against the proposed change in CI; the PR cannot be merged if the harness fails
5. A second reviewer approves the PR (four-eyes principle)
6. Upon merge, the prompt registry is updated: `python -m governance.prompt_registry --update`
7. The new hashes are pinned in `governance/prompt_manifest.json`; the manifest update is included in the same PR
8. The deployment pipeline promotes the updated prompt to production; the production hash verification job confirms the deployed hash matches the manifest within one hour of deployment

Every prompt change is recorded in the git history with the PR title, reviewers, and merge timestamp. This log is available as change-control evidence for GxP audits and model-risk reviews.
