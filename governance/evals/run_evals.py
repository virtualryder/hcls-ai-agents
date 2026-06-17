"""
LLM output evaluation harness for the HCLS suite.

Two eval families, both deterministic and CI-runnable WITHOUT API keys:

  STRUCTURAL  Does the artifact contain what the regulation/standard requires?
              (ICSR narrative: CIOMS/E2B who/what/when/seriousness/causality;
               regulatory submission section: purpose, data, benefit-risk,
               conclusion, and a traceable source reference.)
  GROUNDING   Is every number/entity in the artifact traceable to case state?
              (governance/grounding.py)

Golden datasets live in governance/evals/golden/*.json:
    {"cases": [{"id", "state": {...}, "artifact": "...", "expect": {...}}]}

Two run modes:
  pytest governance/evals            -> evaluates the RECORDED artifacts in the
                                        golden files (regression: did a prompt or
                                        code change degrade structure/grounding
                                        of known-good outputs?)
  python -m governance.evals.run_evals
                                     -> same checks, printed report + exit code.

Adding a case: capture a reviewed-and-approved production-quality output, append
it with its full input state, and let CI hold the line behind it.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from governance.grounding import verify_grounding  # noqa: E402

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

# ── PV ICSR narrative: CIOMS/E2B interrogatives + safety-specific elements ────
ICSR_REQUIRED_ELEMENTS = {
    "who": re.compile(r"\b(patient|subject|reporter|male|female|year[- ]old|age)\b", re.I),
    "what_product": re.compile(r"\b(drug|product|medication|dose|mg|administered|therapy|treatment)\b", re.I),
    "what_event": re.compile(r"\b(event|reaction|adverse|experienced|onset|symptom)\b", re.I),
    "when": re.compile(r"\b(20\d{2}|day|days|hour|onset|following|after|prior)\b", re.I),
    "seriousness": re.compile(r"\b(serious|non-serious|hospitali|life-threatening|death|disab|recover)\w*", re.I),
    "causality": re.compile(r"\b(related|causal|assess|suspect|dechallenge|rechallenge|plausib|unrelated)\w*", re.I),
}
PHI_IN_NARRATIVE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b(?:\d[ -]?){15,19}\b")

# ── Regulatory submission section: required structural anchors ─────────────────
REG_SECTION_REQUIRED = {
    "purpose": re.compile(r"\b(purpose|objective|scope|background|introduction)\b", re.I),
    "data": re.compile(r"\b(data|result|finding|study|analysis|evidence|cohort|endpoint)\b", re.I),
    "benefit_risk": re.compile(r"\b(benefit|risk|safety|efficacy|tolerab|favorable|unfavorable)\w*", re.I),
    "conclusion": re.compile(r"\b(conclu|therefore|in summary|overall|recommend|support)\w*", re.I),
}
# A compliant section must NOT contain unqualified promotional/off-label claims.
PROHIBITED_CLAIM_LANGUAGE = re.compile(
    r"\b(cure[sd]?|guarantee[sd]?|miracle|100% effective|completely safe|no side effects|best[- ]in[- ]class)\b",
    re.I,
)


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    failures: List[str] = field(default_factory=list)


def _grounding_failures(artifact: str, state: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    g = verify_grounding(artifact, state)
    out += [f"ungrounded number in artifact: {n}" for n in g.ungrounded_numbers]
    out += [f"ungrounded entity in artifact: {e}" for e in g.ungrounded_entities]
    return out


def eval_icsr_narrative(case: Dict[str, Any]) -> EvalResult:
    narrative: str = case["artifact"]
    failures: List[str] = []
    for element, pattern in ICSR_REQUIRED_ELEMENTS.items():
        if not pattern.search(narrative):
            failures.append(f"missing ICSR/CIOMS narrative element: {element}")
    if PHI_IN_NARRATIVE.search(narrative):
        failures.append("raw PHI (SSN/PAN) present in ICSR narrative")
    failures += _grounding_failures(narrative, case["state"])
    min_words = case.get("expect", {}).get("min_words", 60)
    if len(narrative.split()) < min_words:
        failures.append(f"narrative too thin: {len(narrative.split())} words < {min_words}")
    return EvalResult(case["id"], not failures, failures)


def eval_regulatory_section(case: Dict[str, Any]) -> EvalResult:
    section: str = case["artifact"]
    failures: List[str] = []
    for element, pattern in REG_SECTION_REQUIRED.items():
        if not pattern.search(section):
            failures.append(f"missing regulatory section element: {element}")
    if PROHIBITED_CLAIM_LANGUAGE.search(section):
        failures.append("prohibited promotional/off-label claim language in regulatory section")
    failures += _grounding_failures(section, case["state"])
    min_words = case.get("expect", {}).get("min_words", 60)
    if len(section.split()) < min_words:
        failures.append(f"section too thin: {len(section.split())} words < {min_words}")
    return EvalResult(case["id"], not failures, failures)


EVALUATORS = {
    "agent01_regulatory_sections": eval_regulatory_section,
    "agent02_icsr_narratives": eval_icsr_narrative,
}


def run_all() -> List[EvalResult]:
    results: List[EvalResult] = []
    for golden_file in sorted(GOLDEN_DIR.glob("*.json")):
        suite = json.loads(golden_file.read_text())
        evaluator = EVALUATORS[golden_file.stem]
        for case in suite["cases"]:
            results.append(evaluator(case))
    return results


if __name__ == "__main__":
    results = run_all()
    failed = [r for r in results if not r.passed]
    for r in results:
        print(("PASS" if r.passed else "FAIL"), r.case_id)
        for f in r.failures:
            print("   -", f)
    print(f"\n{len(results) - len(failed)}/{len(results)} eval cases passed")
    raise SystemExit(1 if failed else 0)
