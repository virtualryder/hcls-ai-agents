"""HCLS governance — grounding, prompt registry, evals, HITL, redteam, fairness.

Governance is built into the platform from the first commit, not bolted on:

    grounding.py        deterministic claim-traceability check for regulated text
    prompt_registry.py  versioned, hash-pinned prompts (no silent prompt drift)
    prompt_manifest.json the pinned prompt versions CI holds the line behind
    evals/              structural + grounding eval harness over golden datasets
    tests/              HITL-gate enforcement + governance-core tests
    redteam/            prompt-injection / jailbreak resistance tests
    fairness/           access-equity / cohort-representativeness checks (RWE)

Every regulated artifact an agent produces (submission section, ICSR narrative,
CAPA plan, MSL brief) is graded by these checks before a human ever sees it, and
the same checks run in CI so a prompt or code change cannot silently degrade a
known-good output.
"""
