"""Seed script populating SQLite database with 8 diverse clients engineered
specifically to demonstrate every risk tier and trip all 12 FINRA suitability rules.
"""
import os
import sys
from datetime import datetime, date, timedelta

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(__file__))

from database.repository import WealthRepository
from models.client_profile import ClientProfile, IPS, KYC
from models.portfolio import Portfolio, Position


def seed_database():
    """Seeds the relational database with 8 production-grade client archetypes."""
    repo = WealthRepository()
    print("[INIT] Initializing SQLite database and seeding 8 FINRA test clients...")

    today = date.today()

    clients_data = [
        # 1. JANE DOE - Benchmark Compliant Moderate
        {
            "profile": ClientProfile(
                client_id="C-2026-001",
                name="Jane Doe (Benchmark Compliant Moderate)",
                ips=IPS(
                    investment_objective="growth_and_income",
                    risk_tolerance="moderate",
                    time_horizon_years=15,
                    liquidity_needs="low",
                    tax_bracket=0.32,
                    restrictions=["no_tobacco", "no_firearms"],
                    max_single_position_pct=0.10,
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=42,
                    annual_income=250000.0,
                    net_worth=1800000.0,
                    investment_experience="experienced",
                    employment_status="Employed",
                    dependents=2,
                )
            ),
            "positions": [
                Position(symbol="SPY", shares=150, cost_basis_per_share=420.50, current_price=545.20, holding_period_days=450, asset_class="equities"),
                Position(symbol="AGG", shares=200, cost_basis_per_share=98.75, current_price=101.30, holding_period_days=500, asset_class="fixed_income"),
                Position(symbol="GLD", shares=50, cost_basis_per_share=185.00, current_price=232.50, holding_period_days=210, asset_class="commodities"),
                Position(symbol="AAPL", shares=100, cost_basis_per_share=165.30, current_price=195.80, holding_period_days=380, asset_class="equities"),
                Position(symbol="MSFT", shares=75, cost_basis_per_share=340.00, current_price=415.60, holding_period_days=250, asset_class="equities"),
                Position(symbol="BND", shares=300, cost_basis_per_share=72.50, current_price=74.20, holding_period_days=600, asset_class="fixed_income"),
                Position(symbol="VWO", shares=80, cost_basis_per_share=42.10, current_price=44.50, holding_period_days=180, asset_class="equities"),
                Position(symbol="CASH", shares=50000, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=90, asset_class="cash"),
            ]
        },

        # 2. ROBERT MILLER - Senior Aggressive Mismatch (Trips FINRA-007 Senior Safeguard & FINRA-001 Equity Cap)
        {
            "profile": ClientProfile(
                client_id="C-2026-002",
                name="Robert Miller (Senior Aggressive Mismatch)",
                ips=IPS(
                    investment_objective="growth",
                    risk_tolerance="aggressive", # Aggressive self-assessment at age 74!
                    time_horizon_years=3,
                    liquidity_needs="high",
                    tax_bracket=0.24,
                    restrictions=[],
                    max_single_position_pct=0.15,
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=74, # Senior investor
                    annual_income=65000.0,
                    net_worth=950000.0,
                    investment_experience="limited",
                    employment_status="Retired",
                    dependents=0,
                )
            ),
            "positions": [
                Position(symbol="QQQ", shares=1200, cost_basis_per_share=380.00, current_price=480.30, holding_period_days=300, asset_class="equities"),
                Position(symbol="SPY", shares=400, cost_basis_per_share=450.00, current_price=545.20, holding_period_days=200, asset_class="equities"),
                Position(symbol="AGG", shares=500, cost_basis_per_share=99.00, current_price=101.30, holding_period_days=150, asset_class="fixed_income"),
                Position(symbol="CASH", shares=15000, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=50, asset_class="cash"),
            ]
        },

        # 3. CHAD SULLIVAN - Speculative Meme Asset Holder (Trips FINRA-005 Blocked Assets)
        {
            "profile": ClientProfile(
                client_id="C-2026-003",
                name="Chad Sullivan (Speculative Meme Asset Holder)",
                ips=IPS(
                    investment_objective="growth",
                    risk_tolerance="aggressive",
                    time_horizon_years=12,
                    liquidity_needs="low",
                    tax_bracket=0.32,
                    restrictions=[],
                    max_single_position_pct=0.20,
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=29,
                    annual_income=140000.0,
                    net_worth=450000.0,
                    investment_experience="experienced",
                    employment_status="Employed",
                    dependents=0,
                )
            ),
            "positions": [
                Position(symbol="DOGE", shares=300000, cost_basis_per_share=0.15, current_price=0.12, holding_period_days=45, asset_class="equities"),
                Position(symbol="SHIB", shares=50000000, cost_basis_per_share=0.00002, current_price=0.000018, holding_period_days=60, asset_class="equities"),
                Position(symbol="SPY", shares=200, cost_basis_per_share=480.00, current_price=545.20, holding_period_days=190, asset_class="equities"),
                Position(symbol="AGG", shares=300, cost_basis_per_share=100.00, current_price=101.30, holding_period_days=100, asset_class="fixed_income"),
                Position(symbol="CASH", shares=25000, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=30, asset_class="cash"),
            ]
        },

        # 4. ELEANOR VANCE - High Liquidity Crunch (Trips FINRA-003 Mandatory Cash Buffer)
        {
            "profile": ClientProfile(
                client_id="C-2026-004",
                name="Eleanor Vance (High Liquidity Crunch)",
                ips=IPS(
                    investment_objective="capital_preservation",
                    risk_tolerance="conservative",
                    time_horizon_years=4,
                    liquidity_needs="high", # Requires >= 15% cash
                    tax_bracket=0.22,
                    restrictions=[],
                    max_single_position_pct=0.10,
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=58,
                    annual_income=110000.0,
                    net_worth=820000.0,
                    investment_experience="experienced",
                    employment_status="Employed",
                    dependents=1,
                )
            ),
            "positions": [
                Position(symbol="AGG", shares=4000, cost_basis_per_share=100.00, current_price=101.30, holding_period_days=400, asset_class="fixed_income"),
                Position(symbol="SPY", shares=300, cost_basis_per_share=490.00, current_price=545.20, holding_period_days=300, asset_class="equities"),
                Position(symbol="TLT", shares=2500, cost_basis_per_share=95.00, current_price=92.50, holding_period_days=250, asset_class="fixed_income"),
                Position(symbol="CASH", shares=1500, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=20, asset_class="cash"), # Only 0.2% cash!
            ]
        },

        # 5. ARTHUR PENDELTON - Tech Executive Single-Stock Concentration (Trips FINRA-004 Concentration Limit)
        {
            "profile": ClientProfile(
                client_id="C-2026-005",
                name="Arthur Pendelton (Extreme Stock Concentration)",
                ips=IPS(
                    investment_objective="growth",
                    risk_tolerance="moderate_aggressive",
                    time_horizon_years=20,
                    liquidity_needs="low",
                    tax_bracket=0.35,
                    restrictions=[],
                    max_single_position_pct=0.10, # Max allowed position is 10%
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=38,
                    annual_income=320000.0,
                    net_worth=2400000.0,
                    investment_experience="sophisticated",
                    employment_status="Employed",
                    dependents=2,
                )
            ),
            "positions": [
                Position(symbol="AAPL", shares=5500, cost_basis_per_share=120.00, current_price=195.80, holding_period_days=800, asset_class="equities"), # $1.07M in AAPL! (>44%)
                Position(symbol="SPY", shares=800, cost_basis_per_share=460.00, current_price=545.20, holding_period_days=350, asset_class="equities"),
                Position(symbol="AGG", shares=3000, cost_basis_per_share=100.00, current_price=101.30, holding_period_days=400, asset_class="fixed_income"),
                Position(symbol="GLD", shares=800, cost_basis_per_share=200.00, current_price=232.50, holding_period_days=280, asset_class="commodities"),
                Position(symbol="CASH", shares=80000, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=100, asset_class="cash"),
            ]
        },

        # 6. HERITAGE CHARITY TRUST - IPS Restriction Violator (Trips FINRA-008 IPS Restrictions)
        {
            "profile": ClientProfile(
                client_id="C-2026-006",
                name="Heritage Charity Trust (IPS Negative Screen Violator)",
                ips=IPS(
                    investment_objective="income",
                    risk_tolerance="moderate_conservative",
                    time_horizon_years=10,
                    liquidity_needs="moderate",
                    tax_bracket=0.15,
                    restrictions=["no_tobacco", "no_firearms"], # Restricts MO, PM, BTI, RGR, SWBI
                    max_single_position_pct=0.12,
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=55,
                    annual_income=200000.0,
                    net_worth=3500000.0,
                    investment_experience="experienced",
                    employment_status="Institutional Trustee",
                    dependents=0,
                )
            ),
            "positions": [
                Position(symbol="MO", shares=8000, cost_basis_per_share=42.00, current_price=48.50, holding_period_days=320, asset_class="equities"), # Tobacco security!
                Position(symbol="AGG", shares=15000, cost_basis_per_share=100.00, current_price=101.30, holding_period_days=600, asset_class="fixed_income"),
                Position(symbol="LQD", shares=8000, cost_basis_per_share=105.00, current_price=108.40, holding_period_days=400, asset_class="fixed_income"),
                Position(symbol="CASH", shares=200000, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=90, asset_class="cash"),
            ]
        },

        # 7. HOWARD STERLING - Whale Undiversified Single Asset Class (Trips FINRA-011 Diversification Rule)
        {
            "profile": ClientProfile(
                client_id="C-2026-007",
                name="Howard Sterling (HNW Undiversified Single Class)",
                ips=IPS(
                    investment_objective="growth",
                    risk_tolerance="aggressive",
                    time_horizon_years=18,
                    liquidity_needs="low",
                    tax_bracket=0.37,
                    restrictions=[],
                    max_single_position_pct=0.30,
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=62,
                    annual_income=750000.0,
                    net_worth=5500000.0, # AUM > $500k, requires >= 4 asset classes
                    investment_experience="sophisticated",
                    employment_status="Business Owner",
                    dependents=1,
                )
            ),
            "positions": [
                Position(symbol="SPY", shares=5000, cost_basis_per_share=450.00, current_price=545.20, holding_period_days=700, asset_class="equities"),
                Position(symbol="QQQ", shares=4000, cost_basis_per_share=390.00, current_price=480.30, holding_period_days=500, asset_class="equities"),
                Position(symbol="AAPL", shares=3000, cost_basis_per_share=150.00, current_price=195.80, holding_period_days=800, asset_class="equities"),
                # 100% Equities, 0 FI, 0 Commodities, 0 Cash
            ]
        },

        # 8. DAVE TURNER - High Churn & Wash Sale Risk (Trips FINRA-012 Wash Sale & FINRA-009 Turnover)
        {
            "profile": ClientProfile(
                client_id="C-2026-008",
                name="Dave Turner (Wash Sale & High Churn)",
                ips=IPS(
                    investment_objective="growth",
                    risk_tolerance="aggressive",
                    time_horizon_years=10,
                    liquidity_needs="low",
                    tax_bracket=0.32,
                    restrictions=[],
                    max_single_position_pct=0.20,
                    rebalance_threshold_pct=0.05,
                ),
                kyc=KYC(
                    age=35,
                    annual_income=210000.0,
                    net_worth=750000.0,
                    investment_experience="experienced",
                    employment_status="Employed",
                    dependents=0,
                )
            ),
            "positions": [
                Position(symbol="VWO", shares=4000, cost_basis_per_share=48.00, current_price=44.50, holding_period_days=14, asset_class="equities"), # Bought 14 days ago with loss!
                Position(symbol="SPY", shares=600, cost_basis_per_share=520.00, current_price=545.20, holding_period_days=40, asset_class="equities"),
                Position(symbol="AGG", shares=1000, cost_basis_per_share=100.00, current_price=101.30, holding_period_days=60, asset_class="fixed_income"),
                Position(symbol="CASH", shares=35000, cost_basis_per_share=1.0, current_price=1.0, holding_period_days=10, asset_class="cash"),
            ]
        },
    ]

    for item in clients_data:
        p = item["profile"]
        repo.save_client(p)
        port = Portfolio(positions=item["positions"])
        repo.save_holdings(p.client_id, port)
        print(f"  [OK] Seeded client: {p.client_id} - {p.name} (${port.total_value:,.2f})")

    print(f"[SUCCESS] Successfully seeded {len(clients_data)} relational clients in SQLite at '{repo.db_path or 'data/wealth_advisory.db'}'.")


if __name__ == "__main__":
    seed_database()
