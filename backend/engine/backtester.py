"""Historical Backtest Engine for Governed Portfolio Rebalancing.

Simulates multi-asset model portfolios across the 2020-2024 market cycle
(including COVID crash, 2021 bull market, and 2022 inflation rate-hikes).
Quantifies tracking error reduction, risk-adjusted returns, and cumulative tax drag.
"""
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from engine.optimizer import optimize_portfolio


CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "historical_prices.json")


def load_historical_prices() -> Dict[str, Dict[str, float]]:
    """Loads cached monthly prices for 2020-2024."""
    if not os.path.exists(CACHE_PATH):
        from data.create_price_cache import generate_historical_price_cache
        generate_historical_price_cache()

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_portfolio_backtest(
    initial_capital: float = 100000.0,
    target_weights: Optional[Dict[str, float]] = None,
    drift_threshold: float = 0.05,
    tax_bracket: float = 0.24,
) -> Dict[str, Any]:
    """
    Executes a monthly backtest from 2020 through 2024 comparing:
    1. Governed Rebalanced Portfolio (CVXPY QP optimization with 5% drift threshold)
    2. Drifting Benchmark Portfolio (unrebalanced buy-and-hold)
    """
    history = load_historical_prices()
    dates = sorted(history.keys())

    if target_weights is None:
        target_weights = {"SPY": 0.60, "AGG": 0.30, "GLD": 0.10}

    symbols = list(target_weights.keys())
    asset_classes = ["equities" if s in ["SPY", "QQQ"] else ("fixed_income" if s == "AGG" else "commodities") for s in symbols]
    targ_w_vec = np.array([target_weights[s] for s in symbols])

    # Initial allocations
    initial_prices = history[dates[0]]
    rebal_shares = {s: (initial_capital * target_weights[s]) / initial_prices[s] for s in symbols}
    rebal_cost_basis = {s: initial_prices[s] for s in symbols}

    drift_shares = dict(rebal_shares)

    rebal_cash = 0.0
    cum_tax_drag = 0.0
    total_rebalances = 0

    timeline = []

    for d_idx, dt in enumerate(dates):
        current_prices = history[dt]

        # Calculate values before rebalance
        rebal_asset_val = sum(rebal_shares[s] * current_prices[s] for s in symbols)
        rebal_total_val = rebal_asset_val + rebal_cash

        drift_total_val = sum(drift_shares[s] * current_prices[s] for s in symbols)

        # Current weights for governed portfolio
        curr_weights = np.array([(rebal_shares[s] * current_prices[s]) / rebal_total_val for s in symbols])

        # Tracking error from target
        tracking_error = float(np.sqrt(np.sum((curr_weights - targ_w_vec) ** 2)))
        drift_w = np.array([(drift_shares[s] * current_prices[s]) / drift_total_val for s in symbols])
        drift_tracking_error = float(np.sqrt(np.sum((drift_w - targ_w_vec) ** 2)))

        rebalance_triggered = False
        rebalance_turnover = 0.0
        tax_incurred = 0.0

        # Check if maximum asset drift exceeds threshold
        max_drift = np.max(np.abs(curr_weights - targ_w_vec))
        if max_drift >= drift_threshold and d_idx > 0:
            rebalance_triggered = True
            total_rebalances += 1

            # Estimate tax cost vector
            tax_costs = np.zeros(len(symbols))
            for i, s in enumerate(symbols):
                gain = current_prices[s] - rebal_cost_basis[s]
                if gain > 0:
                    tax_costs[i] = tax_bracket * 0.15

            opt_res = optimize_portfolio(
                current_weights=curr_weights,
                target_weights=targ_w_vec,
                tax_costs=tax_costs,
                symbols=symbols,
                asset_classes=asset_classes,
                asset_class_bounds={
                    "equities": (0.45, 0.70),
                    "fixed_income": (0.20, 0.40),
                    "commodities": (0.05, 0.15)
                },
                max_position=0.70,
                turnover_limit=0.25
            )

            opt_w = opt_res["optimal_weights"]
            rebalance_turnover = opt_res["turnover"]

            # Execute rebalancing trades & compute realized tax
            for i, s in enumerate(symbols):
                target_val_s = opt_w[i] * rebal_total_val
                current_val_s = rebal_shares[s] * current_prices[s]
                val_diff = target_val_s - current_val_s

                if val_diff < 0: # SELL
                    shares_sold = abs(val_diff) / current_prices[s]
                    gain_per_share = current_prices[s] - rebal_cost_basis[s]
                    if gain_per_share > 0:
                        tax_on_trade = (shares_sold * gain_per_share) * tax_bracket
                        tax_incurred += tax_on_trade
                    rebal_shares[s] -= shares_sold
                elif val_diff > 0: # BUY
                    shares_bought = val_diff / current_prices[s]
                    # Update blended cost basis
                    old_cost = rebal_shares[s] * rebal_cost_basis[s]
                    new_cost = shares_bought * current_prices[s]
                    rebal_shares[s] += shares_bought
                    rebal_cost_basis[s] = (old_cost + new_cost) / rebal_shares[s]

            cum_tax_drag += tax_incurred
            rebal_total_val -= tax_incurred
            # Reset current weights after rebalance
            curr_weights = np.array([(rebal_shares[s] * current_prices[s]) / rebal_total_val for s in symbols])
            tracking_error = float(np.sqrt(np.sum((curr_weights - targ_w_vec) ** 2)))

        timeline.append({
            "date": dt,
            "governed_portfolio_value": round(rebal_total_val, 2),
            "drifting_benchmark_value": round(drift_total_val, 2),
            "governed_tracking_error": round(tracking_error * 100, 2),
            "drifting_tracking_error": round(drift_tracking_error * 100, 2),
            "rebalance_triggered": rebalance_triggered,
            "rebalance_turnover": round(rebalance_turnover * 100, 2),
            "tax_incurred": round(tax_incurred, 2),
            "cumulative_tax_drag": round(cum_tax_drag, 2),
            "governed_equity_weight": round(curr_weights[0] * 100, 1),
            "drifting_equity_weight": round(drift_w[0] * 100, 1),
        })

    df = pd.DataFrame(timeline)

    # Performance Analytics
    df["gov_return"] = df["governed_portfolio_value"].pct_change().fillna(0)
    df["drift_return"] = df["drifting_benchmark_value"].pct_change().fillna(0)

    # Maximum Drawdown
    gov_peak = df["governed_portfolio_value"].cummax()
    gov_dd = (df["governed_portfolio_value"] - gov_peak) / gov_peak
    max_gov_dd = float(gov_dd.min())

    drift_peak = df["drifting_benchmark_value"].cummax()
    drift_dd = (df["drifting_benchmark_value"] - drift_peak) / drift_peak
    max_drift_dd = float(drift_dd.min())

    total_gov_ret = (df["governed_portfolio_value"].iloc[-1] - initial_capital) / initial_capital
    total_drift_ret = (df["drifting_benchmark_value"].iloc[-1] - initial_capital) / initial_capital

    ann_gov_vol = float(df["gov_return"].std() * np.sqrt(12))
    ann_drift_vol = float(df["drift_return"].std() * np.sqrt(12))

    sharpe_gov = (total_gov_ret / 5.0 - 0.02) / (ann_gov_vol if ann_gov_vol > 0 else 1.0)
    sharpe_drift = (total_drift_ret / 5.0 - 0.02) / (ann_drift_vol if ann_drift_vol > 0 else 1.0)

    summary = {
        "initial_capital": initial_capital,
        "final_governed_value": df["governed_portfolio_value"].iloc[-1],
        "final_drifting_value": df["drifting_benchmark_value"].iloc[-1],
        "total_governed_return": total_gov_ret,
        "total_drifting_return": total_drift_ret,
        "max_drawdown_governed": max_gov_dd,
        "max_drawdown_drifting": max_drift_dd,
        "drawdown_protection_gain": abs(max_drift_dd) - abs(max_gov_dd),
        "annualized_governed_volatility": ann_gov_vol,
        "annualized_drifting_volatility": ann_drift_vol,
        "sharpe_ratio_governed": round(sharpe_gov, 2),
        "sharpe_ratio_drifting": round(sharpe_drift, 2),
        "cumulative_tax_drag": cum_tax_drag,
        "total_rebalances_executed": total_rebalances,
        "avg_tracking_error_governed": float(df["governed_tracking_error"].mean()),
        "avg_tracking_error_drifting": float(df["drifting_tracking_error"].mean()),
        "max_equity_drift_unmanaged": float(df["drifting_equity_weight"].max()),
    }

    return {"summary": summary, "timeseries": df}
