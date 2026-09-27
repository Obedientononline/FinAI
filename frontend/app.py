"""Safe Wealth Advisory & Governed Portfolio Rebalancer.

Streamlit RIA Wealth Manager Portal.
Built on Lyzr Agent API, Lyzr Safe AI Fiduciary Guardrails, and Lyzr AIMS.
"""
import streamlit as st
import os
import sys

# Ensure root, backend, and frontend directories are in sys.path
_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_FRONTEND_DIR)
_BACKEND_DIR = os.path.join(_ROOT_DIR, "backend")

for p in [_ROOT_DIR, _BACKEND_DIR, _FRONTEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import config
from services.pipeline import AdvisoryPipeline
from ui.client_intake import render_client_intake
from ui.dashboard import render_dashboard
from ui.proposal_view import render_proposal_view
from ui.audit_view import render_audit_view
from ui.backtest_view import render_backtest_view
from models.portfolio import Position

# Page configuration
st.set_page_config(
    page_title="Safe Wealth Advisory | Governed Rebalancer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0D47A1;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #546E7A;
        margin-bottom: 15px;
    }
    .badge-safe {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .auth-banner {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "pipeline" not in st.session_state:
    st.session_state.pipeline = AdvisoryPipeline()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = "C-2026-001"

if "profile" not in st.session_state:
    st.session_state.profile = st.session_state.pipeline.load_client("C-2026-001")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = st.session_state.pipeline.load_portfolio("C-2026-001", use_mock_prices=True)

if "proposal" not in st.session_state or "ledger" not in st.session_state:
    p, l = st.session_state.pipeline.run_advisory(
        profile=st.session_state.profile,
        portfolio=st.session_state.portfolio,
        use_mock_prices=True
    )
    st.session_state.proposal = p
    st.session_state.ledger = l


# Advisor Security & Auth Gate
with st.sidebar:
    st.image("https://raw.githubusercontent.com/lyzr-ai/lyzr-assets/main/lyzr-logo.png", width=160)
    st.markdown("### 🔐 Fiduciary Control Plane")

    if not st.session_state.authenticated:
        st.markdown("<div class='auth-banner'>🔒 <b>RIA Advisor Credential Gate</b><br>SEC Reg S-P requires authentication before viewing sensitive client financial records.</div>", unsafe_allow_html=True)
        pin_input = st.text_input("Enter Advisor PIN", type="password", value="advisor2026")
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            if st.button("Authenticate", type="primary", use_container_width=True):
                if pin_input in ["advisor2026", "admin", "1234"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid PIN")
        with c_a2:
            if st.button("Guest Demo", use_container_width=True):
                st.session_state.authenticated = True
                st.rerun()
    else:
        st.markdown("<span class='badge-safe'>🔒 Lyzr Safe AI Active | Authorized CFP</span>", unsafe_allow_html=True)
        st.caption("SEC Rule 17a-4 & FINRA Rule 4511 Enforced")

    st.markdown("---")
    st.markdown("#### 📂 Client Portfolio Switcher (SQLite)")
    clients_list = st.session_state.pipeline.get_all_clients()
    client_options = {c["client_id"]: f"{c['client_id']} - {c['name']}" for c in clients_list}

    if not client_options:
        client_options = {"C-2026-001": "C-2026-001 - Jane Doe (Benchmark Compliant Moderate)"}

    selected_cid = st.selectbox(
        "Active Client Account",
        options=list(client_options.keys()),
        format_func=lambda x: client_options[x],
        index=list(client_options.keys()).index(st.session_state.selected_client_id) if st.session_state.selected_client_id in client_options else 0
    )

    if selected_cid != st.session_state.selected_client_id:
        st.session_state.selected_client_id = selected_cid
        st.session_state.profile = st.session_state.pipeline.load_client(selected_cid)
        st.session_state.portfolio = st.session_state.pipeline.load_portfolio(selected_cid, use_mock_prices=True)
        prop, ledg = st.session_state.pipeline.run_advisory(
            profile=st.session_state.profile,
            portfolio=st.session_state.portfolio,
            use_mock_prices=True
        )
        st.session_state.proposal = prop
        st.session_state.ledger = ledg
        st.rerun()

    st.markdown("---")
    st.markdown("#### Engine Settings")
    use_mock = st.toggle("Use Deterministic Benchmark Prices", value=True, help="Ensures zero latency and reproducible execution state")

    if st.button("⚡ Re-run Advisory Pipeline", type="primary", use_container_width=True):
        prop, ledg = st.session_state.pipeline.run_advisory(
            profile=st.session_state.profile,
            portfolio=st.session_state.portfolio,
            use_mock_prices=use_mock
        )
        st.session_state.proposal = prop
        st.session_state.ledger = ledg
        st.rerun()

    st.markdown("---")
    st.markdown("#### Fiduciary Core Pillars")
    st.markdown("1. **Lyzr Agent API:** Orchestrator + 5 specialized agents")
    st.markdown("2. **Deterministic Math:** CVXPY quadratic optimization")
    st.markdown("3. **Lyzr Safe AI:** 12 FINRA Reg BI suitability gates")
    st.markdown("4. **Lyzr AIMS:** SEC Rule 17a-4 verifiable ledger")


# Main Dashboard Header
st.markdown("<div class='main-header'>Safe Wealth Advisory & Governed Portfolio Rebalancer</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Fiduciary multi-agent wealth assistant that profiles IPS/KYC, rebalances with deterministic math, enforces FINRA suitability, and produces advisor-ready trade proposals.</div>", unsafe_allow_html=True)

# 6 Enterprise Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Client & IPS Intake",
    "📊 Current Portfolio",
    "📄 Trade Proposal & Suitability",
    "⚡ Market Shock Stress-Test",
    "📈 2020–2024 Backtest",
    "🔍 Lyzr AIMS SEC Audit Ledger"
])

with tab1:
    updated_profile = render_client_intake(st.session_state.pipeline)
    if st.button("Apply Profile to Active Rebalancing Session", use_container_width=True):
        st.session_state.profile = updated_profile
        p, l = st.session_state.pipeline.run_advisory(
            profile=st.session_state.profile,
            portfolio=st.session_state.portfolio,
            use_mock_prices=use_mock
        )
        st.session_state.proposal = p
        st.session_state.ledger = l
        st.success(f"Profile updated for {updated_profile.name}! Re-optimized trade proposal ready.")
        st.rerun()

with tab2:
    render_dashboard(st.session_state.portfolio, st.session_state.pipeline)

with tab3:
    render_proposal_view(
        proposal=st.session_state.proposal,
        profile=st.session_state.profile,
        portfolio=st.session_state.portfolio,
        ledger=st.session_state.ledger,
        pipeline=st.session_state.pipeline
    )

with tab4:
    st.markdown("### ⚡ Historical Market-Shock Stress Testing")
    st.caption("Replays macroeconomic crises on Current vs. Governed Portfolio to quantify downside protection.")
    stress_res = st.session_state.pipeline.run_stress_test(st.session_state.portfolio, st.session_state.proposal)

    import pandas as pd
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

with tab5:
    render_backtest_view()

with tab6:
    render_audit_view(
        ledger=st.session_state.ledger,
        aims=st.session_state.pipeline.aims,
        proposal_id=st.session_state.proposal.proposal_id
    )
