"""
Reproducible generator for the Agent 02 scored golden set (Build B).

Produces governance/evals/golden/agent02_pv_scored.json: labeled FAERS-shaped
ICSR cases with gold labels (serious flag + criteria, suspect drugs, reactions,
outcomes) plus one duplicate pair and one near-miss non-duplicate. Gold labels
are the ground truth the scorers assert against; the openFDA connector's mapping
is the prediction. Grow the set by appending cases and re-running.

    python -m governance.evals.gen_golden_agent02
"""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "golden" / "agent02_pv_scored.json"

_SEX = {"M": "1", "F": "2"}
_OUTCOME = {"recovered": "1", "recovering": "2", "not_recovered": "3", "sequelae": "4", "fatal": "5", "unknown": "6"}
_SERIOUS_FLAG = {"death": "seriousnessdeath", "life": "seriousnesslifethreatening",
                 "hosp": "seriousnesshospitalization", "disab": "seriousnessdisabling",
                 "congen": "seriousnesscongenitalanomali", "other": "seriousnessother"}
_SERIOUS_LABEL = {"death": "Death", "life": "Life-threatening", "hosp": "Hospitalization",
                  "disab": "Disability", "congen": "Congenital anomaly", "other": "Other medically important condition"}
_OUT_LABEL = {"1": "Recovered/resolved", "2": "Recovering/resolving", "3": "Not recovered/not resolved",
              "4": "Recovered/resolved with sequelae", "5": "Fatal", "6": "Unknown"}


def faers(rid, serious, crit, sex, age, drugs, reactions, outcomes, country="US"):
    """drugs: [(name, characterization)]; reactions: [name]; outcomes: [key]"""
    rec = {"safetyreportid": rid, "serious": "1" if serious else "2",
           "receivedate": "20240101", "occurcountry": country,
           "patient": {"patientonsetage": str(age), "patientonsetageunit": "801", "patientsex": _SEX[sex],
                       "drug": [{"medicinalproduct": n, "drugcharacterization": ch} for n, ch in drugs],
                       "reaction": [{"reactionmeddrapt": rx, "reactionoutcome": _OUTCOME[o]}
                                    for rx, o in zip(reactions, outcomes)]}}
    for k in crit:
        rec["patient"] if False else rec.__setitem__(_SERIOUS_FLAG[k], "1")
    # gold labels (what a reviewer would confirm from the record)
    gold = {"serious": serious,
            "criteria": [_SERIOUS_LABEL[k] for k in crit],
            "drugs": [n for n, ch in drugs if ch == "1"],
            "reactions": list(reactions),
            "outcomes": sorted({_OUT_LABEL[_OUTCOME[o]] for o in outcomes})}
    return rid, rec, gold


CASES = []
def add(rid, serious, crit, sex, age, drugs, reactions, outcomes, country="US", **extra):
    _id, rec, gold = faers(rid, serious, crit, sex, age, drugs, reactions, outcomes, country)
    gold.update(extra)
    CASES.append({"id": _id, "faers": rec, "gold": gold})


# ── serious cases (varied criteria, single + multi drug) ─────────────────────
add("PV-0001", True, ["hosp"], "F", 67, [("METFORMIN", "1"), ("LISINOPRIL", "2")], ["Lactic acidosis", "Acute kidney injury"], ["recovered", "not_recovered"])
add("PV-0002", True, ["death"], "M", 71, [("WARFARIN", "1")], ["Gastrointestinal haemorrhage"], ["fatal"])
add("PV-0003", True, ["life", "hosp"], "F", 54, [("AMOXICILLIN", "1")], ["Anaphylactic reaction"], ["recovered"])
add("PV-0004", True, ["hosp"], "M", 60, [("ATORVASTATIN", "1")], ["Rhabdomyolysis"], ["recovering"])
add("PV-0005", True, ["disab"], "F", 45, [("METHOTREXATE", "1"), ("FOLIC ACID", "2")], ["Hepatic fibrosis"], ["not_recovered"])
add("PV-0006", True, ["other"], "M", 38, [("ISOTRETINOIN", "1")], ["Depression"], ["unknown"])
add("PV-0007", True, ["hosp", "life"], "F", 29, [("CLOZAPINE", "1")], ["Agranulocytosis"], ["recovered"])
add("PV-0008", True, ["congen"], "F", 31, [("VALPROATE", "1")], ["Foetal anticonvulsant syndrome"], ["unknown"])
add("PV-0009", True, ["death"], "M", 80, [("DIGOXIN", "1")], ["Cardiac arrest"], ["fatal"])
add("PV-0010", True, ["hosp"], "F", 52, [("INFLIXIMAB", "1")], ["Tuberculosis"], ["recovering"])
add("PV-0011", True, ["hosp"], "M", 66, [("METFORMIN", "1")], ["Lactic acidosis"], ["recovered"])   # dup of 0001 on drug+reaction

# ── non-serious cases ────────────────────────────────────────────────────────
add("PV-0012", False, [], "F", 40, [("IBUPROFEN", "1")], ["Nausea"], ["recovered"])
add("PV-0013", False, [], "M", 33, [("SERTRALINE", "1")], ["Headache"], ["recovering"])
add("PV-0014", False, [], "F", 27, [("LEVONORGESTREL", "1")], ["Irregular menstruation"], ["recovered"])
add("PV-0015", False, [], "M", 50, [("OMEPRAZOLE", "1")], ["Diarrhoea"], ["recovered"])
add("PV-0016", False, [], "F", 61, [("AMLODIPINE", "1")], ["Peripheral oedema"], ["not_recovered"])
add("PV-0017", False, [], "M", 22, [("CETIRIZINE", "1")], ["Somnolence"], ["recovered"])
add("PV-0018", False, [], "F", 48, [("METFORMIN", "1")], ["Dyspepsia"], ["recovered"])   # same drug as 0001 but different reaction -> NOT a dup
add("PV-0019", False, [], "M", 35, [("PARACETAMOL", "1")], ["Rash"], ["recovering"])
add("PV-0020", False, [], "F", 58, [("SIMVASTATIN", "1")], ["Myalgia"], ["recovered"])

# ── duplicate labels ─────────────────────────────────────────────────────────
# 0011 duplicates 0001 (shared suspect drug METFORMIN + reaction Lactic acidosis)
CASES[[c["id"] for c in CASES].index("PV-0011")]["gold"].update({"is_duplicate": True, "dup_of": "PV-0001"})
# 0018 is a near-miss (shares METFORMIN but different reaction) -> NOT a duplicate
CASES[[c["id"] for c in CASES].index("PV-0018")]["gold"].update({"is_duplicate": False, "dup_of": "PV-0001"})


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"cases": CASES}, indent=2), encoding="utf-8")
    print(f"wrote {len(CASES)} cases -> {OUT}")


if __name__ == "__main__":
    main()
