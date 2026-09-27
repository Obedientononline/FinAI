"""Unit tests for FINRA suitability rule engine and Lyzr Safe AI guardrails."""
import pytest
from datetime import datetime
from models.client_profile import ClientProfile, IPS, KYC
from models.portfolio import TradeOrder
from models.proposal import TradeProposal, SuitabilityReport
from guardrails.suitability_rules import (
    check_equity_cap,
    check_blocked_assets,
    check_cash_buffer,
    check_ips_restrictions,
    check_all_suitability
)


@pytest.fixture
def conservative_profile():
    return ClientProfile(
        client_id="C-TEST-001",
        name="Test Senior",
        risk_score=2,
        risk_category="conservative",
        kyc=KYC(age=74, annual_income=50000, net_worth=600000, investment_experience="limited", employment_status="Retired", dependents=0),
        ips=IPS(
            investment_objective="capital_preservation",
            risk_tolerance="conservative",
            time_horizon_years=3,
            liquidity_needs="high",
            tax_bracket=0.22,
            restrictions=["no_tobacco"],
            max_single_position_pct=0.10,
            rebalance_threshold_pct=0.05
        )
    )


def test_equity_cap_blocks_excessive_equities_for_conservative(conservative_profile):
    """Verify Rule 1: FINRA-001 blocks conservative client exceeding 20% equity."""
    proposal = TradeProposal(
        proposal_id="P-TEST-1",
        client_id=conservative_profile.client_id,
        timestamp=datetime.utcnow(),
        risk_score=conservative_profile.risk_score,
        risk_category=conservative_profile.risk_category,
        current_allocation={"equities": 0.60, "fixed_income": 0.30, "commodities": 0.05, "cash": 0.05},
        target_allocation={"equities": 0.50, "fixed_income": 0.35, "commodities": 0.05, "cash": 0.10}, # 50% > 20% max
        trades=[],
        suitability_report=SuitabilityReport(checks=[]),
        market_analysis="",
        allocation_rationale=""
    )

    check = check_equity_cap(conservative_profile, proposal)
    assert not check.passed
    assert check.severity == "critical"
    assert "FINRA-001" in check.rule_id


def test_blocked_assets_filter(conservative_profile):
    """Verify Rule 5: FINRA-005 blocks meme coins and speculative assets."""
    proposal = TradeProposal(
        proposal_id="P-TEST-2",
        client_id=conservative_profile.client_id,
        timestamp=datetime.utcnow(),
        risk_score=conservative_profile.risk_score,
        risk_category=conservative_profile.risk_category,
        current_allocation={"equities": 0.15, "fixed_income": 0.65, "commodities": 0.05, "cash": 0.15},
        target_allocation={"equities": 0.15, "fixed_income": 0.65, "commodities": 0.05, "cash": 0.15},
        trades=[
            TradeOrder(symbol="DOGE", action="BUY", shares=50000, estimated_price=0.12, estimated_value=6000, asset_class="equities")
        ],
        suitability_report=SuitabilityReport(checks=[]),
        market_analysis="",
        allocation_rationale=""
    )

    check = check_blocked_assets(conservative_profile, proposal)
    assert not check.passed
    assert "DOGE" in check.details


def test_ips_restrictions_filter(conservative_profile):
    """Verify Rule 8: FINRA-008 blocks assets restricted by client IPS (e.g. tobacco)."""
    proposal = TradeProposal(
        proposal_id="P-TEST-3",
        client_id=conservative_profile.client_id,
        timestamp=datetime.utcnow(),
        risk_score=conservative_profile.risk_score,
        risk_category=conservative_profile.risk_category,
        current_allocation={"equities": 0.15, "fixed_income": 0.65, "commodities": 0.05, "cash": 0.15},
        target_allocation={"equities": 0.15, "fixed_income": 0.65, "commodities": 0.05, "cash": 0.15},
        trades=[
            TradeOrder(symbol="MO", action="BUY", shares=100, estimated_price=45.0, estimated_value=4500, asset_class="equities")
        ],
        suitability_report=SuitabilityReport(checks=[]),
        market_analysis="",
        allocation_rationale=""
    )

    check = check_ips_restrictions(conservative_profile, proposal)
    assert not check.passed
    assert "MO" in check.details


def test_full_suitability_report_execution(conservative_profile):
    """Verify all 12 suitability checks run and compile into a valid SuitabilityReport."""
    proposal = TradeProposal(
        proposal_id="P-TEST-4",
        client_id=conservative_profile.client_id,
        timestamp=datetime.utcnow(),
        risk_score=conservative_profile.risk_score,
        risk_category=conservative_profile.risk_category,
        current_allocation={"equities": 0.15, "fixed_income": 0.65, "commodities": 0.05, "cash": 0.15},
        target_allocation={"equities": 0.15, "fixed_income": 0.65, "commodities": 0.05, "cash": 0.15},
        trades=[
            TradeOrder(symbol="AGG", action="BUY", shares=50, estimated_price=100.0, estimated_value=5000, asset_class="fixed_income")
        ],
        suitability_report=SuitabilityReport(checks=[]),
        market_analysis="",
        allocation_rationale=""
    )

    report = check_all_suitability(conservative_profile, proposal)
    assert len(report.checks) == 12
    assert report.all_passed
    assert len(report.critical_failures) == 0
