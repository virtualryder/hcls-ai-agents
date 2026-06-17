# AWS-Native: Clinical Trial Ops Agent (03)

Serverless reference implementation of the Clinical Trial Ops agent using
AWS Step Functions, Lambda, and Bedrock (Claude).  Mirrors the LangGraph
agent in `03-clinical-trial-ops-agent/` with a fully managed, pay-per-use
AWS architecture.

## Architecture

```
EventBridge / API Gateway
        │
        ▼
Step Functions (clinical_trial_ops.asl.json)
  ├─ Assemble  → Lambda: gather study/eTMF data
  ├─ Draft     → Lambda: Strands/Bedrock briefing generation
  ├─ Check     → Lambda: compliance + grounding + risk scoring
  ├─ RouteDecision (Choice) ──► Draft (revise loop)
  └─ HumanReviewGate  (waitForTaskToken — SNS → ClinOps Lead)
        └─ Finalize  → Lambda: seal audit trail, return result
```

## Files

| Path | Purpose |
|---|---|
| `core.py` | Deterministic compliance/grounding/risk logic |
| `strands_agent.py` | Bedrock drafting + demo fallback |
| `lambdas/assemble.py` | Evidence assembly |
| `lambdas/draft.py` | Briefing generation |
| `lambdas/check.py` | Quality gating |
| `lambdas/hitl_notify.py` | HITL SNS notification |
| `lambdas/finalize.py` | Result finalization |
| `stepfunctions/clinical_trial_ops.asl.json` | Step Functions ASL |
| `tests/test_core.py` | Core unit tests |
| `tests/test_asl.py` | ASL structural tests |

## Quick Start (demo mode, no AWS credentials)

```bash
cd aws-native-reference/03-clinical-trial-ops
export EXTRACT_MODE=demo
pytest tests/ -v
```

## Deployment

See `DEPLOY.md` for full CloudFormation / SAM deployment instructions.
