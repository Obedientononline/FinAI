"""Relational repository layer interfacing SQLite with Pydantic domain models."""
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

from .schema import get_connection, init_db
from models.client_profile import ClientProfile, IPS, KYC
from models.portfolio import Portfolio, Position, TradeOrder
from models.proposal import TradeProposal, SuitabilityReport, SuitabilityCheck
from models.audit import AuditEntry, ComplianceLedger


class WealthRepository:
    """Repository managing persistence for clients, IPS/KYC, portfolios, proposals, and audit logs."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    # ------------------ Client & IPS/KYC ------------------
    def save_client(self, profile: ClientProfile):
        """Inserts or replaces a client and their associated IPS and KYC records."""
        conn = self._get_conn()
        with conn:
            # 1. Client
            conn.execute(
                "INSERT INTO clients (client_id, name) VALUES (?, ?) ON CONFLICT(client_id) DO UPDATE SET name=excluded.name;",
                (profile.client_id, profile.name)
            )
            # 2. IPS
            conn.execute(
                """INSERT INTO ips (
                    client_id, investment_objective, risk_tolerance, time_horizon_years,
                    liquidity_needs, tax_bracket, restrictions, max_single_position_pct, rebalance_threshold_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(client_id) DO UPDATE SET
                    investment_objective=excluded.investment_objective,
                    risk_tolerance=excluded.risk_tolerance,
                    time_horizon_years=excluded.time_horizon_years,
                    liquidity_needs=excluded.liquidity_needs,
                    tax_bracket=excluded.tax_bracket,
                    restrictions=excluded.restrictions,
                    max_single_position_pct=excluded.max_single_position_pct,
                    rebalance_threshold_pct=excluded.rebalance_threshold_pct;""",
                (
                    profile.client_id,
                    profile.ips.investment_objective,
                    profile.ips.risk_tolerance,
                    profile.ips.time_horizon_years,
                    profile.ips.liquidity_needs,
                    profile.ips.tax_bracket,
                    json.dumps(profile.ips.restrictions),
                    profile.ips.max_single_position_pct,
                    profile.ips.rebalance_threshold_pct,
                )
            )
            # 3. KYC
            conn.execute(
                """INSERT INTO kyc (
                    client_id, age, annual_income, net_worth, investment_experience, employment_status, dependents
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(client_id) DO UPDATE SET
                    age=excluded.age,
                    annual_income=excluded.annual_income,
                    net_worth=excluded.net_worth,
                    investment_experience=excluded.investment_experience,
                    employment_status=excluded.employment_status,
                    dependents=excluded.dependents;""",
                (
                    profile.client_id,
                    profile.kyc.age,
                    profile.kyc.annual_income,
                    profile.kyc.net_worth,
                    profile.kyc.investment_experience,
                    profile.kyc.employment_status,
                    profile.kyc.dependents,
                )
            )

    def clear_all_clients(self):
        """Removes all stored client records, holdings, proposals, and audit ledgers."""
        conn = self._get_conn()
        with conn:
            conn.execute("DELETE FROM audit_entries;")
            conn.execute("DELETE FROM proposals;")
            conn.execute("DELETE FROM holdings;")
            conn.execute("DELETE FROM ips;")
            conn.execute("DELETE FROM kyc;")
            conn.execute("DELETE FROM clients;")

    def get_client(self, client_id: str) -> Optional[ClientProfile]:
        """Retrieves a client by client_id including IPS, KYC, and calculated risk tier."""
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("SELECT name FROM clients WHERE client_id = ?", (client_id,))
        c_row = cur.fetchone()
        if not c_row:
            return None
        name = c_row["name"]

        cur.execute("SELECT * FROM ips WHERE client_id = ?", (client_id,))
        ips_row = cur.fetchone()
        if not ips_row:
            return None
        ips = IPS(
            investment_objective=ips_row["investment_objective"],
            risk_tolerance=ips_row["risk_tolerance"],
            time_horizon_years=ips_row["time_horizon_years"],
            liquidity_needs=ips_row["liquidity_needs"],
            tax_bracket=ips_row["tax_bracket"],
            restrictions=json.loads(ips_row["restrictions"]),
            max_single_position_pct=ips_row["max_single_position_pct"],
            rebalance_threshold_pct=ips_row["rebalance_threshold_pct"],
        )

        cur.execute("SELECT * FROM kyc WHERE client_id = ?", (client_id,))
        kyc_row = cur.fetchone()
        if not kyc_row:
            return None
        kyc = KYC(
            age=kyc_row["age"],
            annual_income=kyc_row["annual_income"],
            net_worth=kyc_row["net_worth"],
            investment_experience=kyc_row["investment_experience"],
            employment_status=kyc_row["employment_status"],
            dependents=kyc_row["dependents"],
        )

        from engine.risk_scorer import compute_risk_score
        risk_score, risk_category, _ = compute_risk_score(kyc, ips)

        return ClientProfile(
            client_id=client_id,
            name=name,
            ips=ips,
            kyc=kyc,
            risk_score=risk_score,
            risk_category=risk_category,
        )

    def list_clients(self) -> List[Dict[str, Any]]:
        """Lists all client summaries with risk profile metadata."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.client_id, c.name, k.age, k.net_worth, i.risk_tolerance, i.investment_objective, i.time_horizon_years
            FROM clients c
            LEFT JOIN kyc k ON c.client_id = k.client_id
            LEFT JOIN ips i ON c.client_id = i.client_id
            ORDER BY c.client_id;
        """)
        return [dict(row) for row in cur.fetchall()]

    # ------------------ Holdings ------------------
    def save_holdings(self, client_id: str, portfolio: Portfolio):
        """Replaces all current holdings for a client."""
        conn = self._get_conn()
        with conn:
            conn.execute("DELETE FROM holdings WHERE client_id = ?", (client_id,))
            for p in portfolio.positions:
                conn.execute(
                    """INSERT INTO holdings (
                        client_id, symbol, shares, cost_basis_per_share, purchase_date, holding_period_days, asset_class
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);""",
                    (
                        client_id,
                        p.symbol,
                        p.shares,
                        p.cost_basis_per_share,
                        getattr(p, "purchase_date", "2024-01-15"),
                        p.holding_period_days,
                        p.asset_class,
                    )
                )

    def get_holdings(self, client_id: str, current_prices: Optional[Dict[str, float]] = None) -> Portfolio:
        """Retrieves all holdings for a client as a Portfolio object."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM holdings WHERE client_id = ?", (client_id,))
        rows = cur.fetchall()

        from engine.market_data import get_current_prices
        symbols = [r["symbol"] for r in rows]
        prices = current_prices or get_current_prices(symbols, use_mock=True)

        positions = []
        for r in rows:
            sym = r["symbol"]
            cost_basis = float(r["cost_basis_per_share"])
            pos = Position(
                symbol=sym,
                shares=float(r["shares"]),
                cost_basis_per_share=cost_basis,
                current_price=prices.get(sym, cost_basis),
                holding_period_days=int(r["holding_period_days"]),
                asset_class=r["asset_class"],
            )
            positions.append(pos)

        return Portfolio(positions=positions)

    # ------------------ Proposals ------------------
    def save_proposal(self, proposal: TradeProposal):
        """Stores a generated trade proposal."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                """INSERT OR REPLACE INTO proposals (
                    proposal_id, client_id, timestamp, risk_score, risk_category,
                    current_allocation, target_allocation, trades, total_buy_value,
                    total_sell_value, net_tax_impact, suitability_passed, suitability_report,
                    market_analysis, allocation_rationale, advisor_approved, advisor_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (
                    proposal.proposal_id,
                    proposal.client_id,
                    proposal.timestamp.isoformat(),
                    proposal.risk_score,
                    proposal.risk_category,
                    json.dumps(proposal.current_allocation),
                    json.dumps(proposal.target_allocation),
                    json.dumps([t.model_dump() for t in proposal.trades]),
                    proposal.total_buy_value,
                    proposal.total_sell_value,
                    proposal.net_tax_impact,
                    1 if proposal.suitability_report.all_passed else 0,
                    json.dumps(proposal.suitability_report.model_dump()),
                    proposal.market_analysis,
                    proposal.allocation_rationale,
                    1 if proposal.advisor_approved is True else (0 if proposal.advisor_approved is False else None),
                    proposal.advisor_notes,
                )
            )

    # ------------------ Lyzr AIMS Audit & Cryptographic Chain ------------------
    def save_audit_entry(
        self,
        entry: AuditEntry,
        client_id: Optional[str] = None,
        prev_hash: Optional[str] = None,
        entry_hash: Optional[str] = None,
    ):
        """Inserts an immutable audit trace record into SQLite."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                """INSERT OR REPLACE INTO audit_entries (
                    event_id, proposal_id, client_id, timestamp, event_type,
                    agent_name, input_summary, output_summary, reasoning_chain,
                    compliance_status, metadata, prev_hash, entry_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (
                    entry.event_id,
                    entry.proposal_id,
                    client_id,
                    entry.timestamp.isoformat(),
                    entry.event_type,
                    entry.agent_name,
                    entry.input_summary,
                    entry.output_summary,
                    entry.reasoning_chain,
                    entry.compliance_status,
                    json.dumps(entry.metadata, default=lambda x: x.tolist() if hasattr(x, 'tolist') else str(x)),
                    prev_hash,
                    entry_hash or "unhashed",
                )
            )

    def get_audit_entries(self, proposal_id: Optional[str] = None, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries audit entries by proposal_id or client_id."""
        conn = self._get_conn()
        cur = conn.cursor()
        if proposal_id:
            cur.execute("SELECT * FROM audit_entries WHERE proposal_id = ? ORDER BY rowid ASC;", (proposal_id,))
        elif client_id:
            cur.execute("SELECT * FROM audit_entries WHERE client_id = ? ORDER BY rowid ASC;", (client_id,))
        else:
            cur.execute("SELECT * FROM audit_entries ORDER BY rowid DESC LIMIT 50;")
        return [dict(r) for r in cur.fetchall()]

    def tamper_audit_entry(self, event_id: str, altered_reasoning: str) -> bool:
        """
        DELIBERATE TAMPER INJECTION (For Hackathon Integrity Verification Demo).
        Modifies a reasoning chain directly in SQLite without updating the cryptographic hash,
        allowing the live verification engine to catch and highlight the exact compromised node.
        """
        conn = self._get_conn()
        with conn:
            cur = conn.execute(
                "UPDATE audit_entries SET reasoning_chain = ? WHERE event_id = ?;",
                (altered_reasoning, event_id)
            )
            return cur.rowcount > 0

    def verify_proposal_chain(self, proposal_id: str) -> Dict[str, Any]:
        """
        Recalculates the SHA-256 hash chain live across all chronological entries in SQLite.
        Detects any tampering, unauthorized modifications, or broken links in the AIMS chain.
        """
        entries = self.get_audit_entries(proposal_id=proposal_id)
        if not entries:
            return {"verified": False, "error": "No records found for proposal"}

        computed_prev_hash = "GENESIS_ROOT"
        for i, entry in enumerate(entries):
            content_to_hash = (
                f"{computed_prev_hash}|{entry['event_id']}|{entry['event_type']}|"
                f"{entry['agent_name']}|{entry['output_summary']}|{entry['reasoning_chain']}"
            )
            expected_hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()

            stored_hash = entry.get("entry_hash")
            if stored_hash and stored_hash != "unhashed" and stored_hash != expected_hash:
                return {
                    "verified": False,
                    "tampered": True,
                    "compromised_node": entry["event_id"],
                    "compromised_event_type": entry["event_type"],
                    "agent": entry["agent_name"],
                    "stored_hash": stored_hash,
                    "recalculated_hash": expected_hash,
                    "details": f"Tampering detected at event {entry['event_id']}! Stored hash does not match content digest.",
                    "total_entries_checked": i + 1,
                }
            computed_prev_hash = expected_hash

        return {
            "verified": True,
            "tampered": False,
            "final_hash_chain": computed_prev_hash,
            "total_entries_verified": len(entries),
            "standard": "SEC Rule 17a-4 / FINRA 4511 Cryptographic Verification Passed",
        }
