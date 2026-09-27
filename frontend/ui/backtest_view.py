"""UI Component: 2020-2024 Historical Backtest & Quantitative Verification."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from engine.backtester import run_portfolio_backtest


def render_backtest_view():
    """Renders the quantitative backtest analysis across 2020-2024 market cycle."""
    st.markdown("### 📈 2020–2024 Multi-Year Backtest: Governed Rebalancing vs. Unmanaged Drift")
    st.caption("Empirical proof of risk-managed tracking error, tail-risk drawdown protection, and cumulative tax drag.")

    # Interactive Parameters
    with st.expander("⚙️ Backtest Simulation Parameters", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            capital = st.number_input("Starting AUM ($)", min_value=10000.0, max_value=10000000.0, value=100000.0, step=25000.0)
        with c2:
            drift = st.slider("Rebalance Drift Band Threshold", min_value=0.02, max_value=0.10, value=0.05, step=0.01, format="%.2f")
        with c3:
            tax_rate = st.slider("Client Capital Gains Bracket", min_value=0.10, max_value=0.37, value=0.24, step=0.01, format="%.2f")

    # Run simulation
    res = run_portfolio_backtest(initial_capital=capital, drift_threshold=drift, tax_bracket=tax_rate)
    summary = res["summary"]
    df = res["timeseries"]

    # KPI Metric Cards
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Governed Final AUM", f"${summary['final_governed_value']:,.2f}", delta=f"{summary['total_governed_return']:+.1%}")
    k2.metric("Drifting Final AUM", f"${summary['final_drifting_value']:,.2f}", delta=f"{summary['total_drifting_return']:+.1%}")
    k3.metric("Max Drawdown (Gov)", f"{summary['max_drawdown_governed']:.1%}", delta=f"{summary['drawdown_protection_gain']:+.1%} Protection")
    k4.metric("Sharpe Ratio", f"{summary['sharpe_ratio_governed']:.2f}", delta=f"vs {summary['sharpe_ratio_drifting']:.2f} Unmanaged")
    k5.metric("Cumulative Tax Drag", f"${summary['cumulative_tax_drag']:,.2f}", f"{summary['total_rebalances_executed']} Rebalances")

    # Chart 1: Portfolio Growth Curves
    fig_val = go.Figure()
    fig_val.add_trace(go.Scatter(
        x=df["date"], y=df["governed_portfolio_value"],
        mode="lines+markers", name="Governed Rebalanced Portfolio",
        line=dict(color="#1E88E5", width=3),
    ))
    fig_val.add_trace(go.Scatter(
        x=df["date"], y=df["drifting_benchmark_value"],
        mode="lines", name="Unmanaged Drifting Benchmark",
        line=dict(color="#9E9E9E", width=2, dash="dash"),
    ))
    fig_val.update_layout(
        title="Portfolio Wealth Trajectory (2020–2024 Market Cycle)",
        yaxis=dict(title="Portfolio Value ($)", tickprefix="$"),
        xaxis=dict(title="Monthly Timeline"),
        height=360,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_val, use_container_width=True)

    # Chart 2: Tracking Error and Equity Drift
    c_left, c_right = st.columns(2)
    with c_left:
        fig_te = go.Figure()
        fig_te.add_trace(go.Scatter(
            x=df["date"], y=df["governed_tracking_error"],
            mode="lines", name="Governed Tracking Error (%)",
            line=dict(color="#43A047", width=2.5)
        ))
        fig_te.add_trace(go.Scatter(
            x=df["date"], y=df["drifting_tracking_error"],
            mode="lines", name="Drifting Tracking Error (%)",
            line=dict(color="#E53935", width=2, dash="dot")
        ))
        fig_te.update_layout(
            title="Tracking Error to Fiduciary Target (%)",
            yaxis=dict(title="Tracking Error (%)", ticksuffix="%"),
            height=300,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_te, use_container_width=True)

    with c_right:
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(
            x=df["date"], y=df["governed_equity_weight"],
            mode="lines", name="Governed Equity Weight (%)",
            line=dict(color="#1E88E5", width=2.5)
        ))
        fig_w.add_trace(go.Scatter(
            x=df["date"], y=df["drifting_equity_weight"],
            mode="lines", name="Drifting Equity Weight (%)",
            line=dict(color="#FB8C00", width=2, dash="dash")
        ))
        fig_w.add_hline(y=60.0, line_dash="dot", line_color="gray", annotation_text="60% Target")
        fig_w.update_layout(
            title="Equity Allocation Drift vs. Disciplined Cap (%)",
            yaxis=dict(title="Equity Exposure (%)", ticksuffix="%"),
            height=300,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_w, use_container_width=True)

    st.success(
        "💡 **Key Fiduciary Finding:** Governed rebalancing bounded tracking error to an average of "
        f"**{summary['avg_tracking_error_governed']:.1f}%** (vs **{summary['avg_tracking_error_drifting']:.1f}%** for unmanaged drift) "
        f"while protecting client capital from an unchecked equity run-up of **{summary['max_equity_drift_unmanaged']:.1f}%** prior to the 2022 market downturn."
    )
