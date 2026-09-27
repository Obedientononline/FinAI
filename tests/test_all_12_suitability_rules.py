"""Comprehensive 24-point test suite for all 12 FINRA Suitability & Lyzr Safe AI Guardrails.
Verifies both the PASS condition and the FAIL/VETO condition for each individual rule.
"""
import pytest
from datetime import datetime, timezone
from models.client_profile import ClientProfile, IPS, KYC
from models.portfolio import TradeOrder
from models.proposal import TradeProposal, SuitabilityReport
from guardrails.suitability_rules import (
    check_equity_cap,
    check_equity_floor,
    check_cash_buffer,
    check_concentration,
    check_blocked_assets,
    check_horizon_match,
    check_age_guard,
    check_ips_restrictions,
    check_turnover_limit,
    check_tax_efficiency,
    check_diversification,
    check_wash_sale,
)


def create_mock_context(
    age=40,
    risk_score=5,
    risk_category="moderate",
    horizon=15,
    liquidity="low",
    restrictions=None,
    net_worth=1000000.0,
    target_alloc=None,
    trades=None,
    max_single_pos=0.10,
    tax_impact=0.0
):
    profile = ClientProfile(
        client_id="C-TEST",
        name="Test Client",
        risk_score=risk_score,
        risk_category=risk_category,
        kyc=KYC(age=age, annual_income=200000, net_worth=net_worth, investment_experience="experienced", employment_status="Employed", dependents=1),
        ips=IPS(
            investment_objective="growth_and_income",
            risk_tolerance="moderate",
            time_horizon_years=horizon,
            liquidity_needs=liquidity,
            tax_bracket=0.28,
            restrictions=restrictions or [],
            max_single_position_pct=max_single_pos,
            rebalance_threshold_pct=0.05
        )
    )
    proposal = TradeProposal(
        proposal_id="PROP-TEST",
        client_id="C-TEST",
        timestamp=datetime.now(timezone.utc),
        risk_score=risk_score,
        risk_category=risk_category,
        current_allocation={"equities": 0.50, "fixed_income": 0.35, "commodities": 0.05, "cash": 0.10},
        target_allocation=target_alloc or {"equities": 0.50, "fixed_income": 0.35, "commodities": 0.05, "cash": 0.10},
        trades=trades or [],
        suitability_report=SuitabilityReport(checks=[]),
        market_analysis="Neutral market",
        allocation_rationale="Balanced"
    )
    proposal.net_tax_impact = tax_impact
    return profile, proposal


# 1. Rule 1: FINRA-001 Equity Cap
def test_rule_01_equity_cap_pass():
    prof, prop = create_mock_context(risk_score=2, target_alloc={"equities": 0.18, "cash": 0.15})
    res = check_equity_cap(prof, prop)
    assert res.passed is True
    assert res.status == "PASS"

def test_rule_01_equity_cap_fail():
    prof, prop = create_mock_context(risk_score=2, target_alloc={"equities": 0.45, "cash": 0.15}) # 45% > 20% limit
    res = check_equity_cap(prof, prop)
    assert res.passed is False
    assert res.severity == "critical"


# 2. Rule 2: FINRA-002 Equity Floor
def test_rule_02_equity_floor_pass():
    prof, prop = create_mock_context(risk_score=9, target_alloc={"equities": 0.75, "cash": 0.05})
    res = check_equity_floor(prof, prop)
    assert res.passed is True

def test_rule_02_equity_floor_fail():
    prof, prop = create_mock_context(risk_score=9, target_alloc={"equities": 0.30, "cash": 0.20}) # 30% < 50% min
    res = check_equity_floor(prof, prop)
    assert res.passed is False
    assert res.severity == "warning"


# 3. Rule 3: FINRA-003 Cash Buffer
def test_rule_03_cash_buffer_pass():
    prof, prop = create_mock_context(liquidity="high", target_alloc={"equities": 0.20, "cash": 0.18}) # >= 15%
    res = check_cash_buffer(prof, prop)
    assert res.passed is True

def test_rule_03_cash_buffer_fail():
    prof, prop = create_mock_context(liquidity="high", target_alloc={"equities": 0.20, "cash": 0.03}) # 3% < 15%
    res = check_cash_buffer(prof, prop)
    assert res.passed is False
    assert res.severity == "critical"


# 4. Rule 4: FINRA-004 Concentration Limit
def test_rule_04_concentration_pass():
    trade = TradeOrder(symbol="SPY", action="BUY", shares=10, estimated_price=500, estimated_value=5000, asset_class="equities", target_weight=0.08)
    prof, prop = create_mock_context(trades=[trade], max_single_pos=0.10)
    res = check_concentration(prof, prop)
    assert res.passed is True

def test_rule_04_concentration_fail():
    trade = TradeOrder(symbol="AAPL", action="BUY", shares=500, estimated_price=200, estimated_value=100000, asset_class="equities", target_weight=0.28)
    prof, prop = create_mock_context(trades=[trade], max_single_pos=0.10)
    res = check_concentration(prof, prop)
    assert res.passed is False


# 5. Rule 5: FINRA-005 Blocked Assets
def test_rule_05_blocked_assets_pass():
    trade = TradeOrder(symbol="SPY", action="BUY", shares=20, estimated_price=500, estimated_value=10000, asset_class="equities")
    prof, prop = create_mock_context(trades=[trade])
    res = check_blocked_assets(prof, prop)
    assert res.passed is True

def test_rule_05_blocked_assets_fail():
    trade = TradeOrder(symbol="DOGE", action="BUY", shares=50000, estimated_price=0.12, estimated_value=6000, asset_class="equities")
    prof, prop = create_mock_context(trades=[trade])
    res = check_blocked_assets(prof, prop)
    assert res.passed is False
    assert "DOGE" in res.details


# 6. Rule 6: FINRA-006 Horizon Match
def test_rule_06_horizon_match_pass():
    prof, prop = create_mock_context(horizon=2, target_alloc={"equities": 0.25, "cash": 0.20}) # 25% <= 30% limit
    res = check_horizon_match(prof, prop)
    assert res.passed is True

def test_rule_06_horizon_match_fail():
    prof, prop = create_mock_context(horizon=2, target_alloc={"equities": 0.55, "cash": 0.10}) # 55% > 30% limit
    res = check_horizon_match(prof, prop)
    assert res.passed is False


# 7. Rule 7: FINRA-007 Senior Investor Safeguard
def test_rule_07_age_guard_pass():
    prof, prop = create_mock_context(age=73, target_alloc={"equities": 0.35, "cash": 0.15}) # 35% <= 40% cap
    res = check_age_guard(prof, prop)
    assert res.passed is True

def test_rule_07_age_guard_fail():
    prof, prop = create_mock_context(age=73, target_alloc={"equities": 0.65, "cash": 0.10}) # 65% > 40% cap
    res = check_age_guard(prof, prop)
    assert res.passed is False
    assert res.severity == "critical"


# 8. Rule 8: FINRA-008 IPS Negative Screening
def test_rule_08_ips_restrictions_pass():
    trade = TradeOrder(symbol="BND", action="BUY", shares=100, estimated_price=75, estimated_value=7500, asset_class="fixed_income")
    prof, prop = create_mock_context(restrictions=["no_tobacco"], trades=[trade])
    res = check_ips_restrictions(prof, prop)
    assert res.passed is True

def test_rule_08_ips_restrictions_fail():
    trade = TradeOrder(symbol="MO", action="BUY", shares=200, estimated_price=45, estimated_value=9000, asset_class="equities")
    prof, prop = create_mock_context(restrictions=["no_tobacco"], trades=[trade])
    res = check_ips_restrictions(prof, prop)
    assert res.passed is False
    assert "MO" in res.details


# 9. Rule 9: FINRA-009 Turnover Limit
def test_rule_09_turnover_limit_pass():
    trade = TradeOrder(symbol="AGG", action="BUY", shares=100, estimated_price=100, estimated_value=10000, asset_class="fixed_income")
    prof, prop = create_mock_context(net_worth=1000000.0, trades=[trade])
    res = check_turnover_limit(prof, prop)
    assert res.passed is True

def test_rule_09_turnover_limit_fail():
    trade1 = TradeOrder(symbol="SPY", action="BUY", shares=600, estimated_price=500, estimated_value=300000, asset_class="equities")
    prof, prop = create_mock_context(net_worth=500000.0, trades=[trade1]) # $300k / $500k = 60% > 25% limit
    res = check_turnover_limit(prof, prop)
    assert res.passed is False
    assert res.severity == "warning"


# 10. Rule 10: FINRA-010 Tax Efficiency
def test_rule_10_tax_efficiency_pass():
    prof, prop = create_mock_context(tax_impact=1200.0) # $1.2k <= $5k threshold
    res = check_tax_efficiency(prof, prop)
    assert res.passed is True

def test_rule_10_tax_efficiency_fail():
    prof, prop = create_mock_context(tax_impact=14500.0) # $14.5k > $5k threshold
    res = check_tax_efficiency(prof, prop)
    assert res.passed is False
    assert res.severity == "warning"


# 11. Rule 11: FINRA-011 Multi-Asset Diversification
def test_rule_11_diversification_pass():
    # 4 asset classes present for > $500k AUM
    prof, prop = create_mock_context(net_worth=1200000.0, target_alloc={"equities": 0.50, "fixed_income": 0.30, "commodities": 0.10, "cash": 0.10})
    res = check_diversification(prof, prop)
    assert res.passed is True

def test_rule_11_diversification_fail():
    # Only 1 asset class present for > $500k AUM
    prof, prop = create_mock_context(net_worth=1200000.0, target_alloc={"equities": 1.0, "fixed_income": 0.0, "commodities": 0.0, "cash": 0.0})
    res = check_diversification(prof, prop)
    assert res.passed is False


# 12. Rule 12: FINRA-012 Wash Sale Avoidance
def test_rule_12_wash_sale_pass():
    trade1 = TradeOrder(symbol="SPY", action="BUY", shares=50, estimated_price=500, estimated_value=25000, asset_class="equities")
    trade2 = TradeOrder(symbol="AGG", action="SELL", shares=100, estimated_price=100, estimated_value=10000, asset_class="fixed_income")
    prof, prop = create_mock_context(trades=[trade1, trade2])
    res = check_wash_sale(prof, prop)
    assert res.passed is True

def test_rule_12_wash_sale_fail():
    # Same symbol bought and sold in proposal
    trade1 = TradeOrder(symbol="VWO", action="BUY", shares=100, estimated_price=44, estimated_value=4400, asset_class="equities")
    trade2 = TradeOrder(symbol="VWO", action="SELL", shares=50, estimated_price=44, estimated_value=2200, asset_class="equities")
    prof, prop = create_mock_context(trades=[trade1, trade2])
    res = check_wash_sale(prof, prop)
    assert res.passed is False
    assert "VWO" in res.details
