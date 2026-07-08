# TCO & ROI Model — HCLS AI Agent Suite
### Cost estimates, AWS run costs, and return-on-investment framework

> **For Solutions Architects and engagement managers.** This model gives you the numbers to answer "what does it cost to run?" and "what is the business case?" Use the tables below as a starting point — plug in the customer's actual volumes and FTE rates to produce a customer-specific business case. Assumptions are explicit so they can be challenged and refined.
>
> All figures are illustrative estimates based on publicly available AWS pricing (June 2026, us-east-1). Actual costs depend on usage volume, negotiated rates, and regional pricing. Always validate with the AWS Pricing Calculator before presenting to a customer.

---

## Section 1 — AWS Run Cost Estimates (Monthly, Steady State)

### 1.0 Scenario Summary — Pilot vs Production

> **MODEL ASSUMPTION — illustrative estimate** built from published us-east-1 on-demand list
> prices as of mid-2026; prices and token economics change frequently; validate with the AWS
> Pricing Calculator and your AWS account team before quoting. **Bedrock token volume is the
> dominant, workload-dependent variable.**

Derived from the per-agent figures in §1.1–§1.2 (numbers unchanged):

| | **Pilot** (1 agent, dept-scale) | **Production** (8-agent suite, §1.1 volumes) |
|---|---:|---:|
| Reference workload | Agent 02 @ ~100 ICSRs/mo (~10K governed requests/mo, ~50 users) | All 8 agents at §1.1 volumes (~2,000 users) |
| Bedrock inference ← *sensitivity driver* | ~$360/mo (per §1.1 scale factor) | ~$6,060/mo |
| Infrastructure baseline (§1.2, single-agent slice vs full suite) | ~$110/mo | ~$435/mo |
| **TOTAL (monthly)** | **~$470/mo** | **~$6,500/mo** |

**Sensitivity (one line):** 2× Bedrock token volume ≈ **+$6,060/mo** at suite scale (inference is
~93% of the suite total). Not included: personnel, ProServe/SI delivery fees, data egress at
scale, enterprise support plan, non-prod environments. The pilot *phase* budget in §1.3 is higher
than this steady-state pilot column because acceptance testing runs at partial production volume.

### 1.1 Bedrock Inference Costs

**Model assumptions:**
- Primary model: Claude claude-sonnet-4-6 (input $3.00/M tokens, output $15.00/M tokens — approximate; check current pricing)
- Classification steps: Claude Haiku (input $0.80/M tokens, output $4.00/M tokens)
- Demo mode uses zero Bedrock tokens

**Per-agent monthly inference cost (illustrative):**

| Agent | Use case | Estimated monthly volume | Avg tokens/workflow (in+out) | Monthly inference cost |
|---|---|---|---|---|
| 01 Regulatory Writing | Benefit-risk section drafts | 50 drafts/mo | 8,000 tokens | ~$480 |
| 02 Pharmacovigilance (ICSR) | ICSR narrative drafts | 500 ICSRs/mo | 6,000 tokens | ~$1,800 |
| 03 Clinical Trial Ops | TMF gap reports + queries | 200 reports/mo | 4,000 tokens | ~$720 |
| 04 Site/Patient Matching | Feasibility + cohort reports | 20 studies/mo | 10,000 tokens | ~$600 |
| 05 Quality / CAPA | CAPA drafts | 100 CAPAs/mo | 5,000 tokens | ~$900 |
| 06 Protocol Design | Protocol section drafts | 10 protocols/mo | 12,000 tokens | ~$720 |
| 07 RWE / HEOR | Evidence summaries | 20 analyses/mo | 8,000 tokens | ~$480 |
| 08 Medical Affairs MSL | Pre-call briefs | 200 briefs/mo | 3,000 tokens | ~$360 |

**Notes:**
- Volumes above are representative for a mid-size pharma (10,000–30,000 employees). Adjust for customer's actual pipeline.
- Haiku is used for classification and seriousness-assessment steps (lower token cost); Sonnet for drafting.
- Grounding check runs after draft — adds ~20% to token count estimates above.
- Bedrock charges per token consumed, not per request. EXTRACT_MODE=demo uses zero tokens.

**Total monthly inference (all 8 agents, above volumes):** ~$6,060/month

**Scale factor:**
- 100 ICSRs/month → ~$360/month (Agent 02 alone)
- 1,000 ICSRs/month → ~$3,600/month
- 5,000 ICSRs/month → ~$18,000/month

---

### 1.2 AWS Infrastructure Costs (All 8 Agents, Steady State)

| Service | Configuration | Monthly estimate |
|---|---|---|
| **Amazon ECS Fargate** | 8 agent services; 0.5 vCPU / 1 GB per service; ~160 task-hours/month total | ~$80 |
| **Amazon DynamoDB** | Agent state tables + audit trail; ~10 GB storage; ~5M read + 2M write units/month | ~$60 |
| **AWS Step Functions** | ~10,000 state transitions/month (AWS-native reference path) | ~$25 |
| **Amazon Cognito** | Up to 10,000 MAU (Monthly Active Users) | Free tier (≤50K MAU) |
| **AWS Secrets Manager** | ~40 secrets; 1M API calls/month | ~$20 |
| **Amazon S3** | Document artifacts; ~100 GB storage | ~$5 |
| **Amazon CloudWatch** | Logs, metrics, dashboards | ~$30 |
| **AWS KMS** | Customer-managed keys; ~100K key requests/month | ~$10 |
| **VPC / NAT Gateway** | NAT Gateway data processed; ~100 GB/month | ~$15 |
| **Amazon QLDB** *(optional — Part 11 highest assurance)* | ~1M document revisions/month | ~$40 |
| **Bedrock Guardrails** | ~50K API calls/month | ~$50 |
| **AgentCore Gateway + Identity** | Per-call pricing; ~50K invocations/month | ~$100 |
| **Total infrastructure (excl. inference)** | | **~$435/month** |

**Total monthly AWS cost (infrastructure + inference, all 8 agents at illustrative volumes):** ~$6,500/month

**Annualized AWS run cost:** ~$78,000/year

---

### 1.3 POC / Pilot Environment Costs

| Phase | Duration | Estimated AWS cost | Notes |
|---|---|---|---|
| POC (demo mode) | 8–12 weeks | ~$500–$1,500 | Minimal Bedrock inference (demo mode); infra only |
| POC (with live Bedrock) | 8–12 weeks | ~$2,000–$5,000 | Some live inference for acceptance testing |
| Pilot (production-like) | 12–20 weeks | ~$8,000–$20,000 | Live inference at partial volume |

MAP/PoA credits typically cover a significant portion of POC/Pilot AWS costs (see `docs/AWS-FUNDING-AND-GTM.md`).

---

## Section 2 — Total Cost of Ownership (3-Year)

### 2.1 Three-Year TCO Model (Illustrative — Mid-Size Pharma, 3 Agents)

Deploying Agents 01 (Regulatory Writing), 02 (Pharmacovigilance), and 05 (Quality/CAPA) for a pharma with ~500 ICSRs/month and 50 regulatory drafts/month.

| Cost category | Year 1 | Year 2 | Year 3 | 3-Year total |
|---|---|---|---|---|
| **One-time engagement fees** | | | | |
| Assessment | $75,000 | — | — | $75,000 |
| POC (1 agent) | $150,000 | — | — | $150,000 |
| Pilot (3 agents) | $400,000 | — | — | $400,000 |
| **Total one-time** | **$625,000** | **—** | **—** | **$625,000** |
| **Recurring AWS costs** | | | | |
| Bedrock inference (3 agents, above volumes) | $35,000 | $40,000 | $45,000 | $120,000 |
| Infrastructure (3 agents) | $5,000 | $5,500 | $6,000 | $16,500 |
| **Total AWS (recurring)** | **$40,000** | **$45,500** | **$51,000** | **$136,500** |
| **Managed service / operations** | | | | |
| SI platform operations (if managed service) | $120,000 | $120,000 | $120,000 | $360,000 |
| **Total 3-year TCO** | | | | **~$1,121,500** |

*If the institution operates the platform internally (not as a managed service), remove the SI operations line. Reduce by ~$360K.*

---

## Section 3 — ROI Framework

### 3.1 Agent 02 — Pharmacovigilance ICSR (Highest ROI, Fastest Payback)

**Current state (manual):**

| Metric | Assumption | Basis |
|---|---|---|
| Monthly ICSR volume | 500 ICSRs/month | Customer-provided |
| Average processing time | 4.5 hours/ICSR | Industry benchmark; ask customer to confirm |
| Total FTE-hours/month | 2,250 hours | 500 × 4.5 |
| FTE blended rate | $75/hour | PV processor fully-loaded cost |
| Monthly FTE cost | $168,750/month | 2,250 × $75 |
| Rework rate | 18% | Industry benchmark for manual ICSR processing |
| Rework cost/month | $30,375/month | 18% × $168,750 |
| **Total current-state monthly cost** | **$199,125/month** | |

**Agent-assisted state:**

| Metric | Assumption |
|---|---|
| Time reduction (agent drafts narrative; human reviews) | 65% reduction in FTE time |
| FTE-hours/month (agent-assisted) | 788 hours (500 × 1.58 hrs review time) |
| Monthly FTE cost (agent-assisted) | $59,063/month |
| Rework rate (agent + grounding check) | 6% |
| Rework cost/month | $3,544/month |
| **Total agent-assisted monthly cost** | **$62,607/month** |

**Monthly savings (FTE + rework reduction):** $136,518/month

**Annual savings:** $1,638,216/year

**Annual AWS cost (Agent 02, 500 ICSRs/month):** ~$25,200/year (inference + infra)

**Net annual benefit:** ~$1,613,000/year

**Payback period (POC + Pilot cost = $550,000):** ~4 months after Pilot go-live

---

### 3.2 Agent 01 — Regulatory Writing

**Current state:**

| Metric | Assumption |
|---|---|
| Monthly volume | 50 benefit-risk or CSR section drafts |
| Average medical writer time per draft | 12 hours (evidence retrieval + drafting + consistency check) |
| FTE-hours/month | 600 hours |
| Medical writer blended rate | $120/hour |
| Monthly FTE cost | $72,000/month |
| Revision cycle rate | 30% require >1 revision |

**Agent-assisted state:**

| Metric | Assumption |
|---|---|
| Time reduction (agent retrieves evidence, drafts, checks consistency) | 55% |
| FTE-hours/month | 270 hours (review, judgment calls, approval) |
| Monthly FTE cost | $32,400/month |
| Revision rate | 12% |
| **Net monthly savings** | ~$39,600/month |

**Annual savings:** ~$475,000/year

---

### 3.3 Benefit Summary Table (All 8 Agents, Illustrative)

| Agent | Annual FTE savings (mid estimate) | Annual error/rework reduction | Total annual benefit |
|---|---|---|---|
| 01 Regulatory Writing | $475,000 | $95,000 | $570,000 |
| 02 Pharmacovigilance | $1,638,000 | $365,000 | $2,003,000 |
| 03 Clinical Trial Ops | $380,000 | $120,000 | $500,000 |
| 04 Site/Patient Matching | $250,000 | $50,000 | $300,000 |
| 05 Quality / CAPA | $420,000 | $180,000 | $600,000 |
| 06 Protocol Design | $310,000 | $90,000 | $400,000 |
| 07 RWE / HEOR | $290,000 | $60,000 | $350,000 |
| 08 Medical Affairs MSL | $180,000 | $40,000 | $220,000 |
| **Total (all 8 agents)** | **$3,943,000** | **$1,000,000** | **~$4,943,000/year** |

*Benefits are illustrative. Actual savings depend on customer volume, FTE rates, current error rates, and adoption curve. Reduce by 50% for a conservative case.*

---

## Section 4 — How to Use This Model With a Customer

### Step 1 — Collect four numbers from the customer

1. Monthly volume for the target workflow (e.g., ICSRs processed, drafts written)
2. Current average FTE hours per case
3. FTE blended hourly rate (fully loaded, including benefits)
4. Current rework / revision rate (%)

### Step 2 — Apply the reduction assumptions

Use the reduction percentages from Section 3 as a starting point. Adjust based on the customer's workflow complexity and the degree of connector integration (demo mode savings are lower than full live-connector savings).

### Step 3 — Calculate payback period

```
Payback (months) = (POC + Pilot fees) / (Monthly savings - Monthly AWS cost)
```

Example (Agent 02, 500 ICSRs/month):
```
Payback = $550,000 / ($136,518 - $2,100) = 4.1 months
```

### Step 4 — Build the board-level summary

| | Conservative (-50%) | Base | Optimistic (+25%) |
|---|---|---|---|
| Annual benefit | `$[X]M` | `$[X]M` | `$[X]M` |
| Annual AWS cost | `$[X]K` | `$[X]K` | `$[X]K` |
| Net annual benefit | `$[X]M` | `$[X]M` | `$[X]M` |
| Payback period | `[X] months` | `[X] months` | `[X] months` |
| 3-year NPV (10% discount) | `$[X]M` | `$[X]M` | `$[X]M` |

---

## Section 5 — SA Worksheet (Quick Reference)

Fill in customer-specific values:

```
Customer name:              ___________________________
Target agent(s):            ___________________________
Monthly workflow volume:     ___________________________
Current FTE hours/case:      ___________________________
FTE blended rate ($/hr):    ___________________________
Current rework rate (%):    ___________________________

Calculated:
  Current monthly FTE cost:      $ _______________
  Agent-assisted monthly cost:   $ _______________
  Monthly savings:               $ _______________
  Monthly AWS cost (estimate):   $ _______________
  Net monthly savings:           $ _______________
  POC + Pilot investment:        $ _______________
  Payback period (months):       _______________
  Year 1 net benefit:            $ _______________
  3-year net benefit:            $ _______________
```

---

*Related: `offerings/COST-ROI-MODEL.md` (narrative version), `offerings/BATTLECARD.md`, `docs/AWS-FUNDING-AND-GTM.md`*

---

> **Note for SA teams:** The Excel/XLSX version of this model is available from the SI's internal delivery toolkit. This Markdown version is the source of record — the XLSX is a formatted export. If you need to update assumptions, update this file first.

---
**Value side:** see [ROI-CASE-STUDY.md](ROI-CASE-STUDY.md) for a fully worked, illustrative ROI example with totals.
