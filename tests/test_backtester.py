"""Unit tests for the 2020-2024 historical backtest harness."""
import pytest
from engine.backtester import run_portfolio_backtest


def test_portfolio_backtest_execution():
    """Verify historical backtest runs across 2020-2024 and produces valid time series."""
    res = run_portfolio_backtest(initial_capital=100000.0, drift_threshold=0.05)
    summary = res["summary"]
    df = res["timeseries"]

    assert len(df) >= 20
    assert summary["final_governed_value"] > 0
    assert summary["final_drifting_value"] > 0
    assert summary["total_rebalances_executed"] >= 1
    # Governed tracking error must be lower on average than unmanaged drifting
    assert summary["avg_tracking_error_governed"] < summary["avg_tracking_error_drifting"]
    assert summary["max_drawdown_governed"] <= 0
    assert summary["cumulative_tax_drag"] >= 0
    assert "date" in df.columns
    assert "governed_portfolio_value" in df.columns
