"""Agent 2: Macro Market Analyst Agent.

Analyzes macroeconomic indicators, regime shifts (e.g., late-cycle inflation,
rate normalization), and derives tactical asset class tilts for strategic allocation.
"""
from typing import Dict, Any


class MacroAgent:
    """Macro Market Analyst assessing prevailing market regime and asset class tilts."""

    def __init__(self, agent_id: str = "sim_macro_id", agent_factory: Any = None):
        self.agent_id = agent_id
        self.role = "Chief Investment Strategist"
        self.factory = agent_factory

    def analyze_regime(self) -> Dict[str, Any]:
        """
        Assesses prevailing macro market regime and determines asset class outlook.
        
        Returns:
            Dict containing regime name, macro drivers, and asset class sentiment/tilts.
        """
        summary_override = None
        if self.factory:
            prompt = (
                "Provide a macro market regime analysis covering inflation trends, interest rate paths, "
                "equity factor valuations, and tactical asset class tilts across Equities, Fixed Income, "
                "Commodities, and Cash."
            )
            res = self.factory.chat_agent("macro", prompt)
            if res.get("status") == "SUCCESS" and res.get("text"):
                summary_override = f"[Lyzr Agent API: {res.get('agent_id')}] {res['text']}"

        default_summary = (
            "Macro environment exhibits late-cycle characteristics with decelerating inflation and firm growth. "
            "Recommends maintaining disciplined strategic asset weights with emphasis on high-quality core equities, "
            "attractive duration lock-in for fixed income, and a dedicated precious metals allocation for tail-risk hedging."
        )

        regime_data = {
            "regime": "Late-Cycle Disinflation & Policy Normalization",
            "drivers": [
                "Federal Reserve policy rate stabilization around neutral bands",
                "Moderating core CPI with resilient labor markets",
                "Elevated equity multiples warranting high-quality factor discipline",
                "Attractive real yields in intermediate Treasuries and investment grade corporate bonds"
            ],
            "asset_class_tilts": {
                "equities": "NEUTRAL / QUALITY_TILT (Focus on cash-flow generative large-cap and dividend growers)",
                "fixed_income": "OVERWEIGHT (Favorable duration profile in intermediate IG debt)",
                "commodities": "MODEST_OVERWEIGHT (Gold as structural geopolitical and currency debasement hedge)",
                "cash": "NEUTRAL (Preserve tactical liquidity buffer and dry powder)"
            },
            "summary": summary_override or default_summary
        }
        return regime_data
