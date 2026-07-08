# Agent 02 (Pharmacovigilance) — scored eval report

**Result:** PASS · **Cases:** 20 · Predictions from the real openFDA/FAERS connector mapping; grounding via `governance/grounding.py`; PHI-leak via the platform masker.

| Metric | Value | Threshold | Status |
|---|---|---|---|
| seriousness_recall | 1.0 | >= 0.95 | PASS |
| seriousness_precision | 1.0 | >= 0.8 | PASS |
| entity_f1 | 1.0 | >= 0.85 | PASS |
| duplicate_accuracy | 1.0 | >= 0.9 | PASS |
| grounding_rate | 1.0 | >= 0.9 | PASS |
| phi_leak_rate | 0.0 | <= 0.0 | PASS |
| e2b_completeness | 1.0 | >= 0.95 | PASS |

**Seriousness confusion:** TP=11 FP=0 FN=0 TN=9 (recall is weighted highest — missing a serious case is the real-world harm).

This report is the quality-evidence artifact for the assurance packet: it shows the agent's extraction/classification measured against a labeled safety benchmark with a **PHI-leak hard gate (= 0)**. Regenerate with `python -m governance.evals.score_agent02`.
