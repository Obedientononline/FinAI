# ⚙️ Backend Services, APIs & Deterministic Engines

This directory contains the core backend services, REST API endpoints, deterministic mathematical engines, regulatory guardrails, database persistence, and models.

## 📁 Directory Structure

| Module | Purpose |
| :--- | :--- |
| **`app.py`** | Flask REST API & web service providing endpoints for pipeline execution, document parsing, backtesting, and PDF export. |
| **`services/`** | Orchestration pipeline (`pipeline.py`), multi-format document parser OCR/PDF (`document_parser.py`), Lyzr AIMS SHA-256 logger (`aims_logger.py`), and compliance PDF generator (`proposal_generator.py`). |
| **`engine/`** | Deterministic CVXPY/OSQP quadratic optimizer (`optimizer.py`), risk scoring algorithms (`risk_scorer.py`), 5-year empirical backtest engine (`backtester.py`), and market data cache (`market_data.py`). |
| **`guardrails/`** | Hard-coded deterministic FINRA Reg BI & IPS suitability verification rules (`suitability_rules.py`). |
| **`database/`** | SQLite relational persistence layer (`schema.py`, `repository.py`). |
| **`models/`** | Pydantic data schemas for client profiles, portfolios, trade proposals, and audit records. |
| **`data/`** | Relational database (`wealth_advisory.db`), seeded client archetypes, historical price cache, and sample documents. |

## 🚀 Running the Backend Service

```bash
python backend/app.py
```
Or with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 backend.app:app
```
