"""Unit tests for deterministic CVXPY quadratic portfolio optimizer."""
import numpy as np
import pytest
from engine.optimizer import optimize_portfolio, weights_to_trades
from models.portfolio import Position


def test_cvxpy_optimizer_basic_solve():
    """Verify solver reaches optimal status and weights sum to 1.0."""
    symbols = ["SPY", "AGG", "GLD", "CASH"]
    asset_classes = ["equities", "fixed_income", "commodities", "cash"]
    current_weights = np.array([0.70, 0.15, 0.10, 0.05])
    target_weights = np.array([0.50, 0.35, 0.05, 0.10])
    tax_costs = np.array([0.02, 0.00, 0.01, 0.00])

    asset_class_bounds = {
        "equities": (0.35, 0.55),
        "fixed_income": (0.25, 0.45),
        "commodities": (0.00, 0.10),
        "cash": (0.05, 0.20)
    }

    res = optimize_portfolio(
        current_weights=current_weights,
        target_weights=target_weights,
        tax_costs=tax_costs,
        symbols=symbols,
        asset_classes=asset_classes,
        asset_class_bounds=asset_class_bounds,
        max_position=0.60,
        turnover_limit=0.30
    )

    assert res["status"] == "optimal"
    assert np.isclose(np.sum(res["optimal_weights"]), 1.0, atol=1e-4)
    assert np.all(res["optimal_weights"] >= -1e-5)
    assert res["turnover"] <= 0.30 + 1e-4


def test_weights_to_trades_share_counts():
    """Verify weight deltas convert accurately into integer share orders."""
    symbols = ["SPY", "AGG", "CASH"]
    current_prices = {"SPY": 500.0, "AGG": 100.0, "CASH": 1.0}
    total_val = 100000.0

    positions = [
        Position(symbol="SPY", shares=140, cost_basis_per_share=450.0, current_price=500.0, holding_period_days=400, asset_class="equities"),
        Position(symbol="AGG", shares=200, cost_basis_per_share=100.0, current_price=100.0, holding_period_days=200, asset_class="fixed_income"),
        Position(symbol="CASH", shares=10000, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=50, asset_class="cash"),
    ]

    # Target: SPY 50% ($50k = 100 sh), AGG 40% ($40k = 400 sh), CASH 10% ($10k)
    optimal_weights = np.array([0.50, 0.40, 0.10])

    trades = weights_to_trades(
        current_positions=positions,
        optimal_weights=optimal_weights,
        total_portfolio_value=total_val,
        symbols=symbols,
        current_prices=current_prices,
        tax_bracket=0.32
    )

    trade_map = {t.symbol: t for t in trades}
    assert "SPY" in trade_map
    assert trade_map["SPY"].action == "SELL"
    assert trade_map["SPY"].shares == 40 # 140 - 100 = 40 to sell
    assert trade_map["SPY"].tax_impact >= 0.0

    assert "AGG" in trade_map
    assert trade_map["AGG"].action == "BUY"
    assert trade_map["AGG"].shares == 200 # 400 - 200 = 200 to buy
