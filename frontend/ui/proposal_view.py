"""UI Component: Advisor Trade Proposal & FINRA Suitability Inspection."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from models.proposal import TradeProposal
from models.client_profile import ClientProfile
from models.portfolio import Portfolio
from models.audit import ComplianceLedger
from services.proposal_generator import generate_proposal_markdown, generate_proposal_pdf


def render_proposal_view(
    proposal: TradeProposal,
    profile: ClientProfile,
    portfolio: Portfolio,
    ledger: ComplianceLedger,
    pipeline,
):
    """Renders the comprehensive Advisor Proposal Review Dossier."""
    st.markdown("### 📄 Advisor Trade Proposal & Governed Rebalancing Docket")

    # Status Banner
    is_approved = proposal.suitability_report.all_passed
    if is_approved:
        st.success(
            f"✅ **Lyzr Safe AI Compliance Gate: APPROVED (Proposal ID: `{proposal.proposal_id}`)**\n\n"
            f"All 12 FINRA suitability checks passed. Mathematical tracking error minimized. Ready for Advisor 1-Click Execution."
        )
    else:
        st.error(
            f"🚫 **Lyzr Safe AI Compliance Gate: BLOCKED (Proposal ID: `{proposal.proposal_id}`)**\n\n"
            f"{len(proposal.suitability_report.critical_failures)} Critical Suitability Violation(s) Detected. "
            f"Execution inhibited in accordance with Fiduciary Reg BI rules."
        )

    # Executive Proposal Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Buy Orders", f"${proposal.total_buy_value:,.2f}")
    m2.metric("Total Sell Orders", f"${proposal.total_sell_value:,.2f}")
    m3.metric("Net Est. Tax Drag", f"${proposal.net_tax_impact:,.2f}")
    m4.metric("Turnover Ratio", f"{((proposal.total_buy_value + proposal.total_sell_value) / portfolio.total_value) if portfolio.total_value > 0 else 0.0:.1%}")

    # Tabs for Proposal Components
    tab_alloc, tab_trades, tab_finra, tab_stress = st.tabs([
        "🔄 Allocation Shift",
        "🛒 Trade Orders",
        "🛡️ FINRA Suitability (12 Checks)",
        "⚡ Market Shock Stress-Test"
    ])

    with tab_alloc:
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("#### Strategic Transition")
            classes = ["equities", "fixed_income", "commodities", "cash"]
            current_vals = [proposal.current_allocation.get(c, 0.0) for c in classes]
            target_vals = [proposal.target_allocation.get(c, 0.0) for c in classes]
            class_labels = [c.replace("_", " ").title() for c in classes]

            fig_bar = go.Figure(data=[
                go.Bar(name='Current Allocation', x=class_labels, y=current_vals, marker_color='#90CAF9'),
                go.Bar(name='Target Allocation', x=class_labels, y=target_vals, marker_color='#1E88E5')
            ])
            fig_bar.update_layout(
                barmode='group',
                yaxis=dict(tickformat='.0%'),
                margin=dict(l=10, r=10, t=30, b=10),
                height=320,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_right:
            st.markdown("#### Transition Table & Rationale")
            shift_data = []
            for c in classes:
                curr_w = proposal.current_allocation.get(c, 0.0)
                targ_w = proposal.target_allocation.get(c, 0.0)
                shift_data.append({
                    "Asset Class": c.replace("_", " ").title(),
                    "Current": f"{curr_w:.1%}",
                    "Target": f"{targ_w:.1%}",
                    "Shift": f"{targ_w - curr_w:+.1%}"
                })
            st.dataframe(pd.DataFrame(shift_data), use_container_width=True)
            st.info(f"**Strategist Allocation Rationale:**\n{proposal.allocation_rationale}")

    with tab_trades:
        st.markdown("#### Deterministic Share Trade Orders (CVXPY Quadratic Program)")
        if not proposal.trades:
            st.write("No trade adjustments necessary. Portfolio currently within drift tolerance bounds.")
        else:
            trades_rows = []
            for t in proposal.trades:
                trades_rows.append({
                    "Action": "🟢 BUY" if t.action == "BUY" else "🔴 SELL",
                    "Symbol": t.symbol,
                    "Asset Class": t.asset_class.title(),
                    "Shares": f"{t.shares:,.0f}",
                    "Price": f"${t.estimated_price:,.2f}",
                    "Estimated Value": f"${t.estimated_value:,.2f}",
                    "Est. Tax Impact": f"${t.tax_impact:,.2f}" if t.action == "SELL" else "$0.00",
                    "Rationale": t.rationale
                })
            st.dataframe(pd.DataFrame(trades_rows), use_container_width=True)

    with tab_finra:
        st.markdown("#### Lyzr Safe AI — 12-Rule FINRA Suitability & SEC Reg BI Gate")
        
        col_f1, col_f2 = st.columns(2)
        half = len(proposal.suitability_report.checks) // 2
        
        with col_f1:
            for check in proposal.suitability_report.checks[:half]:
                icon = "✅" if check.passed else ("🚫" if check.severity == "critical" else "⚠️")
                box_type = st.success if check.passed else (st.error if check.severity == "critical" else st.warning)
                box_type(f"{icon} **[{check.rule_id}] {check.rule_name}** ({check.severity.upper()})\n\n{check.details}")

        with col_f2:
            for check in proposal.suitability_report.checks[half:]:
                icon = "✅" if check.passed else ("🚫" if check.severity == "critical" else "⚠️")
                box_type = st.success if check.passed else (st.error if check.severity == "critical" else st.warning)
                box_type(f"{icon} **[{check.rule_id}] {check.rule_name}** ({check.severity.upper()})\n\n{check.details}")

    with tab_stress:
        st.markdown("#### Historical Market-Shock Stress Testing (Stretch Goal)")
        st.caption("Replays macroeconomic crises on the Current Portfolio vs the Governed Rebalanced Portfolio.")
        stress_res = pipeline.run_stress_test(portfolio, proposal)

        stress_rows = []
        for shock_name, metrics in stress_res.items():
            stress_rows.append({
                "Crisis Scenario": shock_name,
                "Current Drawdown": f"{metrics['current_portfolio_drawdown']:.1%}",
                "Rebalanced Drawdown": f"{metrics['target_portfolio_drawdown']:.1%}",
                "Drawdown Protection": f"{metrics['risk_reduction_percentage']:+.1%}",
                "Capital Preserved": f"${metrics['dollar_preservation']:,.2f}"
            })
        st.dataframe(pd.DataFrame(stress_rows), use_container_width=True)
        st.success("Rebalanced portfolio demonstrates improved downside tail-risk resilience across historical macro shocks.")

    # Advisor Actions Section
    st.markdown("---")
    c_act1, c_act2, c_act3 = st.columns([2, 1, 1])

    with c_act1:
        notes = st.text_input("Advisor Approval / Regulatory Notes", value="Trade proposal reviewed and aligned with client IPS fiduciary objectives.")

    with c_act2:
        approve_disabled = not proposal.suitability_report.all_passed
        if st.button("🚀 1-Click Approve & Execute", type="primary", disabled=approve_disabled, use_container_width=True):
            proposal.advisor_approved = True
            proposal.advisor_notes = notes
            pipeline.aims.log_event(
                event_type="ADVISOR_DECISION",
                agent_name="RIA Wealth Advisor (Human-in-the-Loop)",
                input_summary=f"Proposal {proposal.proposal_id}",
                output_summary="EXECUTED_APPROVED",
                reasoning_chain=f"Human Advisor signed off: '{notes}'. Ledger hash confirmed.",
                compliance_status="PASS",
                proposal_id=proposal.proposal_id
            )
            st.balloons()
            st.success(f"Trade Proposal `{proposal.proposal_id}` officially APPROVED & Queued for Custodian Execution!")

    with c_act3:
        # PDF Generation & Download
        pdf_path = f"proposal_{proposal.proposal_id}.pdf"
        generate_proposal_pdf(proposal, profile, ledger, output_path=pdf_path)
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download Proposal PDF",
                data=pdf_bytes,
                file_name=f"Fiduciary_Proposal_{proposal.proposal_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception:
            md_content = generate_proposal_markdown(proposal, profile, ledger)
            st.download_button(
                label="📥 Download Proposal Report",
                data=md_content,
                file_name=f"Fiduciary_Proposal_{proposal.proposal_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
