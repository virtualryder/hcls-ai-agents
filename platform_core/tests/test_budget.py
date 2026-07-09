"""Budget meter (AGP FinOps clause): hard cap denies before spend; soft cap warns; alerts fire."""
import pytest

from hcls_agent_platform.budget import BudgetMeter


def test_hard_cap_denies_over_budget_before_spend():
    m = BudgetMeter("02-pharmacovigilance", "PV", monthly_token_cap=1000, cap_behavior="hard")
    m.commit(900)
    d = m.preflight(500)
    assert d.allowed is False and "budget_exceeded" in d.reason
    # preflight does not mutate the meter
    assert m.used == 900


def test_under_budget_allowed():
    m = BudgetMeter("a", "d", monthly_token_cap=1000)
    assert m.preflight(100).allowed is True


def test_soft_cap_allows_with_throttle_signal():
    m = BudgetMeter("a", "d", monthly_token_cap=100, cap_behavior="soft")
    m.commit(90)
    d = m.preflight(50)
    assert d.allowed is True and d.throttled is True


def test_alerts_fire_once():
    m = BudgetMeter("a", "d", monthly_token_cap=100, alert_thresholds=[0.6, 0.85, 1.0])
    assert 0.6 in m.commit(60)
    assert 0.6 not in m.commit(10)      # already fired
    assert 0.85 in _flatten(m, 20)


def _flatten(m, n):
    return m.commit(n)


def test_invalid_cap_rejected():
    with pytest.raises(ValueError):
        BudgetMeter("a", "d", monthly_token_cap=0)
