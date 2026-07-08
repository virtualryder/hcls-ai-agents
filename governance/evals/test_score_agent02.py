"""
CI gate for the Agent 02 scored eval (Build B) + negative controls.

The positive tests hold the quality line on the golden set. The negative controls
prove the gate has TEETH — that the scorers actually catch a missed-serious case,
an ungrounded narrative, and a PHI identifier — so a green run means something.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))
sys.path.insert(0, str(_HERE.parent.parent / "platform_core"))

from governance.evals.scorers import score_dataset, gate, THRESHOLDS, _PHI  # noqa: E402
from governance.grounding import verify_grounding                          # noqa: E402

GOLDEN = _HERE / "golden" / "agent02_pv_scored.json"


def _cases():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]


# ── positive: the benchmark passes every threshold ───────────────────────────

def test_scored_eval_meets_all_thresholds():
    result = score_dataset(_cases())
    passed, failures = gate(result["metrics"])
    assert passed, f"threshold failures: {failures}"


def test_phi_leak_hard_gate_is_zero():
    result = score_dataset(_cases())
    assert result["metrics"]["phi_leak_rate"] == 0.0


def test_seriousness_recall_meets_regulatory_bar():
    m = score_dataset(_cases())["metrics"]
    assert m["seriousness_recall"] >= THRESHOLDS["seriousness_recall"]


# ── negative controls: the gate must FAIL on bad data ────────────────────────

def test_gate_catches_a_missed_serious_case():
    # Same case, but the FAERS record marks it non-serious while gold says serious
    # -> a false negative on the seriousness classifier -> recall must drop below 1.
    cases = _cases()
    poisoned = json.loads(json.dumps(cases[0]))
    poisoned["id"] = "PV-POISON"
    poisoned["faers"]["serious"] = "2"          # predict() will read False
    poisoned["gold"]["serious"] = True          # but the truth is serious
    result = score_dataset([poisoned])
    passed, _ = gate(result["metrics"])
    assert result["metrics"]["seriousness_recall"] < 1.0
    assert not passed                            # the gate rejects it


def test_grounding_scorer_flags_an_ungrounded_number():
    # A narrative asserting a value absent from the case state must be flagged.
    g = verify_grounding("The patient received 999 mg and the QT interval was 640 ms.",
                         {"suspect_drugs": ["METFORMIN"], "reactions": ["Lactic acidosis"]})
    assert g.ungrounded_numbers, "grounding scorer failed to flag an ungrounded number"


def test_phi_detector_catches_identifiers():
    assert _PHI.search("reporter jane.doe@example.com SSN 123-45-6789")
    assert not _PHI.search("A female patient, age 67 year, from US.")
