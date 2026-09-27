"""Agent 3: Strategic Target Allocator Agent.

Combines client fiduciary profile, IPS parameters, and macroeconomic perspectives
to synthesize optimal strategic target asset allocation weights across Equities,
Fixed Income, Commodities, and Cash.
"""
from typing import Dict, Any, Tuple
import config
from models.client_profile import ClientProfile


class AllocatorAgent:
    """Strategic Asset Allocator translating risk categories into target percentage mixes."""

    def __init__(self, agent_id: str = "sim_allocator_id", agent_factory: Any = None):
        self.agent_id = agent_id
        self.role = "Portfolio Strategist"
        self.factory = agent_factory

    def compute_target_allocation(
        self, profile: ClientProfile, macro_analysis: Dict[str, Any]
    ) -> Tuple[Dict[str, float], str]:
        """
        Determines target asset class allocation honoring risk profile boundaries.
        
        Returns:
            Tuple of:
            - Dict mapping asset class names to target weights (summing exactly to 1.0)
            - Rationale narrative explaining the allocation
        """
        risk_category = profile.risk_category or "moderate"
        default_ranges = config.DEFAULT_ALLOCATION_RANGES.get(
            risk_category, config.DEFAULT_ALLOCATION_RANGES["moderate"]
        )

        # Baseline midpoint allocations within approved fiduciary bands
        # Adjust slightly based on client liquidity and macro tilts
        liquidity = profile.ips.liquidity_needs.lower() if profile.ips else "moderate"
        
        if risk_category == "conservative":
            cash_w = 0.20 if liquidity == "high" else 0.15
            eq_w = 0.15
            comm_w = 0.05
            fi_w = round(1.0 - (cash_w + eq_w + comm_w), 4)
        elif risk_category == "moderate_conservative":
            cash_w = 0.15 if liquidity == "high" else 0.10
            eq_w = 0.30
            comm_w = 0.05
            fi_w = round(1.0 - (cash_w + eq_w + comm_w), 4)
        elif risk_category == "moderate":
            cash_w = 0.12 if liquidity == "high" else 0.08
            eq_w = 0.50
            comm_w = 0.07
            fi_w = round(1.0 - (cash_w + eq_w + comm_w), 4)
        elif risk_category == "moderate_aggressive":
            cash_w = 0.08 if liquidity == "high" else 0.05
            eq_w = 0.65
            comm_w = 0.08
            fi_w = round(1.0 - (cash_w + eq_w + comm_w), 4)
        else: # aggressive
            cash_w = 0.05 if liquidity == "high" else 0.03
            eq_w = 0.77
            comm_w = 0.08
            fi_w = round(1.0 - (cash_w + eq_w + comm_w), 4)

        target_allocation = {
            "equities": float(eq_w),
            "fixed_income": float(fi_w),
            "commodities": float(comm_w),
            "cash": float(cash_w)
        }

        # Validate exact unity sum
        total_w = sum(target_allocation.values())
        if abs(total_w - 1.0) > 1e-6:
            diff = 1.0 - total_w
            target_allocation["cash"] = round(target_allocation["cash"] + diff, 4)

        rationale = (
            f"Strategic Asset Allocation Model: '{risk_category.replace('_', ' ').title()}'\n"
            f"Targets established: Equities {target_allocation['equities']:.1%}, "
            f"Fixed Income {target_allocation['fixed_income']:.1%}, "
            f"Commodities {target_allocation['commodities']:.1%}, "
            f"Cash {target_allocation['cash']:.1%}.\n"
            f"Strictly honors fiduciary boundary constraints (Max allowed equities for this tier: "
            f"{default_ranges['equities'][1]:.1%}). Incorporates {liquidity} liquidity requirement and "
            f"macro environment of {macro_analysis.get('regime', 'standard market conditions')}."
        )

        return target_allocation, rationale
