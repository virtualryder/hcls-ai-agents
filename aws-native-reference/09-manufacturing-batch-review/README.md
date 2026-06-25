# Agent 09 (AWS-native) — Manufacturing Batch-Review

Strands + Step Functions rebuild of the LangGraph agent. Step Functions orchestrates deterministic
Lambdas (`assemble → draft → check → RouteChoice → QAReviewGate → finalize`); Strands/Bedrock drafts
only the human-readable exception report. The **QA gate uses `waitForTaskToken`** — framework-enforced
HITL: the state machine pauses until a QA reviewer calls `SendTaskSuccess` with their signed decision.

- `core.py` — deterministic scan (review by exception) + routing; no model, no AWS deps.
- `lambdas/` — `assemble`, `draft`, `check`, `finalize`, `hitl_notify` (+ `_shared`).
- `stepfunctions/manufacturing_batch_review.asl.json` — the state machine (QA `waitForTaskToken` gate).
- `strands_agent.py` — Bedrock drafting (optional; falls back to a deterministic report).
- `tests/` — `test_core.py` (logic) + `test_asl.py` (state-machine structure). No AWS/model needed.

Run the tests: `pytest aws-native-reference/09-manufacturing-batch-review/tests -q`.
Deploy: see `DEPLOY.md`.
