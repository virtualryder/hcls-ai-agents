"""
Fairness: cohort representativeness for RWE / site & patient matching.

When agents propose trial-eligible cohorts or rank sites, a biased cohort is both
an ethical and a regulatory problem (FDA Diversity Action Plan expectations; equity
of access to research). This check is a deterministic, reviewable guardrail: it
compares a proposed cohort's demographic mix against a reference population and
flags material under-representation for human review. It does not auto-correct —
epidemiologists and medical leaders decide.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def representativeness_gaps(cohort_mix, reference_mix, tolerance=0.10):
    """
    cohort_mix / reference_mix: {group: proportion}. Returns groups whose cohort
    proportion is more than `tolerance` (absolute) below the reference.
    """
    gaps = {}
    for group, ref in reference_mix.items():
        got = cohort_mix.get(group, 0.0)
        if ref - got > tolerance:
            gaps[group] = round(ref - got, 4)
    return gaps


def test_flags_material_underrepresentation():
    reference = {"white": 0.60, "black": 0.13, "hispanic": 0.19, "asian": 0.06}
    cohort = {"white": 0.88, "black": 0.02, "hispanic": 0.05, "asian": 0.05}
    gaps = representativeness_gaps(cohort, reference)
    assert "black" in gaps and "hispanic" in gaps


def test_representative_cohort_has_no_gaps():
    reference = {"white": 0.60, "black": 0.13, "hispanic": 0.19, "asian": 0.06}
    cohort = {"white": 0.58, "black": 0.15, "hispanic": 0.20, "asian": 0.07}
    assert representativeness_gaps(cohort, reference) == {}
