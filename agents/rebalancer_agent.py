"""Agent 4: Tax-Aware Rebalancer Agent.

Invokes deterministic quadratic programming optimizer (CVXPY) and tax calculation engine
to translate target asset allocation and current portfolio holdings into exact, share-level
buy/sell trade recommendations with calculated tax impacts.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import config
from models.portfolio import Portfolio, Position, TradeOrder
from models.client_profile import ClientProfile
from engine.optimizer import optimize_portfolio, weights_to_trades
from engine.market_data import get_current_prices


class RebalancerAgent:
    """Quantitative Rebalancer agent driving mathematical portfolio optimization."""

    def __init__(self, agent_id: str = "sim_rebalancer_id"):
        self.agent_id = agent_id
        self.role = "Quantitative Portfolio Manager"

    def execute_rebalance(
        self,
        portfolio: Portfolio,
        target_allocation: Dict[str, float],
        profile: ClientProfile,
        use_mock_prices: bool = False,
    ) -> Tuple[List[TradeOrder], Dict[str, Any], str]:
        """
        Runs deterministic CVXPY quadratic optimization to achieve target allocation.

        Returns:
            Tuple of:
            - List of concrete TradeOrder objects
            - Optimization telemetry dictionary
            - Rationale narrative
        """
        symbols = [p.symbol for p in portfolio.positions]
        prices = get_current_prices(symbols, use_mock=use_mock_prices)

        # Update position current prices and re-evaluate portfolio
        for p in portfolio.positions:
            if p.symbol in prices:
                p.current_price = prices[p.symbol]
        portfolio.compute_fields()

        total_value = portfolio.total_value
        if total_value <= 0:
            return [], {"status": "error", "message": "Zero portfolio value"}, "Portfolio has zero value."

        current_weights = np.array([p.weight for p in portfolio.positions])
        asset_classes = [p.asset_class for p in portfolio.positions]

        # Target weights by symbol: distribute target asset class weight evenly across holdings in that class
        class_to_symbols = {}
        for p in portfolio.positions:
            class_to_symbols.setdefault(p.asset_class, []).append(p.symbol)

        target_weights = np.zeros(len(symbols))
        for i, p in enumerate(portfolio.positions):
            num_in_class = len(class_to_symbols[p.asset_class])
            target_class_w = target_allocation.get(p.asset_class, 0.0)
            target_weights[i] = target_class_w / num_in_class if num_in_class > 0 else 0.0

        # Construct asset class bounds
        risk_category = profile.risk_category or "moderate"
        alloc_ranges = config.DEFAULT_ALLOCATION_RANGES.get(
            risk_category, config.DEFAULT_ALLOCATION_RANGES["moderate"]
        )
        asset_class_bounds = {k: v for k, v in alloc_ranges.items()}

        # Estimate tax penalty vector (c_i) for selling positions with unrealized short-term gains
        tax_costs = np.zeros(len(symbols))
        tax_bracket = profile.ips.tax_bracket if profile.ips else 0.32
        for i, p in enumerate(portfolio.positions):
            if p.unrealized_gain_loss > 0:
                is_st = p.holding_period_days <= 365
                tax_costs[i] = (tax_bracket if is_st else 0.15) * 0.1

        max_pos = profile.ips.max_single_position_pct if profile.ips else config.DEFAULT_MAX_SINGLE_POSITION

        # Run CVXPY quadratic optimizer
        opt_result = optimize_portfolio(
            current_weights=current_weights,
            target_weights=target_weights,
            tax_costs=tax_costs,
            symbols=symbols,
            asset_classes=asset_classes,
            asset_class_bounds=asset_class_bounds,
            max_position=max_pos,
            turnover_limit=config.MAX_TURNOVER_PER_REBALANCE,
        )

        opt_weights = opt_result["optimal_weights"]

        # Convert optimal weights to concrete trade orders
        trades = weights_to_trades(
            current_positions=portfolio.positions,
            optimal_weights=opt_weights,
            total_portfolio_value=total_value,
            symbols=symbols,
            current_prices=prices,
            tax_bracket=tax_bracket,
        )

        total_buys = sum(t.estimated_value for t in trades if t.action == "BUY")
        total_sells = sum(t.estimated_value for t in trades if t.action == "SELL")
        total_tax = sum(t.tax_impact for t in trades)

        rationale = (
            f"Deterministic Quadratic Rebalancing completed with solver status: {opt_result['status']}.\n"
            f"Formulated {len(trades)} actionable trade orders: {sum(1 for t in trades if t.action == 'BUY')} BUYs "
            f"(${total_buys:,.2f}), {sum(1 for t in trades if t.action == 'SELL')} SELLs (${total_sells:,.2f}).\n"
            f"Portfolio turnover: {opt_result.get('turnover', 0.0):.1%}. Estimated net tax impact: ${total_tax:,.2f}.\n"
            f"Mathematical tracking error minimized to target bounds with active tax-drag mitigation."
        )

        return trades, opt_result, rationale
