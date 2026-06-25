"""
Deterministic core for the Manufacturing Batch-Review native rebuild.

All non-LLM logic lives here so it can run in Lambdas, be unit-tested without a
model, and remain auditable under cGMP 21 CFR 211 / 21 CFR Part 11. Strands/
Bedrock only drafts the human-readable exception report; this module makes every
pass/fail and routing decision.

  scan()                 — review by exception: OOS / out-of-limit / missing step /
                           unsigned record (CRITICAL|MAJOR|MINOR)
  grounding_findings()   — numbers in the report must appear in the batch corpus
  required_elements()    — report must name batch, a recommendation, exceptions, closure
  route()                — RECOMMEND_RELEASE | RECOMMEND_HOLD | REVISE | ESCALATE

No model, no AWS dependencies.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

CRITICAL, MAJOR, MINOR = "CRITICAL", "MAJOR", "MINOR"


def _num(v: Any):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def scan(batch_record: Dict[str, Any], lims_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    exceptions: List[Dict[str, Any]] = []
    for r in lims_results or []:
        result, lo, hi = _num(r.get("result")), _num(r.get("lo")), _num(r.get("hi"))
        oos = str(r.get("status", "")).upper() == "OOS"
        if result is not None and lo is not None and result < lo:
            oos = True
        if result is not None and hi is not None and result > hi:
            oos = True
        if oos:
            exceptions.append({"code": "OOS", "severity": CRITICAL, "step": r.get("test", "QC test"),
                               "detail": f"QC result {r.get('result')} outside spec "
                                         f"[{r.get('lo')}, {r.get('hi')}]", "source": "lims"})
    steps = batch_record.get("steps", []) or []
    recorded = {s.get("id") for s in steps}
    for s in steps:
        name = s.get("name", s.get("id", "step"))
        val, lo, hi = _num(s.get("value")), _num(s.get("lo")), _num(s.get("hi"))
        crit = bool(s.get("critical"))
        if val is not None and ((lo is not None and val < lo) or (hi is not None and val > hi)):
            exceptions.append({"code": "OUT_OF_LIMIT", "severity": MAJOR, "step": name,
                               "detail": f"parameter {s.get('value')} outside limit "
                                         f"[{s.get('lo')}, {s.get('hi')}]", "source": "mes"})
        if not s.get("signed", False):
            exceptions.append({"code": "UNSIGNED_RECORD" if crit else "UNSIGNED_STEP",
                               "severity": CRITICAL if crit else MINOR, "step": name,
                               "detail": f"{'critical ' if crit else ''}step lacks an e-signature",
                               "source": "mes"})
    for req in batch_record.get("required_steps", []) or []:
        if req not in recorded:
            exceptions.append({"code": "MISSING_STEP", "severity": CRITICAL, "step": req,
                               "detail": f"required step {req!r} not present", "source": "mes"})
    critical = sum(1 for e in exceptions if e["severity"] == CRITICAL)
    return {"exceptions": exceptions, "exception_count": len(exceptions), "critical_count": critical}


_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")


def _flatten(obj: Any) -> List[Any]:
    if isinstance(obj, dict):
        out: List[Any] = []
        for v in obj.values():
            out += _flatten(v)
        return out
    if isinstance(obj, list):
        out = []
        for v in obj:
            out += _flatten(v)
        return out
    return [obj]


def grounding_findings(text: str, corpus: Dict[str, Any]) -> List[str]:
    corpus_nums = set(_NUM.findall(" ".join(str(v) for v in _flatten(corpus))))
    out: List[str] = []
    for tok in _NUM.findall(text):
        try:
            if float(tok) <= 12:
                continue
        except ValueError:
            continue
        if tok not in corpus_nums:
            out.append(f"ungrounded number: {tok}")
    return out


_REQUIRED = {
    "batch_identified": re.compile(r"\b(batch|lot)\b", re.I),
    "recommendation": re.compile(r"\b(recommendation|release|hold)\b", re.I),
    "exception_coverage": re.compile(
        r"\b(exception|OOS|out[- ]of[- ](spec|limit)|deviation|unsigned|missing|no exceptions)\b", re.I),
    "closure": re.compile(r"\b(QA sign[- ]off|no batch disposition|recommendation for QA|pending QA)\b", re.I),
}


def required_elements(text: str) -> List[str]:
    return [f"missing required report element: {k}" for k, p in _REQUIRED.items() if not p.search(text)]


def route(state: Dict[str, Any], report: str, revision_count: int) -> Dict[str, Any]:
    """Deterministic routing. CRITICAL exceptions escalate; quality issues revise (bounded);
    otherwise recommend release/hold and send to the QA gate."""
    corpus = {k: v for k, v in state.items() if k not in ("raw_batch_record",)}
    corpus["exceptions"] = state.get("exceptions", [])
    grnd = grounding_findings(report, corpus)
    missing = required_elements(report)

    if (grnd or missing) and revision_count < 1:
        return {"next": "Draft", "action": "REVISE", "grounding_findings": grnd,
                "missing_elements": missing, "reason": "quality issues; requesting revision"}
    if state.get("critical_count", 0) > 0:
        return {"next": "QAReviewGate", "action": "ESCALATE", "grounding_findings": grnd,
                "missing_elements": missing, "reason": "critical exception(s) — senior QA review"}
    action = "RECOMMEND_HOLD" if state.get("exception_count", 0) > 0 else "RECOMMEND_RELEASE"
    return {"next": "QAReviewGate", "action": action, "grounding_findings": grnd,
            "missing_elements": missing, "reason": "quality checks passed"}
