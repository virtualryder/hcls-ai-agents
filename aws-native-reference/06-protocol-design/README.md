# Protocol Design Agent — AWS-native Reference

AWS-native rebuild of the Protocol Design Agent using AWS Step Functions and
Strands/Bedrock. Mirrors `06-protocol-design-agent/` (LangGraph version) in
domain logic; replaces the graph runtime with Step Functions state machine.

## Key design decisions

| Concern | LangGraph version | AWS-native version |
|---|---|---|
| Orchestration | LangGraph StateGraph | Step Functions Express/Standard |
| LLM integration | LangChain `get_llm` factory | Strands `Agent` + Bedrock |
| HITL gate | `interrupt_before` | `waitForTaskToken` (framework-enforced) |
| State persistence | Postgres checkpointer | Step Functions execution state + DynamoDB |
| Deterministic logic | agent/nodes.py | core.py (unit-testable, no AWS) |
| RWD privacy | connector-enforced | Lambda IAM + cell-suppression policy |

## Workflow

```
Assemble → Draft → Check → RouteChoice → Draft (revision)
                                       → HumanReviewGate → Finalize
```

- **Assemble**: builds evidence corpus from guidance refs + RWD cohort data
- **Draft**: Strands/Bedrock drafts protocol sections (LLM only drafts)
- **Check**: deterministic compliance + grounding gate (no LLM)
- **HumanReviewGate**: `waitForTaskToken` — Medical/Clinical Reviewer reviews
- **Finalize**: packages sections for IND/CTA after reviewer approval

## Files

```
core.py                           # deterministic compliance, grounding, regulatory risk, routing
strands_agent.py                  # Strands/Bedrock protocol section drafter
lambdas/
  _shared.py                      # audit helpers
  assemble.py                     # evidence corpus assembly from guidance + RWD
  draft.py                        # Strands/Bedrock drafter invocation
  check.py                        # compliance + grounding check + routing
  hitl_notify.py                  # waitForTaskToken HITL gate
  finalize.py                     # IND/CTA package creation (post reviewer approval)
stepfunctions/
  protocol_design.asl.json        # Step Functions state machine definition
tests/
  test_core.py                    # deterministic logic tests
  test_asl.py                     # ASL structural tests
sample_input.json                 # example input for testing
DEPLOY.md                         # deployment guide
requirements.txt                  # Python dependencies
```

## Quick test (no AWS required)

```bash
EXTRACT_MODE=demo pytest tests/ -v
```
