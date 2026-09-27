"""SQLite database schema and connection management for Safe Wealth Advisory."""
import os
import sqlite3
from typing import Optional

# Check if running in a serverless environment (Netlify / AWS Lambda) or read-only filesystem
_root_dir = os.path.dirname(os.path.dirname(__file__))
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("NETLIFY") or not os.access(_root_dir, os.W_OK):
    DB_DIR = os.path.join("/tmp", "wealth_advisory_data")
else:
    DB_DIR = os.path.join(_root_dir, "data")

DB_PATH = os.path.join(DB_DIR, "wealth_advisory.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns an active SQLite database connection with row factory enabled."""
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # If in serverless and template DB exists, copy it over to /tmp if not already present
    src_db = os.path.join(_root_dir, "data", "wealth_advisory.db")
    if target_path != src_db and os.path.exists(src_db) and not os.path.exists(target_path):
        import shutil
        try:
            shutil.copy2(src_db, target_path)
        except Exception:
            pass

    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None):
    """Initializes all relational tables if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    -- Clients Table
    CREATE TABLE IF NOT EXISTS clients (
        client_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- Investment Policy Statement (IPS) Table
    CREATE TABLE IF NOT EXISTS ips (
        client_id TEXT PRIMARY KEY,
        investment_objective TEXT NOT NULL,
        risk_tolerance TEXT NOT NULL,
        time_horizon_years INTEGER NOT NULL,
        liquidity_needs TEXT NOT NULL,
        tax_bracket REAL NOT NULL,
        restrictions TEXT NOT NULL, -- JSON list of strings
        max_single_position_pct REAL NOT NULL,
        rebalance_threshold_pct REAL NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
    );

    -- Know Your Customer (KYC) Table
    CREATE TABLE IF NOT EXISTS kyc (
        client_id TEXT PRIMARY KEY,
        age INTEGER NOT NULL,
        annual_income REAL NOT NULL,
        net_worth REAL NOT NULL,
        investment_experience TEXT NOT NULL,
        employment_status TEXT NOT NULL,
        dependents INTEGER NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
    );

    -- Portfolio Holdings Table
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        shares REAL NOT NULL,
        cost_basis_per_share REAL NOT NULL,
        purchase_date TEXT NOT NULL,
        holding_period_days INTEGER NOT NULL,
        asset_class TEXT NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
    );

    -- Trade Proposals Table
    CREATE TABLE IF NOT EXISTS proposals (
        proposal_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        risk_score INTEGER NOT NULL,
        risk_category TEXT NOT NULL,
        current_allocation TEXT NOT NULL, -- JSON dict
        target_allocation TEXT NOT NULL,  -- JSON dict
        trades TEXT NOT NULL,             -- JSON list of trade dicts
        total_buy_value REAL NOT NULL,
        total_sell_value REAL NOT NULL,
        net_tax_impact REAL NOT NULL,
        suitability_passed INTEGER NOT NULL, -- 1 or 0
        suitability_report TEXT NOT NULL, -- JSON dict
        market_analysis TEXT NOT NULL,
        allocation_rationale TEXT NOT NULL,
        advisor_approved INTEGER,         -- 1, 0, or NULL
        advisor_notes TEXT,
        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
    );

    -- Lyzr AIMS Audit Entries Table
    CREATE TABLE IF NOT EXISTS audit_entries (
        event_id TEXT PRIMARY KEY,
        proposal_id TEXT,
        client_id TEXT,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        input_summary TEXT NOT NULL,
        output_summary TEXT NOT NULL,
        reasoning_chain TEXT NOT NULL,
        compliance_status TEXT NOT NULL,
        metadata TEXT,                    -- JSON dict
        prev_hash TEXT,
        entry_hash TEXT NOT NULL
    );

    -- Indexes for high-performance compliance queries
    CREATE INDEX IF NOT EXISTS idx_holdings_client ON holdings(client_id);
    CREATE INDEX IF NOT EXISTS idx_proposals_client ON proposals(client_id);
    CREATE INDEX IF NOT EXISTS idx_audit_proposal ON audit_entries(proposal_id);
    CREATE INDEX IF NOT EXISTS idx_audit_client ON audit_entries(client_id);
    """)

    conn.commit()
    conn.close()
