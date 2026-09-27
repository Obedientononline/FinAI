"""UI Component: Client Intake & Fiduciary Profiling."""
import streamlit as st
import json
from models.client_profile import ClientProfile, IPS, KYC
from engine.risk_scorer import compute_risk_score, get_scoring_explanation


def render_client_intake(pipeline) -> ClientProfile:
    """Renders the Client Intake & IPS Parsing interface."""
    st.markdown("### 📋 Client & Investment Policy Statement (IPS) Intake")
    st.caption("Fiduciary onboarding with deterministic risk scoring and mandatory regulatory bounds.")

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        preset = st.selectbox(
            "Load Client Scenario Preset",
            [
                "Jane Doe (Moderate Growth & Income, 15yr Horizon)",
                "Robert Miller (Conservative Senior 72yo, Capital Preservation)",
                "Sophia Chen (Aggressive Growth Tech Executive, 25yr Horizon)",
                "Custom Intake Form"
            ],
            index=0
        )

    # Base values
    if "Jane Doe" in preset:
        default_name = "Jane Doe"
        default_id = "C-2026-001"
        default_age = 42
        default_income = 250000.0
        default_nw = 1800000.0
        default_exp = "experienced"
        default_obj = "growth_and_income"
        default_tol = "moderate"
        default_horizon = 15
        default_liq = "low"
        default_tax = 0.32
        default_rest = ["no_tobacco", "no_firearms"]
        default_max_pos = 0.10
    elif "Robert Miller" in preset:
        default_name = "Robert Miller"
        default_id = "C-2026-002"
        default_age = 72
        default_income = 95000.0
        default_nw = 1200000.0
        default_exp = "experienced"
        default_obj = "capital_preservation"
        default_tol = "conservative"
        default_horizon = 4
        default_liq = "high"
        default_tax = 0.24
        default_rest = ["no_tobacco"]
        default_max_pos = 0.08
    elif "Sophia Chen" in preset:
        default_name = "Sophia Chen"
        default_id = "C-2026-003"
        default_age = 31
        default_income = 420000.0
        default_nw = 2100000.0
        default_exp = "sophisticated"
        default_obj = "growth"
        default_tol = "aggressive"
        default_horizon = 25
        default_liq = "low"
        default_tax = 0.35
        default_rest = []
        default_max_pos = 0.15
    else:
        default_name = "Alex Vance"
        default_id = "C-2026-004"
        default_age = 50
        default_income = 180000.0
        default_nw = 950000.0
        default_exp = "limited"
        default_obj = "income"
        default_tol = "moderate_conservative"
        default_horizon = 8
        default_liq = "moderate"
        default_tax = 0.24
        default_rest = []
        default_max_pos = 0.10

    with st.expander("👤 Client Demographic & KYC Data", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Full Name", value=default_name)
            client_id = st.text_input("Client ID", value=default_id)
        with c2:
            age = st.number_input("Age", min_value=18, max_value=105, value=default_age)
            experience = st.selectbox(
                "Investment Experience",
                ["none", "limited", "experienced", "sophisticated"],
                index=["none", "limited", "experienced", "sophisticated"].index(default_exp)
            )
        with c3:
            income = st.number_input("Annual Income ($)", min_value=0.0, value=default_income, step=10000.0, format="%.2f")
            net_worth = st.number_input("Investable Net Worth ($)", min_value=0.0, value=default_nw, step=50000.0, format="%.2f")

    with st.expander("📜 Investment Policy Statement (IPS) Parameters", expanded=True):
        p1, p2, p3 = st.columns(3)
        with p1:
            objective = st.selectbox(
                "Investment Objective",
                ["growth", "growth_and_income", "income", "capital_preservation"],
                index=["growth", "growth_and_income", "income", "capital_preservation"].index(default_obj)
            )
            tolerance = st.selectbox(
                "Stated Risk Tolerance",
                ["conservative", "moderate_conservative", "moderate", "moderate_aggressive", "aggressive"],
                index=["conservative", "moderate_conservative", "moderate", "moderate_aggressive", "aggressive"].index(default_tol)
            )
        with p2:
            horizon = st.slider("Time Horizon (Years)", min_value=1, max_value=40, value=default_horizon)
            liquidity = st.selectbox(
                "Liquidity Needs",
                ["low", "moderate", "high"],
                index=["low", "moderate", "high"].index(default_liq)
            )
        with p3:
            tax_bracket = st.slider("Marginal Tax Bracket", min_value=0.10, max_value=0.37, value=default_tax, step=0.01, format="%.2f")
            max_pos_pct = st.slider("Max Single Position Limit", min_value=0.05, max_value=0.25, value=default_max_pos, step=0.01, format="%.2f")

        restrictions_selected = st.multiselect(
            "IPS Negative Screen Restrictions",
            ["no_tobacco", "no_firearms", "no_fossil_fuels", "no_crypto"],
            default=default_rest
        )

    # Real-time Mathematical Scoring Preview
    kyc_obj = KYC(
        age=age,
        annual_income=income,
        net_worth=net_worth,
        investment_experience=experience,
        employment_status="Employed",
        dependents=2
    )
    ips_obj = IPS(
        investment_objective=objective,
        risk_tolerance=tolerance,
        time_horizon_years=horizon,
        liquidity_needs=liquidity,
        tax_bracket=tax_bracket,
        restrictions=restrictions_selected,
        max_single_position_pct=max_pos_pct,
        rebalance_threshold_pct=0.05
    )

    score, category, breakdown = compute_risk_score(kyc_obj, ips_obj)

    st.markdown("#### ⚖️ Fiduciary Risk Scoring Telemetry (Deterministic Math)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Calculated Risk Score", f"{score} / 10")
    m2.metric("Risk Category", category.replace("_", " ").title())
    m3.metric("Mandatory Equity Ceiling", "≤ 20.0%" if score <= 3 else ("≤ 35.0%" if score == 4 else ("≤ 55.0%" if score <= 6 else ("≤ 70.0%" if score == 7 else "≤ 90.0%"))))
    m4.metric("Mandatory Cash Buffer", "≥ 15.0%" if liquidity == "high" else ("≥ 7.0%" if liquidity == "moderate" else "≥ 2.0%"))

    with st.expander("🔍 View Mathematical Scoring Breakdown"):
        st.write(get_scoring_explanation(breakdown))

    profile = ClientProfile(
        client_id=client_id,
        name=name,
        ips=ips_obj,
        kyc=kyc_obj,
        risk_score=score,
        risk_category=category
    )
    return profile
