# Quality CAPA Agent — AWS-native Reference

AWS-native rebuild of the Quality CAPA Agent using AWS Step Functions and
Strands/Bedrock. Mirrors `05-quality-capa-agent/` (LangGraph version) in
domain logic; replaces the graph runtime with Step Functions state machine.

## Key design decisions

| Concern | LangGraph version | AWS-native version |
|---|---|---|
| Orchestration | LangGraph StateGraph | Step Functions Express/Standard |
| LLM integration | LangChain `get_llm` factory | Strands `Agent` + Bedrock |
| HITL gate | `interrupt_before` | `waitForTaskToken` (framework-enforced) |
| State persistence | Postgres checkpointer | Step Functions execution state + DynamoDB |
| Deterministic logic | agent/nodes.py | core.py (unit-testable, no AWS) |

## Workflow

```
Assemble → Draft → Check → RouteChoice → Draft (revision)
                                       → HumanReviewGate → Finalize
```

- **Assemble**: classifies event severity/risk, builds grounding corpus
- **Draft**: Strands/Bedrock drafts the CAPA plan (LLM only drafts)
- **Check**: deterministic compliance + grounding gate (no LLM)
- **HumanReviewGate**: `waitForTaskToken` — Qualified Person reviews and approves
- **Finalize**: creates CAPA draft in QMS after QP approval

## Files

```
core.py                         # deterministic classification, compliance, grounding, routing
strands_agent.py                # Strands/Bedrock CAPA plan drafter
lambdas/
  _shared.py                    # audit helpers
  assemble.py                   # event classification + evidence assembly
  draft.py                      # Strands/Bedrock drafter invocation
  check.py                      # compliance + grounding check + routing
  hitl_notify.py                # waitForTaskToken HITL gate
  finalize.py                   # QMS CAPA draft creation (post QP approval)
stepfunctions/
  quality_capa.asl.json         # Step Functions state machine definition
tests/
  test_core.py                  # deterministic logic tests
  test_asl.py                   # ASL structural tests
sample_input.json               # example input for testing
DEPLOY.md                       # deployment guide
requirements.txt                # Python dependencies
```

## Quick test (no AWS required)

```bash
EXTRACT_MODE=demo pytest tests/ -v
```
