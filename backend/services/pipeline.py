"""Fiduciary Advisory Pipeline Service.

Provides a unified high-level interface to ingest client records, coordinate
the multi-agent workflow, run stress-tests and tax-loss harvesting scans, and
return comprehensive proposal packages.
"""
import os
import json
import csv
from datetime import datetime, date
from typing import Dict, Any, Tuple, List, Optional

import config
from models.client_profile import ClientProfile, IPS, KYC
from models.portfolio import Portfolio, Position, TradeOrder
from models.proposal import TradeProposal
from models.audit import ComplianceLedger
from services.aims_logger import AIMSLogger
from engine.market_data import get_current_prices
from engine.tax_engine import identify_tlh_opportunities


from database.repository import WealthRepository


class AdvisoryPipeline:
    """Unified engine driving end-to-end client advisory, rebalancing, and compliance."""

    def __init__(self, repo: Optional[WealthRepository] = None):
        from agents.manager_agent import ManagerAgent
        self.repo = repo or WealthRepository()
        self.aims = AIMSLogger(repo=self.repo)
        self.manager = ManagerAgent(aims_logger=self.aims)

    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Queries all clients from relational SQLite database."""
        return self.repo.list_clients()

    def load_client(self, client_id: str) -> Optional[ClientProfile]:
        """Loads client profile from SQLite repository, falling back to sample JSON."""
        client = self.repo.get_client(client_id)
        if client:
            return client
        return self.load_sample_client()

    def load_portfolio(self, client_id: str, use_mock_prices: bool = True) -> Portfolio:
        """Loads portfolio holdings from SQLite repository, falling back to sample CSV."""
        port = self.repo.get_holdings(client_id)
        if port and port.positions:
            return port
        return self.load_sample_portfolio(use_mock_prices=use_mock_prices)

    def save_new_client(self, profile: ClientProfile, portfolio: Portfolio):
        """Saves a newly onboarded client and initial holdings to SQLite."""
        self.repo.save_client(profile)
        self.repo.save_holdings(profile.client_id, portfolio)

    def clear_all_clients(self):
        """Cleans and resets all client records in repository."""
        self.repo.clear_all_clients()

    def load_sample_client(self) -> ClientProfile:
        """Loads client profile from data/sample_ips.json and sample_kyc.json."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        ips_path = os.path.join(base_dir, "data", "sample_ips.json")
        kyc_path = os.path.join(base_dir, "data", "sample_kyc.json")

        with open(ips_path, "r", encoding="utf-8") as f:
            ips_raw = json.load(f)

        with open(kyc_path, "r", encoding="utf-8") as f:
            kyc_raw = json.load(f)

        ips_data = ips_raw.get("ips", ips_raw)
        kyc_data = kyc_raw.get("kyc", kyc_raw)

        return ClientProfile(
            client_id=ips_raw.get("client_id", "C-2026-001"),
            name=ips_raw.get("name", "Jane Doe"),
            ips=IPS(**ips_data),
            kyc=KYC(**kyc_data),
        )

    def load_sample_portfolio(self, use_mock_prices: bool = True) -> Portfolio:
        """Loads portfolio holdings from data/sample_holdings.csv."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        holdings_path = os.path.join(base_dir, "data", "sample_holdings.csv")

        positions = []
        symbols = []
        raw_rows = []

        with open(holdings_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = row["symbol"].strip().upper()
                symbols.append(sym)
                raw_rows.append(row)

        prices = get_current_prices(symbols, use_mock=use_mock_prices)

        for row in raw_rows:
            sym = row["symbol"].strip().upper()
            shares = float(row["shares"])
            cost_basis = float(row["cost_basis_per_share"])
            purchase_date_str = row["purchase_date"].strip()

            try:
                p_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
                holding_days = (date.today() - p_date).days
            except Exception:
                holding_days = 400

            asset_class = config.ASSET_CLASS_MAP.get(sym, "equities")
            curr_price = prices.get(sym, cost_basis)

            pos = Position(
                symbol=sym,
                shares=shares,
                cost_basis_per_share=cost_basis,
                current_price=curr_price,
                holding_period_days=holding_days,
                asset_class=asset_class,
            )
            positions.append(pos)

        return Portfolio(positions=positions)

    def run_advisory(
        self,
        profile: Optional[ClientProfile] = None,
        portfolio: Optional[Portfolio] = None,
        use_mock_prices: bool = True,
    ) -> Tuple[TradeProposal, ComplianceLedger]:
        """Runs the entire multi-agent fiduciary advisory and rebalancing workflow."""
        if profile is None:
            profile = self.load_sample_client()
        if portfolio is None:
            portfolio = self.load_sample_portfolio(use_mock_prices=use_mock_prices)

        proposal, ledger = self.manager.run_advisory_pipeline(
            profile=profile, portfolio=portfolio, use_mock_prices=use_mock_prices
        )
        return proposal, ledger

    def run_tax_loss_harvesting_scan(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """Identifies active tax-loss harvesting candidates across portfolio holdings."""
        symbols = [p.symbol for p in portfolio.positions]
        prices = get_current_prices(symbols, use_mock=True)
        return identify_tlh_opportunities(portfolio.positions, prices, wash_sale_days=config.WASH_SALE_DAYS)

    def run_stress_test(self, portfolio: Portfolio, proposal: TradeProposal) -> Dict[str, Any]:
        """
        Executes historical market-shock stress testing on current vs target portfolio.
        Scenarios:
        1. 2008 Global Financial Crisis (Equities -50%, FI +12%, Comm -35%, Cash 0%)
        2. 2020 COVID Liquidity Shock (Equities -34%, FI -5%, Comm -15%, Cash 0%)
        3. 2022 Inflation & Rate Hike Surge (Equities -19%, FI -13%, Comm +25%, Cash +2%)
        """
        shocks = {
            "2008 Global Financial Crisis": {
                "equities": -0.50, "fixed_income": 0.12, "commodities": -0.35, "cash": 0.00
            },
            "2020 COVID Liquidity Shock": {
                "equities": -0.34, "fixed_income": -0.05, "commodities": -0.15, "cash": 0.00
            },
            "2022 Inflation & Rate Hike Surge": {
                "equities": -0.19, "fixed_income": -0.13, "commodities": 0.25, "cash": 0.02
            }
        }

        results = {}
        for scenario_name, shock_weights in shocks.items():
            current_drawdown = sum(
                portfolio.allocation.get(ac, 0.0) * shock_weights.get(ac, 0.0)
                for ac in ["equities", "fixed_income", "commodities", "cash"]
            )
            target_drawdown = sum(
                proposal.target_allocation.get(ac, 0.0) * shock_weights.get(ac, 0.0)
                for ac in ["equities", "fixed_income", "commodities", "cash"]
            )

            resilience_gain = target_drawdown - current_drawdown

            results[scenario_name] = {
                "current_portfolio_drawdown": current_drawdown,
                "target_portfolio_drawdown": target_drawdown,
                "risk_reduction_percentage": resilience_gain,
                "dollar_preservation": abs(resilience_gain) * portfolio.total_value,
            }

        return results
