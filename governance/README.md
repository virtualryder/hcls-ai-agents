# Governance & Evaluation Framework

Governance is built into this suite from the first commit — not added after a
pilot. Every regulated artifact an agent produces is graded by deterministic
checks before a human sees it, and the same checks run in CI so a prompt or code
change cannot silently degrade a known-good output.

| Layer | File | What it enforces |
|---|---|---|
| **Grounding** | `grounding.py` | Every number/entity in a regulated artifact is traceable to case state (no hallucinated dose, endpoint, or institution). |
| **Prompt registry** | `prompt_registry.py`, `prompt_manifest.json` | Prompts are versioned and hash-pinned; CI fails on un-bumped prompt drift (model-risk change control). |
| **Evals** | `evals/run_evals.py`, `evals/golden/*.json` | Structural (CIOMS/E2B ICSR; benefit-risk section anatomy) + grounding regression over reviewed golden artifacts. |
| **HITL gates** | `tests/test_hitl_gates.py` | High-risk tools are *framework-enforced* to require a verified human approval — not merely documented. |
| **Red team** | `redteam/test_prompt_injection.py` | Injected instructions cannot change authorization; grounding catches smuggled facts; PHI masking blocks exfiltration. |
| **Fairness** | `fairness/test_cohort_representativeness.py` | Flags material demographic under-representation in proposed cohorts (FDA Diversity Action Plan posture). |

## Run it

```bash
pip install pytest
# All governance + platform checks
PYTHONPATH=platform_core pytest platform_core/tests governance -q
# Eval harness only (no API keys needed — grades recorded golden artifacts)
python -m governance.evals.run_evals
# Prompt-drift check / update
python -m governance.prompt_registry            # verify
python -m governance.prompt_registry --update   # bump manifest after a reviewed change
```

## How it maps to regulation

- **21 CFR Part 11 / GxP data integrity** — audit trail (gateway), grounding,
  prompt version pinning, human e-signature linkage at HITL gates.
- **SR 11-7-style model risk** — prompt = part of the model; versioned, validated,
  monitored; eval harness is the ongoing performance check.
- **FDA/EMA good-AI principles (Jan 2026)** — defined context of use per agent,
  credibility controls proportional to risk, human accountability for decisions.
- **GVP / ICH E2B(R3)** — ICSR structural completeness checks in the eval harness.
