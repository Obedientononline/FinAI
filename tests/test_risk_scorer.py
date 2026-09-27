"""Unit tests for deterministic risk scoring engine."""
import pytest
from models.client_profile import KYC, IPS
from engine.risk_scorer import compute_risk_score, get_scoring_explanation


def test_conservative_client_scoring():
    """Verify senior conservative client receives a low risk score (1-3)."""
    kyc = KYC(
        age=75,
        annual_income=60000.0,
        net_worth=800000.0,
        investment_experience="limited",
        employment_status="Retired",
        dependents=0
    )
    ips = IPS(
        investment_objective="capital_preservation",
        risk_tolerance="conservative",
        time_horizon_years=3,
        liquidity_needs="high",
        tax_bracket=0.22,
        restrictions=["no_tobacco"],
        max_single_position_pct=0.08,
        rebalance_threshold_pct=0.05
    )

    score, category, breakdown = compute_risk_score(kyc, ips)
    assert 1 <= score <= 3
    assert category == "conservative"
    assert "age_factor" in breakdown
    assert len(get_scoring_explanation(breakdown)) > 0


def test_aggressive_client_scoring():
    """Verify young aggressive executive receives a high risk score (8-10)."""
    kyc = KYC(
        age=28,
        annual_income=350000.0,
        net_worth=1200000.0,
        investment_experience="sophisticated",
        employment_status="Employed",
        dependents=0
    )
    ips = IPS(
        investment_objective="growth",
        risk_tolerance="aggressive",
        time_horizon_years=30,
        liquidity_needs="low",
        tax_bracket=0.35,
        restrictions=[],
        max_single_position_pct=0.15,
        rebalance_threshold_pct=0.05
    )

    score, category, breakdown = compute_risk_score(kyc, ips)
    assert 8 <= score <= 10
    assert category == "aggressive"


def test_moderate_client_scoring():
    """Verify middle-aged moderate investor receives moderate tier (5-6)."""
    kyc = KYC(
        age=45,
        annual_income=180000.0,
        net_worth=1500000.0,
        investment_experience="experienced",
        employment_status="Employed",
        dependents=2
    )
    ips = IPS(
        investment_objective="growth_and_income",
        risk_tolerance="moderate",
        time_horizon_years=15,
        liquidity_needs="moderate",
        tax_bracket=0.24,
        restrictions=[],
        max_single_position_pct=0.10,
        rebalance_threshold_pct=0.05
    )

    score, category, breakdown = compute_risk_score(kyc, ips)
    assert 4 <= score <= 6
    assert category in ["moderate", "moderate_conservative"]
