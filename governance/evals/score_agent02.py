"""
Scored eval runner for Agent 02 (Pharmacovigilance) — Build B.

Loads the labeled golden set, runs the real connector-mapping pipeline to produce
predictions, scores the regulatory-weighted metrics, gates against thresholds, and
writes an evidence report (eval-report.md + eval-report.json). Exit code is non-zero
if any threshold is missed — so CI holds the quality line.

    python -m governance.evals.score_agent02
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))

from governance.evals.scorers import score_dataset, gate, THRESHOLDS, LOWER_IS_BETTER  # noqa: E402

GOLDEN = _HERE / "golden" / "agent02_pv_scored.json"
REPORT_MD = _HERE / "eval-report.md"
REPORT_JSON = _HERE / "eval-report.json"


def _load():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]


def build_report(result, passed, failures) -> str:
    m = result["metrics"]
    rows = []
    for name, thr in THRESHOLDS.items():
        val = m.get(name, 0.0)
        op = "<=" if name in LOWER_IS_BETTER else ">="
        ok = (val <= thr) if name in LOWER_IS_BETTER else (val >= thr)
        rows.append(f"| {name} | {val} | {op} {thr} | {'PASS' if ok else 'FAIL'} |")
    conf = result["confusion"]["serious"]
    md = [
        "# Agent 02 (Pharmacovigilance) — scored eval report",
        "",
        f"**Result:** {'PASS' if passed else 'FAIL'} · **Cases:** {result['n_cases']} · "
        "Predictions from the real openFDA/FAERS connector mapping; grounding via "
        "`governance/grounding.py`; PHI-leak via the platform masker.",
        "",
        "| Metric | Value | Threshold | Status |",
        "|---|---|---|---|",
        *rows,
        "",
        f"**Seriousness confusion:** TP={conf['tp']} FP={conf['fp']} FN={conf['fn']} TN={conf['tn']} "
        "(recall is weighted highest — missing a serious case is the real-world harm).",
        "",
        "This report is the quality-evidence artifact for the assurance packet: it shows the "
        "agent's extraction/classification measured against a labeled safety benchmark with a "
        "**PHI-leak hard gate (= 0)**. Regenerate with `python -m governance.evals.score_agent02`.",
    ]
    if failures:
        md += ["", "## Threshold failures", *[f"- {f}" for f in failures]]
    return "\n".join(md) + "\n"


def main() -> int:
    cases = _load()
    result = score_dataset(cases)
    passed, failures = gate(result["metrics"])
    REPORT_JSON.write_text(json.dumps({"passed": passed, **result, "failures": failures}, indent=2), encoding="utf-8")
    REPORT_MD.write_text(build_report(result, passed, failures), encoding="utf-8")
    print(f"Agent 02 scored eval — {'PASS' if passed else 'FAIL'} ({result['n_cases']} cases)")
    for k, v in result["metrics"].items():
        print(f"  {k:22s} {v}")
    for f in failures:
        print("  FAIL:", f)
    print(f"report -> {REPORT_MD}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
