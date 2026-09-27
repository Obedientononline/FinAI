"""UI Component: Current Portfolio Dashboard & Drift Diagnostics."""
import streamlit as st
import pandas as pd
import plotly.express as px
from models.portfolio import Portfolio


def render_dashboard(portfolio: Portfolio, pipeline):
    """Renders the existing portfolio metrics and visual breakdown."""
    st.markdown("### 📊 Existing Portfolio Holdings & Asset Allocation")
    st.caption("Live portfolio telemetry, cost-basis diagnostics, and asset class distributions.")

    # High level KPIs
    total_val = portfolio.total_value
    unrealized_total = sum(p.unrealized_gain_loss for p in portfolio.positions)
    pct_gain = (unrealized_total / (total_val - unrealized_total)) if (total_val - unrealized_total) > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Portfolio AUM", f"${total_val:,.2f}")
    k2.metric("Unrealized Capital P&L", f"${unrealized_total:,.2f}", delta=f"{pct_gain:+.2%}")
    k3.metric("Number of Positions", len(portfolio.positions))
    k4.metric("Asset Classes", len([k for k, v in portfolio.allocation.items() if v > 0]))

    c_chart, c_table = st.columns([1, 2])

    with c_chart:
        alloc_data = [
            {"Asset Class": k.replace("_", " ").title(), "Weight": v, "Value": v * total_val}
            for k, v in portfolio.allocation.items()
        ]
        df_alloc = pd.DataFrame(alloc_data)

        fig = px.pie(
            df_alloc,
            names="Asset Class",
            values="Weight",
            hole=0.45,
            color="Asset Class",
            color_discrete_map={
                "Equities": "#1E88E5",
                "Fixed Income": "#43A047",
                "Commodities": "#FB8C00",
                "Cash": "#7E57C2"
            }
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

    with c_table:
        holdings_data = []
        for p in portfolio.positions:
            holdings_data.append({
                "Symbol": p.symbol,
                "Class": p.asset_class.title(),
                "Shares": f"{p.shares:,.1f}",
                "Cost Basis": f"${p.cost_basis_per_share:,.2f}",
                "Price": f"${p.current_price:,.2f}",
                "Market Value": f"${p.market_value:,.2f}",
                "Weight": f"{p.weight:.1%}",
                "Gain / Loss": f"${p.unrealized_gain_loss:,.2f}",
                "Holding (Days)": p.holding_period_days,
            })
        df_holdings = pd.DataFrame(holdings_data)
        st.dataframe(df_holdings, use_container_width=True, height=300)

    # Tax-loss harvesting detector
    tlh_ops = pipeline.run_tax_loss_harvesting_scan(portfolio)
    if tlh_ops:
        with st.expander(f"💡 Tax-Loss Harvesting Opportunity Detected ({len(tlh_ops)} Position)", expanded=True):
            for op in tlh_ops:
                st.info(
                    f"**{op['symbol']}** has an unrealized loss of **${op['unrealized_loss']:,.2f}** "
                    f"held for {op['days_since_purchase']} days (>30 day wash-sale window passed). "
                    f"Recommended proxy replacement ETF: **{op['replacement_symbol']}** to maintain exposure while harvesting tax deduction."
                )
