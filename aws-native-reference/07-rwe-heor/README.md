# RWE/HEOR Evidence Agent — AWS-native Reference

Step Functions + Lambda + Bedrock Strands implementation of the RWE/HEOR agent.
Mirrors the LangGraph implementation but runs natively on AWS without a persistent
server. The LLM synthesizes narrative only; all statistical computation is deterministic.

## Architecture

```
Assemble → Synthesize → Check → RouteChoice → [loop] → HumanReviewGate (HITL) → Finalize
```

- **Assemble**: build grounding corpus from RWD cohort results
- **Synthesize**: Strands/Bedrock drafts synthesis from validated stats
- **Check**: deterministic grounding + compliance gate (no LLM)
- **HumanReviewGate**: `waitForTaskToken` — Epidemiologist must approve
- **Finalize**: publish evidence package (post-approval only)

## PHI compliance

All RWD outputs are aggregate de-identified counts only (minimum cell N >= 11).
PHI never crosses the query boundary. The gateway enforces this via scoped tokens.

## Files

| File | Purpose |
|---|---|
| `core.py` | Deterministic grounding + compliance logic |
| `strands_agent.py` | Bedrock Strands drafter (demo fallback) |
| `lambdas/` | One file per Step Functions state |
| `stepfunctions/rwe_heor.asl.json` | State machine definition |
| `tests/` | Unit tests (no AWS required) |
