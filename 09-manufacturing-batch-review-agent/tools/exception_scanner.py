# tools/exception_scanner.py
# ============================================================
# Review-by-exception scanner — the deterministic control at the heart of Agent 09.
#
# Given an electronic batch record (steps with measured params + limits + e-signatures)
# and LIMS QC results (result + spec limits), it surfaces ONLY what deviated:
#   * OOS               LIMS result outside its specification        -> CRITICAL
#   * OUT_OF_LIMIT      in-process parameter outside its limit       -> MAJOR
#   * MISSING_STEP      a required manufacturing step not recorded   -> CRITICAL
#   * UNSIGNED_RECORD   a critical step lacking an e-signature       -> CRITICAL
#   * UNSIGNED_STEP     a non-critical step lacking an e-signature   -> MINOR
#
# Deterministic and fully traceable: every exception names its source so the
# drafted report (and the QA reviewer) can verify it against the record.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List

CRITICAL = "CRITICAL"
MAJOR = "MAJOR"
MINOR = "MINOR"


def _num(v: Any):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def scan(batch_record: Dict[str, Any], lims_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    exceptions: List[Dict[str, Any]] = []

    # 1) LIMS QC results — out-of-specification is a critical exception.
    for r in lims_results or []:
        test = r.get("test", "unknown test")
        result = _num(r.get("result"))
        lo, hi = _num(r.get("lo")), _num(r.get("hi"))
        status = str(r.get("status", "")).upper()
        oos = status == "OOS"
        if result is not None and lo is not None and result < lo:
            oos = True
        if result is not None and hi is not None and result > hi:
            oos = True
        if oos:
            exceptions.append({
                "code": "OOS", "severity": CRITICAL, "step": test,
                "detail": f"QC result {r.get('result')} {r.get('unit','')} outside spec "
                          f"[{r.get('lo')}, {r.get('hi')}]".strip(),
                "source": "lims",
            })

    # 2) In-process steps — parameters, required steps, e-signatures.
    steps = batch_record.get("steps", []) or []
    recorded_ids = {s.get("id") for s in steps}
    for s in steps:
        name = s.get("name", s.get("id", "step"))
        val, lo, hi = _num(s.get("value")), _num(s.get("lo")), _num(s.get("hi"))
        critical = bool(s.get("critical"))
        if val is not None and ((lo is not None and val < lo) or (hi is not None and val > hi)):
            exceptions.append({
                "code": "OUT_OF_LIMIT", "severity": MAJOR, "step": name,
                "detail": f"parameter {s.get('value')} {s.get('unit','')} outside limit "
                          f"[{s.get('lo')}, {s.get('hi')}]".strip(),
                "source": "mes",
            })
        if not s.get("signed", False):
            exceptions.append({
                "code": "UNSIGNED_RECORD" if critical else "UNSIGNED_STEP",
                "severity": CRITICAL if critical else MINOR, "step": name,
                "detail": f"{'critical ' if critical else ''}step lacks an e-signature",
                "source": "mes",
            })

    # 3) Required steps that were never recorded.
    for req in batch_record.get("required_steps", []) or []:
        if req not in recorded_ids:
            exceptions.append({
                "code": "MISSING_STEP", "severity": CRITICAL, "step": req,
                "detail": f"required step {req!r} not present in the batch record",
                "source": "mes",
            })

    critical_count = sum(1 for e in exceptions if e["severity"] == CRITICAL)
    return {
        "exceptions": exceptions,
        "exception_count": len(exceptions),
        "critical_count": critical_count,
    }
