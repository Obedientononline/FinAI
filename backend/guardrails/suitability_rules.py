"""FINRA Suitability Rule Engine.

12 deterministic rules that enforce Investment Policy Statement (IPS) compliance
and FINRA Regulation Best Interest (Reg BI) suitability requirements.

All rules are hard-coded, deterministic, and auditable — no LLM involvement.
"""
import json
import os
from typing import List, Dict, Any

from models.client_profile import ClientProfile
from models.proposal import TradeProposal, SuitabilityCheck, SuitabilityReport

try:
    from config import *
except ImportError:
    pass

# Load blocked assets
_BLOCKED_ASSETS_PATH = os.path.join(os.path.dirname(__file__), "blocked_assets.json")
try:
    with open(_BLOCKED_ASSETS_PATH, "r") as f:
        BLOCKED_ASSETS = json.load(f)
except Exception:
    BLOCKED_ASSETS = {}


def check_all_suitability(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityReport:
    """Run all 12 suitability checks and return a comprehensive report."""
    checks = [
        check_equity_cap(profile, proposal),
        check_equity_floor(profile, proposal),
        check_cash_buffer(profile, proposal),
        check_concentration(profile, proposal),
        check_blocked_assets(profile, proposal),
        check_horizon_match(profile, proposal),
        check_age_guard(profile, proposal),
        check_ips_restrictions(profile, proposal),
        check_turnover_limit(profile, proposal),
        check_tax_efficiency(profile, proposal),
        check_diversification(profile, proposal),
        check_wash_sale(profile, proposal),
    ]
    return SuitabilityReport(checks=checks)


def check_equity_cap(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 1: FINRA-001 Equity Cap"""
    risk_score = getattr(profile, "risk_score", 5)
    target_equities = proposal.target_allocation.get("equities", 0.0)
    
    if risk_score <= 3:
        max_eq = 0.20
    elif risk_score == 4:
        max_eq = 0.35
    elif risk_score <= 6:
        max_eq = 0.55
    elif risk_score == 7:
        max_eq = 0.70
    else:
        max_eq = 0.90
        
    passed = target_equities <= max_eq
    return SuitabilityCheck(
        rule_id="FINRA-001",
        rule_name="Equity Cap",
        passed=passed,
        severity="critical",
        details=f"Target equities {target_equities:.1%} vs Max {max_eq:.1%} for risk score {risk_score}."
    )


def check_equity_floor(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 2: FINRA-002 Equity Floor"""
    risk_score = getattr(profile, "risk_score", 5)
    target_equities = proposal.target_allocation.get("equities", 0.0)
    
    min_eq = 0.0
    if risk_score >= 8:
        min_eq = 0.50
    elif risk_score == 7:
        min_eq = 0.40
        
    passed = target_equities >= min_eq
    return SuitabilityCheck(
        rule_id="FINRA-002",
        rule_name="Equity Floor",
        passed=passed,
        severity="warning",
        details=f"Target equities {target_equities:.1%} vs Min {min_eq:.1%} for risk score {risk_score}."
    )


def check_cash_buffer(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 3: FINRA-003 Cash Buffer"""
    liquidity_needs = profile.ips.liquidity_needs.lower() if profile.ips else "moderate"
    target_cash = proposal.target_allocation.get("cash", 0.0)
    
    if liquidity_needs == "high":
        min_cash = 0.15
    elif liquidity_needs == "low":
        min_cash = 0.02
    else:
        min_cash = 0.07
        
    passed = target_cash >= min_cash
    return SuitabilityCheck(
        rule_id="FINRA-003",
        rule_name="Cash Buffer",
        passed=passed,
        severity="critical",
        details=f"Target cash {target_cash:.1%} vs Min {min_cash:.1%} for {liquidity_needs} liquidity needs."
    )


def check_concentration(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 4: FINRA-004 Concentration Limit"""
    ips = getattr(profile, "ips", None)
    max_single_position_pct = getattr(ips, "max_single_position_pct", 0.10) if ips else 0.10
    
    passed = True
    failed_symbols = []
    
    for trade in proposal.trades:
        w_val = getattr(trade, "target_weight", None)
        if w_val is None:
            w_val = getattr(trade, "post_weight", 0.0)
        weight = float(w_val) if w_val is not None else 0.0
        if weight > max_single_position_pct:
            passed = False
            failed_symbols.append(getattr(trade, "symbol", "UNKNOWN"))
            
    return SuitabilityCheck(
        rule_id="FINRA-004",
        rule_name="Concentration Limit",
        passed=passed,
        severity="critical",
        details=f"Positions exceeding {max_single_position_pct:.1%}: {failed_symbols}" if not passed else f"All positions <= {max_single_position_pct:.1%}."
    )


def check_blocked_assets(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 5: FINRA-005 Blocked Assets"""
    all_blocked = set()
    for cat, assets in BLOCKED_ASSETS.items():
        all_blocked.update(assets)
        
    passed = True
    violating_trades = []
    
    for trade in proposal.trades:
        sym = getattr(trade, "symbol", "UNKNOWN")
        if sym in all_blocked:
            passed = False
            violating_trades.append(sym)
            
    return SuitabilityCheck(
        rule_id="FINRA-005",
        rule_name="Blocked Assets",
        passed=passed,
        severity="critical",
        details=f"Found blocked assets: {violating_trades}" if not passed else "No blocked assets found."
    )


def check_horizon_match(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 6: FINRA-006 Horizon Match"""
    horizon = profile.ips.time_horizon_years if profile.ips else 10
    target_equities = proposal.target_allocation.get("equities", 0.0)
    
    if horizon < 3:
        max_eq = 0.30
    elif horizon <= 10:
        max_eq = 0.60
    else:
        max_eq = 1.0
        
    passed = target_equities <= max_eq
    return SuitabilityCheck(
        rule_id="FINRA-006",
        rule_name="Horizon Match",
        passed=passed,
        severity="critical",
        details=f"Target equities {target_equities:.1%} vs Max {max_eq:.1%} for {horizon}y horizon."
    )


def check_age_guard(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 7: FINRA-007 Age Guard"""
    age = profile.kyc.age if profile.kyc else 40
    target_equities = proposal.target_allocation.get("equities", 0.0)
    
    if age >= 70:
        max_eq = 0.40
        severity = "critical"
    elif age >= 65:
        max_eq = 0.55
        severity = "critical"
    elif age >= 60:
        max_eq = 0.65
        severity = "warning"
    else:
        max_eq = 1.0
        severity = "warning"
        
    passed = target_equities <= max_eq
    
    return SuitabilityCheck(
        rule_id="FINRA-007",
        rule_name="Age Guard",
        passed=passed,
        severity=severity,
        details=f"Target equities {target_equities:.1%} vs Max {max_eq:.1%} for age {age}."
    )


def check_ips_restrictions(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 8: FINRA-008 IPS Restrictions"""
    ips = getattr(profile, "ips", None)
    restrictions = getattr(ips, "restrictions", []) if ips else []
    restricted_symbols = set()
    
    if "no_tobacco" in restrictions:
        restricted_symbols.update(BLOCKED_ASSETS.get("tobacco_securities", []))
    if "no_firearms" in restrictions:
        restricted_symbols.update(BLOCKED_ASSETS.get("firearms_securities", []))
        
    passed = True
    violating_trades = []
    
    for trade in proposal.trades:
        sym = getattr(trade, "symbol", "UNKNOWN")
        if sym in restricted_symbols:
            passed = False
            violating_trades.append(sym)
            
    return SuitabilityCheck(
        rule_id="FINRA-008",
        rule_name="IPS Restrictions",
        passed=passed,
        severity="critical",
        details=f"Trades violating IPS restrictions: {violating_trades}" if not passed else "No IPS violations."
    )


def check_turnover_limit(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 9: FINRA-009 Turnover Limit"""
    total_turnover = proposal.total_buy_value + proposal.total_sell_value
    # Estimate AUM from net worth as proxy; in production use actual portfolio value
    aum = profile.kyc.net_worth if profile.kyc else 0.0
    
    turnover_ratio = (total_turnover / aum) if aum > 0 else 0.0
    passed = turnover_ratio <= 0.25
    
    return SuitabilityCheck(
        rule_id="FINRA-009",
        rule_name="Turnover Limit",
        passed=passed,
        severity="warning",
        details=f"Turnover ratio {turnover_ratio:.1%} vs Max 25.0%."
    )


def check_tax_efficiency(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 10: FINRA-010 Tax Efficiency"""
    # Use net_tax_impact from proposal (sum of all trade tax_impacts)
    st_gains = proposal.net_tax_impact if proposal.net_tax_impact > 0 else 0.0
        
    passed = st_gains <= 5000.0
    
    return SuitabilityCheck(
        rule_id="FINRA-010",
        rule_name="Tax Efficiency",
        passed=passed,
        severity="warning",
        details=f"Estimated tax impact ${st_gains:,.2f} vs threshold $5,000.00."
    )


def check_diversification(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 11: FINRA-011 Diversification"""
    aum = profile.kyc.net_worth if profile.kyc else 0.0
    if aum <= 500000:
        return SuitabilityCheck(
            rule_id="FINRA-011",
            rule_name="Diversification",
            passed=True,
            severity="warning",
            details="AUM <= $500K, skipped."
        )
        
    num_asset_classes = sum(1 for w in proposal.target_allocation.values() if w > 0.0)
    passed = num_asset_classes >= 4
    
    return SuitabilityCheck(
        rule_id="FINRA-011",
        rule_name="Diversification",
        passed=passed,
        severity="warning",
        details=f"Asset classes: {num_asset_classes} vs Min 4."
    )


def check_wash_sale(profile: ClientProfile, proposal: TradeProposal) -> SuitabilityCheck:
    """Rule 12: FINRA-012 Wash Sale"""
    buys = set(getattr(t, "symbol", "UNKNOWN") for t in proposal.trades if getattr(t, "action", "").lower() == "buy")
    sells = set(getattr(t, "symbol", "UNKNOWN") for t in proposal.trades if getattr(t, "action", "").lower() == "sell")
    
    wash_sales = buys.intersection(sells)
    passed = len(wash_sales) == 0
    
    return SuitabilityCheck(
        rule_id="FINRA-012",
        rule_name="Wash Sale",
        passed=passed,
        severity="critical",
        details=f"Potential wash sales detected: {list(wash_sales)}" if not passed else "No wash sale risk detected in proposal."
    )
