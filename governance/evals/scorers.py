"""
Scored eval metrics for Agent 02 (Pharmacovigilance) — Build B.

Where run_evals.py answers "does the artifact pass structural + grounding checks?"
(binary, regression), this module answers "how GOOD is the agent, on a labeled
benchmark, against thresholds a Chief Safety/Quality Officer would set?"

The predictions are produced by the REAL ingestion pipeline — the openFDA/FAERS
connector mapping (OpenFDASafetyConnector._map_report) — so this scores actual
extraction/classification quality, not a stub. Grounding reuses
governance/grounding.py; PHI-leak reuses the platform masker's detector.

Metrics (aggregated over the golden set), with regulatory-weighted thresholds:
  seriousness_recall     >= 0.95   (missing a SERIOUS case is the real-world harm)
  seriousness_precision  >= 0.80
  entity_f1              >= 0.85   (drug / reaction / outcome extraction)
  duplicate_accuracy     >= 0.90
  grounding_rate         >= 0.90   (narrative claims traceable to the case)
  phi_leak_rate          == 0.00   (HARD GATE — any unmasked identifier fails)
  e2b_completeness       >= 0.95   (required ICSR fields present)
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "platform_core"))

from governance.grounding import verify_grounding                       # noqa: E402
from hcls_agent_platform.connectors.openfda import OpenFDASafetyConnector  # noqa: E402
from hcls_agent_platform.phi import mask                                # noqa: E402

THRESHOLDS: Dict[str, float] = {
    "seriousness_recall": 0.95,
    "seriousness_precision": 0.80,
    "entity_f1": 0.85,
    "duplicate_accuracy": 0.90,
    "grounding_rate": 0.90,
    "phi_leak_rate": 0.0,          # <= (hard gate: must be exactly 0)
    "e2b_completeness": 0.95,
}
# Direction: most metrics are "higher is better" (>=); phi_leak_rate is "<=".
LOWER_IS_BETTER = {"phi_leak_rate"}

# Required E2B(R3)/ICSR minimum fields (the "valid ICSR" four + reaction).
_E2B_REQUIRED = ["case_id", "suspect_drugs", "reactions", "serious", "narrative_text"]
_PHI = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|[\w.+-]+@[\w-]+\.[\w.]+")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def _set(xs: List[str]) -> Set[str]:
    return {_norm(x) for x in xs if x}


@dataclass
class CasePrediction:
    case_id: str
    serious: bool
    drugs: Set[str]
    reactions: Set[str]
    outcomes: Set[str]
    narrative: str
    record: Dict[str, Any]


def predict(faers_record: Dict[str, Any]) -> CasePrediction:
    """Run the REAL connector mapping to produce the agent's extraction."""
    rec = OpenFDASafetyConnector._map_report(faers_record)
    return CasePrediction(
        case_id=rec["case_id"],
        serious=bool(rec["serious"]),
        drugs=_set(rec["suspect_drugs"]) or _set(rec["all_drugs"]),
        reactions=_set(rec["reactions"]),
        outcomes=_set(rec["outcomes"]),
        narrative=rec["narrative_text"],
        record=rec,
    )


# ── individual metric helpers ────────────────────────────────────────────────

def _prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 1.0
    r = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


def score_dataset(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    cases: list of {"id", "faers": {...}, "gold": {serious, drugs, reactions,
           outcomes, is_duplicate?, dup_of?}}.  Returns metrics + per-case detail.
    """
    # seriousness confusion
    s_tp = s_fp = s_fn = s_tn = 0
    # entity micro-F1 accumulators
    e_tp = e_fp = e_fn = 0
    grounded = 0
    phi_leaks = 0
    completeness_scores: List[float] = []
    detail: List[Dict[str, Any]] = []

    preds: Dict[str, CasePrediction] = {}
    for c in cases:
        pred = predict(c["faers"])
        preds[c["id"]] = pred
        gold = c["gold"]

        # seriousness
        gs, ps = bool(gold["serious"]), pred.serious
        if gs and ps: s_tp += 1
        elif gs and not ps: s_fn += 1
        elif not gs and ps: s_fp += 1
        else: s_tn += 1

        # entities (drug/reaction/outcome as one micro-set)
        gold_ents = _set(gold.get("drugs", [])) | _set(gold.get("reactions", [])) | _set(gold.get("outcomes", []))
        pred_ents = pred.drugs | pred.reactions | pred.outcomes
        e_tp += len(gold_ents & pred_ents)
        e_fp += len(pred_ents - gold_ents)
        e_fn += len(gold_ents - pred_ents)

        # grounding on the composed narrative
        g = verify_grounding(pred.narrative, {**pred.record, **{"reactions": list(pred.reactions)}})
        is_grounded = not (g.ungrounded_numbers or g.ungrounded_entities)
        grounded += 1 if is_grounded else 0

        # PHI-leak: the emitted (masked) narrative must carry no identifier
        emitted = mask(pred.narrative)
        leaked = bool(_PHI.search(emitted))
        phi_leaks += 1 if leaked else 0

        # E2B completeness — a field is "present" if populated. Note: serious=False
        # is a VALID present value, so test presence (not None/""/[]), not truthiness.
        present = sum(1 for f in _E2B_REQUIRED if pred.record.get(f) not in (None, "", [], {}))
        completeness_scores.append(present / len(_E2B_REQUIRED))

        detail.append({"id": c["id"], "serious_gold": gs, "serious_pred": ps,
                       "grounded": is_grounded, "phi_leak": leaked})

    # duplicate detection: gold cases carry is_duplicate + dup_of; predict by
    # shared suspect drug + reaction between the case and its referenced pair.
    dup_correct = dup_total = 0
    by_id = {c["id"]: c for c in cases}
    for c in cases:
        if "is_duplicate" not in c["gold"]:
            continue
        dup_total += 1
        gold_dup = bool(c["gold"]["is_duplicate"])
        ref = c["gold"].get("dup_of")
        pred_dup = False
        if ref and ref in preds:
            a, b = preds[c["id"]], preds[ref]
            pred_dup = bool((a.drugs & b.drugs) and (a.reactions & b.reactions))
        if pred_dup == gold_dup:
            dup_correct += 1

    s_p, s_r, _ = _prf(s_tp, s_fp, s_fn)
    _, _, e_f1 = _prf(e_tp, e_fp, e_fn)
    n = len(cases)
    metrics = {
        "seriousness_recall": round(s_r, 4),
        "seriousness_precision": round(s_p, 4),
        "entity_f1": round(e_f1, 4),
        "duplicate_accuracy": round(dup_correct / dup_total, 4) if dup_total else 1.0,
        "grounding_rate": round(grounded / n, 4) if n else 1.0,
        "phi_leak_rate": round(phi_leaks / n, 4) if n else 0.0,
        "e2b_completeness": round(sum(completeness_scores) / n, 4) if n else 1.0,
    }
    return {"metrics": metrics, "n_cases": n, "detail": detail,
            "confusion": {"serious": {"tp": s_tp, "fp": s_fp, "fn": s_fn, "tn": s_tn}}}


def gate(metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Return (passed, failures) against THRESHOLDS."""
    failures: List[str] = []
    for name, thr in THRESHOLDS.items():
        val = metrics.get(name, 0.0)
        if name in LOWER_IS_BETTER:
            if val > thr:
                failures.append(f"{name}={val} exceeds max {thr}")
        elif val < thr:
            failures.append(f"{name}={val} below min {thr}")
    return (not failures), failures
