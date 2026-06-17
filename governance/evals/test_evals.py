"""CI entry point for the eval harness — golden artifacts must stay PASS."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from governance.evals.run_evals import run_all


def test_all_golden_cases_pass():
    results = run_all()
    assert results, "no eval cases discovered"
    failures = {r.case_id: r.failures for r in results if not r.passed}
    assert not failures, f"eval regressions: {failures}"
