# AWS-Native: Pharmacovigilance Agent (02)

Serverless reference implementation of the Pharmacovigilance ICSR intake agent using
AWS Step Functions, Lambda, and Bedrock (Claude via Strands). Mirrors the LangGraph
agent in `02-pharmacovigilance-agent/` with a fully managed, pay-per-use AWS architecture.

## Architecture

```
EventBridge / API Gateway
        │
        ▼
Step Functions (pharmacovigilance.asl.json)
  ├─ Assemble   → Lambda: validity check + E2B field extract + MedDRA/WHODrug coding + seriousness
  ├─ Draft      → Lambda: Strands/Bedrock ICSR narrative generation
  ├─ Check      → Lambda: PHI check + grounding + required-element gate + core.route()
  ├─ RouteChoice (Choice) ──► Draft (revise loop, max 1 revision)
  └─ HumanReviewGate (waitForTaskToken — SNS → PV Medical Reviewer)
        └─ Finalize → Lambda: submit_report only if review.approved; seal audit trail
```

## Pipeline Steps

| State | Lambda | Description |
|---|---|---|
| `Assemble` | `lambdas/assemble.py` | ICSR validity (4 elements), E2B field extraction, MedDRA PT + WHODrug coding, ICH E2A seriousness classification, 7/15-day clock |
| `Draft` | `lambdas/draft.py` | Strands/Bedrock ICSR narrative; demo fallback with no AWS creds |
| `Check` | `lambdas/check.py` | `core.route()`: PHI check, grounding gate, required-element check |
| `RouteChoice` | — | REVISE → loop to Draft; ESCALATE/APPROVE_DRAFT → HumanReviewGate |
| `HumanReviewGate` | `lambdas/hitl_notify.py` | `waitForTaskToken` parks execution; DynamoDB + SNS notify PV reviewer |
| `Finalize` | `lambdas/finalize.py` | `submit_report()` only when `review.approved = True`; audit sealed |

## Files

| Path | Purpose |
|---|---|
| `core.py` | Deterministic PV logic: validity, seriousness, clock, grounding, PHI, route() |
| `strands_agent.py` | Bedrock ICSR narrative drafting + grounding-safe demo fallback |
| `lambdas/_shared.py` | Shared audit/ok/err helpers |
| `lambdas/assemble.py` | Evidence assembly (extract + code) |
| `lambdas/draft.py` | Narrative generation |
| `lambdas/check.py` | Quality gating |
| `lambdas/hitl_notify.py` | HITL waitForTaskToken record + SNS |
| `lambdas/finalize.py` | Conditional submit |
| `stepfunctions/pharmacovigilance.asl.json` | Step Functions ASL definition |
| `tests/test_core.py` | Core unit tests (validity, seriousness, grounding, route) |
| `tests/test_asl.py` | ASL structural tests |
| `sample_input.json` | Realistic AE intake (Lisinopril / acute renal failure) |

## Quick Start (demo mode, no AWS credentials)

```bash
cd aws-native-reference/02-pharmacovigilance
export EXTRACT_MODE=demo
pytest tests/ -v
```

## Deployment

See `DEPLOY.md` for full SAM deployment instructions.

## Regulatory Compliance

| Requirement | Implementation |
|---|---|
| ICH E2A — 4 mandatory ICSR elements | `core.validity_check()` |
| ICH E2A — seriousness criteria | `core.seriousness_classification()` |
| ICH E2A — 7/15-day expedited clock | `core.expedited_clock()` |
| GVP Module VI — audit trail | Every Lambda appends a timestamped entry |
| 21 CFR Part 11 — electronic records | `waitForTaskToken` gate; reviewer identity bound at submit |
| PHI / HIPAA — no SSN in narrative | `core.phi_check()` escalates on SSN pattern |
| Grounding — no invented numbers | `core.grounding_findings()` checks all numbers > 12 |
