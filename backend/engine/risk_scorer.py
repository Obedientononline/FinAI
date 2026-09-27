"""Deterministic risk scoring engine.

Computes a risk score (1-10) from KYC and IPS data using a transparent,
auditable formula. No LLM involvement — pure deterministic math.
"""

from typing import Dict, Tuple, Any

def compute_risk_score(kyc: Dict[str, Any], ips: Dict[str, Any]) -> Tuple[int, str, Dict[str, float]]:
    """
    Returns (risk_score, risk_category, scoring_breakdown)
    
    Scoring rubric (10 points max):
    - Age factor: 0-2 pts (younger = higher risk capacity)
      age <= 30: 2.0, 31-40: 1.7, 41-50: 1.4, 51-60: 1.0, 61-70: 0.5, 70+: 0.2
    
    - Income/Net Worth factor: 0-2 pts (higher ratio = more capacity)
      income/networth >= 0.2: 2.0, >= 0.15: 1.5, >= 0.10: 1.0, < 0.10: 0.5
    
    - Time horizon factor: 0-2 pts
      >= 20yr: 2.0, 15-19: 1.7, 10-14: 1.3, 5-9: 0.8, < 5: 0.3
    
    - Stated risk tolerance: 0-2 pts (direct mapping)
      aggressive: 2.0, moderate_aggressive: 1.6, moderate: 1.2, 
      moderate_conservative: 0.7, conservative: 0.3
    
    - Investment experience: 0-1 pt
      sophisticated: 1.0, experienced: 0.7, limited: 0.4, none: 0.1
    
    - Liquidity needs: 0-1 pt (lower needs = more risk capacity)
      low: 1.0, moderate: 0.5, high: 0.1
    """
    if hasattr(kyc, "model_dump"):
        kyc = kyc.model_dump()
    elif not isinstance(kyc, dict):
        kyc = getattr(kyc, "__dict__", {})

    if hasattr(ips, "model_dump"):
        ips = ips.model_dump()
    elif not isinstance(ips, dict):
        ips = getattr(ips, "__dict__", {})

    breakdown = {}
    
    # 1. Age Factor
    age = kyc.get('age', 50)
    if age <= 30:
        age_score = 2.0
    elif age <= 40:
        age_score = 1.7
    elif age <= 50:
        age_score = 1.4
    elif age <= 60:
        age_score = 1.0
    elif age <= 70:
        age_score = 0.5
    else:
        age_score = 0.2
    breakdown['age_factor'] = age_score
    
    # 2. Income/Net Worth Factor
    income = kyc.get('annual_income', 0)
    net_worth = kyc.get('net_worth', 1)  # avoid division by zero
    if net_worth <= 0:
        ratio = 0
    else:
        ratio = income / net_worth
    
    if ratio >= 0.2:
        ratio_score = 2.0
    elif ratio >= 0.15:
        ratio_score = 1.5
    elif ratio >= 0.10:
        ratio_score = 1.0
    else:
        ratio_score = 0.5
    breakdown['income_net_worth_factor'] = ratio_score
    
    # 3. Time Horizon Factor
    horizon = ips.get('time_horizon_years', 10)
    if horizon >= 20:
        horizon_score = 2.0
    elif horizon >= 15:
        horizon_score = 1.7
    elif horizon >= 10:
        horizon_score = 1.3
    elif horizon >= 5:
        horizon_score = 0.8
    else:
        horizon_score = 0.3
    breakdown['time_horizon_factor'] = horizon_score
    
    # 4. Stated Risk Tolerance
    tolerance_map = {
        'aggressive': 2.0,
        'moderate_aggressive': 1.6,
        'moderate': 1.2,
        'moderate_conservative': 0.7,
        'conservative': 0.3
    }
    tolerance = ips.get('risk_tolerance', 'moderate')
    tolerance_score = tolerance_map.get(tolerance, 1.2)
    breakdown['stated_risk_tolerance'] = tolerance_score
    
    # 5. Investment Experience
    experience_map = {
        'sophisticated': 1.0,
        'experienced': 0.7,
        'limited': 0.4,
        'none': 0.1
    }
    experience = kyc.get('investment_experience', 'limited')
    experience_score = experience_map.get(experience, 0.4)
    breakdown['investment_experience'] = experience_score
    
    # 6. Liquidity Needs
    liquidity_map = {
        'low': 1.0,
        'moderate': 0.5,
        'high': 0.1
    }
    liquidity = ips.get('liquidity_needs', 'moderate')
    liquidity_score = liquidity_map.get(liquidity, 0.5)
    breakdown['liquidity_needs'] = liquidity_score
    
    total_score_float = sum(breakdown.values())
    
    # Round to nearest integer 1-10
    risk_score = int(round(total_score_float))
    risk_score = max(1, min(10, risk_score))
    
    # Category mapping: 1-3=conservative, 4=moderate_conservative, 
    # 5-6=moderate, 7=moderate_aggressive, 8-10=aggressive
    if risk_score <= 3:
        category = 'conservative'
    elif risk_score == 4:
        category = 'moderate_conservative'
    elif risk_score <= 6:
        category = 'moderate'
    elif risk_score == 7:
        category = 'moderate_aggressive'
    else:
        category = 'aggressive'
        
    return risk_score, category, breakdown


def get_scoring_explanation(breakdown: Dict[str, float]) -> str:
    """Returns a human-readable explanation of how the score was derived."""
    lines = ["Risk Score Breakdown:"]
    lines.append(f"- Age factor: {breakdown.get('age_factor', 0)} pts")
    lines.append(f"- Income-to-Net Worth: {breakdown.get('income_net_worth_factor', 0)} pts")
    lines.append(f"- Time horizon: {breakdown.get('time_horizon_factor', 0)} pts")
    lines.append(f"- Stated risk tolerance: {breakdown.get('stated_risk_tolerance', 0)} pts")
    lines.append(f"- Investment experience: {breakdown.get('investment_experience', 0)} pts")
    lines.append(f"- Liquidity needs: {breakdown.get('liquidity_needs', 0)} pts")
    
    total = sum(breakdown.values())
    lines.append(f"Total float score: {total:.2f}")
    
    return "\n".join(lines)
