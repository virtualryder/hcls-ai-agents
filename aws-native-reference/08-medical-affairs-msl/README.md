# Medical Affairs MSL Agent — AWS-native Reference

Step Functions + Lambda + Bedrock Strands implementation of the Medical Affairs MSL agent.
Mirrors the LangGraph implementation but runs natively on AWS. The LLM drafts the brief;
all compliance logic is deterministic and cannot be bypassed.

## Architecture

```
Assemble → Draft → Check → RouteChoice → [loop] → HumanReviewGate (HITL) → Finalize (MLR)
```

- **Assemble**: retrieve HCP profile (CRM) and approved documents (DMS)
- **Draft**: Strands/Bedrock drafts on-label brief from approved content only
- **Check**: deterministic compliance gate (off-label, promotional, grounding) — no LLM
- **HumanReviewGate**: `waitForTaskToken` — Medical Affairs Approver must approve
- **Finalize**: submit to MLR review (HIGH-RISK write, post-approval only)

## Compliance enforcement

Off-label or promotional findings force `ESCALATE` in `core.route()` — they still route
to `HumanReviewGate` (so the Approver sees and resolves the finding) but `Finalize` will
not submit to MLR until the Approver explicitly approves via `SendTaskSuccess`.

## Files

| File | Purpose |
|---|---|
| `core.py` | Deterministic compliance + grounding logic |
| `strands_agent.py` | Bedrock Strands drafter (demo fallback) |
| `lambdas/` | One file per Step Functions state |
| `stepfunctions/medical_affairs_msl.asl.json` | State machine definition |
| `tests/` | Unit tests (no AWS required) |
