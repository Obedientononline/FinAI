"""Agent 1: Fiduciary Profiler Agent.

Parses Investment Policy Statements (IPS) and Know Your Customer (KYC) records.
Applies deterministic mathematical scoring to derive client risk scores (1-10),
establishes fiduciary boundary constraints, and logs detailed rationale.
"""
from typing import Dict, Any, Tuple
from models.client_profile import ClientProfile
from engine.risk_scorer import compute_risk_score, get_scoring_explanation


class ProfilerAgent:
    """Fiduciary Profiler that evaluates client risk profiles and investment parameters."""

    def __init__(self, agent_id: str = "sim_profiler_id", agent_factory: Any = None):
        self.agent_id = agent_id
        self.role = "Certified Financial Planner (CFP)"
        self.factory = agent_factory

    def profile_client(self, profile: ClientProfile) -> Tuple[ClientProfile, Dict[str, Any], str]:
        """
        Profiles a client deterministically from KYC and IPS data.
        
        Returns:
            Tuple of:
            - Updated ClientProfile (with risk_score and risk_category set)
            - Scoring breakdown dict
            - Natural language fiduciary rationale
        """
        risk_score, risk_category, breakdown = compute_risk_score(profile.kyc, profile.ips)
        
        # Mutate/Update profile
        profile.risk_score = risk_score
        profile.risk_category = risk_category
        
        explanation = get_scoring_explanation(breakdown)
        
        # Check if live Lyzr Agent API inference is available
        llm_rationale = None
        if self.factory:
            prompt = (
                f"Analyze client IPS & KYC: Client {profile.name} (Age: {profile.kyc.age}), "
                f"Income ${profile.kyc.annual_income:,.0f}, Net Worth ${profile.kyc.net_worth:,.0f}, "
                f"Horizon {profile.ips.time_horizon_years}y, Liquidity: {profile.ips.liquidity_needs}. "
                f"Calculated mathematical score: {risk_score}/10 ({risk_category}). "
                f"Provide professional CFP fiduciary commentary."
            )
            res = self.factory.chat_agent("profiler", prompt)
            if res.get("status") == "SUCCESS" and res.get("text"):
                llm_rationale = f"[Lyzr Agent API: {res.get('agent_id')}]\n{res['text']}"

        default_rationale = (
            f"Fiduciary Assessment for {profile.name} (Client ID: {profile.client_id}):\n"
            f"Evaluated age ({profile.kyc.age}), time horizon ({profile.ips.time_horizon_years} yrs), "
            f"liquidity preference ({profile.ips.liquidity_needs}), and investment experience ({profile.kyc.investment_experience}).\n"
            f"Derived deterministic risk score {risk_score}/10 classifying the portfolio into '{risk_category}'.\n"
            f"IPS Restrictions noted: {', '.join(profile.ips.restrictions) if profile.ips.restrictions else 'None'}."
        )

        rationale = llm_rationale or default_rationale
        return profile, breakdown, rationale
