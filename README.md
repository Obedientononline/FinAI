# 🏛️ Safe Wealth Advisory & Governed Portfolio Rebalancer

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Netlify-00AD9F?style=for-the-badge&logo=netlify)](https://wealth-advisory-ai.netlify.app/)
[![Lyzr Agent API](https://img.shields.io/badge/Lyzr-Agent%20API-0052FF?style=flat-square)](https://www.lyzr.ai/)
[![Lyzr Safe AI](https://img.shields.io/badge/Lyzr-Safe%20AI%20Guardrails-00C853?style=flat-square)](https://www.lyzr.ai/)
[![Lyzr AIMS](https://img.shields.io/badge/Lyzr-AIMS%20SEC%20Audit-7C4DFF?style=flat-square)](https://www.lyzr.ai/)
[![FINRA Suitability](https://img.shields.io/badge/FINRA-Rule%202111%20%26%20Reg%20BI-FF6D00?style=flat-square)](https://www.finra.org/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)](https://www.python.org/)

> 🌐 **Live Deployment Portal:** [https://wealth-advisory-ai.netlify.app/](https://wealth-advisory-ai.netlify.app/)
>
> **Fiduciary multi-agent wealth assistant that profiles IPS/KYC, rebalances with deterministic quadratic math, enforces FINRA suitability via Lyzr Safe AI, and produces advisor-ready trade proposals with verifiable Lyzr AIMS audit trails.**

---

## 🎯 Executive Summary & Opportunity

Registered Investment Advisers (RIAs) balance KYC risk tiers, tax drag, asset allocation models, and strict SEC / FINRA suitability across thousands of client portfolios. 

Autonomous AI advisors pose catastrophic enterprise risks:
1. **Unsuitable Recommendations:** Hallucinated asset allocations breaching client risk capacity or investor age limits.
2. **Non-Deterministic Trade Math:** LLMs calculating trade share counts or dollar values (inherently probabilistic and prone to arithmetic failure).
3. **Missing Audit Trails:** Inability to produce tamper-evident reasoning records during SEC regulatory examinations.

### Our Solution
**Safe Wealth Advisory** bridges the production enterprise gap through a governed **Hybrid Architecture**:
- **Probabilistic LLM Agents (Lyzr Agent API)** for cognitive analysis: IPS/KYC interpretation, macro regime assessment, and fiduciary briefing generation.
- **Deterministic Quadratic Programming (CVXPY / OSQP)** for trade mathematics: Exact, auditable, share-level buy/sell calculations minimizing tracking error and tax friction.
- **Hard Regulatory Gates (Lyzr Safe AI)**: 12 non-negotiable FINRA Reg BI & IPS compliance checks with absolute veto authority.
- **Cryptographic Auditability (Lyzr AIMS)**: Immutable SHA-256 hash chains complying with SEC Rule 17a-4 and FINRA Rule 4511 Books and Records standards.

---

## 🏗️ Multi-Agent Architecture

```
                                ┌──────────────────────────────────────────────┐
                                │             01. CLIENT INGEST                │
                                │  IPS Constraints, KYC Data, Active Holdings  │
                                └──────────────────────┬───────────────────────┘
                                                       │
                                                       ▼
                                ┌──────────────────────────────────────────────┐
                                │       00. WEALTH ADVISORY ORCHESTRATOR       │
                                │           (Lyzr Manager Agent API)           │
                                └──────┬───────────────┬───────────────┬───────┘
                                       │               │               │
                 ┌─────────────────────┴────────┐      │      ┌────────┴────────────────────┐
                 ▼                              ▼      │      ▼                             ▼
   ┌───────────────────────────┐ ┌───────────────────┐ │ ┌────────────────────────┐ ┌─────────────────────────┐
   │    01. PROFILER AGENT     │ │  02. MACRO AGENT  │ │ │  04. REBALANCER AGENT  │ │  05. SUITABILITY AGENT   │
   │ Deterministic 1-10 Score  │ │ Macro Regime &    │ │ │ CVXPY Quadratic Solver │ │ Lyzr Safe AI 12 Checks   │
   │ Fiduciary Risk Tier       │ │ Sector Tilts      │ │ │ Exact Integer Shares   │ │ Zero IPS Violation Veto  │
   └─────────────┬─────────────┘ └─────────┬─────────┘ │ └────────────┬───────────┘ └────────────┬────────────┘
                 │                         │           │              │                          │
                 └────────────┬────────────┘           │              │                          │
                              ▼                        │              │                          │
                 ┌─────────────────────────┐           │              │                          │
                 │   03. ALLOCATOR AGENT   │───────────┘              │                          │
                 │ Strategic Target Mix    │                          │                          │
                 │ Equities / FI / Comm / $│                          │                          │
                 └─────────────────────────┘                          │                          │
                                                                      ▼                          ▼
                                                       ┌──────────────────────────────────────────────┐
                                                       │           05. ADVISOR DOSSIER & AIMS         │
                                                       │ • 1-Click RIA Execution Portal               │
                                                       │ • Formal PDF Compliance Proposal             │
                                                       │ • Immutable Lyzr AIMS SHA-256 Hash Chain     │
                                                       └──────────────────────────────────────────────┘
```

---

## 🌟 Key Standout Innovations for Hackathon Judges

1. **Relational SQLite Database & 8 FINRA Test Archetypes:** No toy JSON files. Full relational SQLite schema (`clients`, `ips`, `kyc`, `holdings`, `proposals`, `audit_entries`) seeded with 8 diverse clients specifically engineered to test and trip all 12 FINRA suitability rules.
2. **Deterministic Mathematical Proofs (CVXPY / OSQP):** Includes closed-form known-answer analytical benchmarks in the test suite proving optimal weights match analytical solutions down to $10^{-4}$ precision.
3. **2020–2024 Empirical Backtest Harness:** Monthly backtest over 5 historical years (COVID-19, 2021 bull market, 2022 rate hikes) demonstrating bounded tracking error ($1.2\%$ vs $14.8\%$ unmanaged drift) and quantified downside protection.
4. **Lyzr AIMS Live Tamper-Detection Engine:** Live SHA-256 hash chaining with a 1-click "Deliberately Tamper with Record" demo that catches database tampering in real time.
5. **Mock SEC Regulatory Compliance Memo:** Professional one-pager ([`docs/MOCK_SEC_EXAM_MEMO.md`](docs/MOCK_SEC_EXAM_MEMO.md)) reviewing the system against SEC Reg BI and FINRA Rule 2111.
6. **Architecture Decision Record (ADR-001):** Fiduciary technical rationale ([`docs/ARCHITECTURE_DECISION_RECORD.md`](docs/ARCHITECTURE_DECISION_RECORD.md)) detailing why hybrid LLM + deterministic optimization eliminates generative financial math failures.

---

## 👥 The 8 Seeded Relational Clients (Engineered FINRA Tripwires)

| Client ID | Client Name | Risk Tier & Profile | Engineered Regulatory Tripwire |
| :---: | :--- | :--- | :--- |
| `C-2026-001` | **Jane Doe** | Moderate (Score 5/10), 15y horizon | **Benchmark Compliant** (Passes all 12 FINRA suitability checks). |
| `C-2026-002` | **Robert Miller** | Senior 74yo, self-stated aggressive | **Trips `FINRA-007` & `FINRA-001`** (Senior Safeguard: age $70+$ capped at $\le 40\%$ equity). |
| `C-2026-003` | **Chad Sullivan** | 29yo, holds $300\text{k}$ DOGE & $50\text{M}$ SHIB | **Trips `FINRA-005`** (Blocked Assets: meme coins and speculative assets blocked). |
| `C-2026-004` | **Eleanor Vance** | 58yo, High Liquidity Needs, $0.2\%$ cash | **Trips `FINRA-003`** (Mandatory Cash Buffer: high liquidity requires $\ge 15\%$ cash). |
| `C-2026-005` | **Arthur Pendelton** | Tech executive, $46\%$ AAPL position | **Trips `FINRA-004`** (Single-Asset Concentration: exceeds $10\%$ IPS ceiling). |
| `C-2026-006` | **Heritage Charity Trust** | Institutional trust, "no tobacco" IPS | **Trips `FINRA-008`** (IPS Negative Screening: attempts to hold Altria / MO). |
| `C-2026-007` | **Howard Sterling** | HNW $>\$5\text{M}$ AUM, $100\%$ US Equities | **Trips `FINRA-011`** (Multi-Asset Diversification: portfolios $>\$500\text{k}$ need $\ge 4$ classes). |
| `C-2026-008` | **Dave Turner** | High churn, sells VWO at loss in 14 days | **Trips `FINRA-012` & `FINRA-009`** (Wash-Sale 30-day window & excessive turnover). |

---

## 🛡️ Lyzr Capabilities & Rubric Alignment (100 Pts)

| Rubric Pillar | Weight | Implementation Details |
| :--- | :---: | :--- |
| **Lyzr Framework Integration** | **30%** | • **Lyzr Agent API:** 5 specialized subagents orchestrated via Manager API (`managed_agents`).<br>• **Lyzr Safe AI:** Hard compliance boundaries screening out-of-policy assets and enforcing risk ceilings.<br>• **Lyzr AIMS:** Tamper-evident ledger hashing all multi-agent prompts, tools, decisions, and approval states. |
| **Financial Logic & Suitability** | **30%** | • **Zero IPS Violations:** Hard-coded mathematical boundaries prevent breach.<br>• **Deterministic Math:** CVXPY quadratic optimizer solves $\min \|w - w_t\|^2 + \lambda \sum |w - w_c| c_i$.<br>• **12 FINRA Rules:** Equity caps, cash buffers, concentration limits, blocked meme assets, wash-sale avoidance. |
| **Code Modularity & Tests** | **20%** | • Clean package segregation (`agents/`, `engine/`, `guardrails/`, `models/`, `services/`, `ui/`, `tests/`).<br>• Pydantic v2 type safety across all workflows.<br>• Automated test suite covering mathematical solving, suitability breaches, and end-to-end execution. |
| **Wealth Manager UI/UX** | **20%** | • Enterprise-grade Streamlit portal designed for RIA wealth managers.<br>• Plotly interactive transitions, real-time drift gauges, 1-click execution, and official PDF export.<br>• **Historical Stress Tester:** Replays 2008 GFC, 2020 COVID shock, and 2022 Inflation rate hikes. |

---

## ⚖️ The 12-Rule FINRA Suitability & Safe AI Matrix

Our **Suitability Agent** acts as the firm's Chief Compliance Officer with absolute veto authority:

| Rule ID | Regulatory Check | Severity | Enforcement Logic |
| :--- | :--- | :---: | :--- |
| `FINRA-001` | **Equity Cap Enforcement** | **CRITICAL** | Conservative $\le 20\%$, Mod. Conservative $\le 35\%$, Moderate $\le 55\%$, Mod. Aggressive $\le 70\%$, Aggressive $\le 90\%$. |
| `FINRA-002` | **Equity Floor Appropriateness** | **WARNING** | Flags portfolios failing minimum growth participation for aggressive profiles (Min $50\%$). |
| `FINRA-003` | **Mandatory Cash Buffer** | **CRITICAL** | High Liquidity $\ge 15\%$ cash, Moderate $\ge 7\%$, Low $\ge 2\%$. Prevents forced liquidation during drawdowns. |
| `FINRA-004` | **Single-Asset Concentration** | **CRITICAL** | No single security position may exceed IPS limit (Default: $\le 10\%$). Mitigates idiosyncratic risk. |
| `FINRA-005` | **Blocked Assets Filter** | **CRITICAL** | Blocks meme coins (`DOGE`, `SHIB`, `PEPE`), penny stocks ($<\$5$), and speculative 0DTE options. |
| `FINRA-006` | **Horizon-Duration Match** | **CRITICAL** | Short horizon ($<3\text{ yrs}$) capped at $\le 30\%$ equities to protect against sequence-of-returns risk. |
| `FINRA-007` | **Senior Investor Safeguard** | **CRITICAL** | Age $70+$ capped at $\le 40\%$ equities regardless of self-reported risk tolerance (FINRA Senior Rule 2165). |
| `FINRA-008` | **IPS Negative Screening** | **CRITICAL** | Strictly respects client mandates (e.g., `no_tobacco` blocks `MO`, `PM`, `BTI`; `no_firearms` blocks `RGR`, `SWBI`). |
| `FINRA-009` | **Turnover / Churn Limit** | **WARNING** | Total turnover bounded to $\le 25\%$ of AUM per event to prevent unnecessary transaction fees. |
| `FINRA-010` | **Tax Drag Efficiency** | **WARNING** | Flags short-term capital gains exceeding $\$5,000$ to prompt tax-timing or loss-harvesting review. |
| `FINRA-011` | **Multi-Asset Diversification**| **WARNING** | Portfolios $>\$500\text{k}$ must allocate across $\ge 4$ asset classes (Equities, Fixed Income, Commodities, Cash). |
| `FINRA-012` | **Wash Sale Rule Screening** | **CRITICAL** | Enforces IRS 30-day window: Blocks buy orders on assets harvested at a loss within the past 30 days. |

---

## 🧮 Deterministic Financial Engine (NO LLM Math)

The rebalancing engine solves a constrained convex Quadratic Program (QP):

$$\min_{w} \quad \underbrace{\|w - w_{\text{target}}\|_2^2}_{\text{Tracking Error Minimization}} + \lambda \sum_{i=1}^n \underbrace{|w_i - w_{\text{current},i}| \cdot c_i}_{\text{Tax Drag Penalty}}$$

**Subject to:**
1. $\sum_{i=1}^n w_i = 1.0$ *(Fully invested constraint)*
2. $0 \le w_i \le w_{\max}$ *(Long-only and concentration constraints)*
3. $\sum_{i=1}^n |w_i - w_{\text{current},i}| \le 2 \cdot \text{TurnoverLimit}$ *(Churn prevention)*
4. $L_k \le \sum_{i \in \text{Class}_k} w_i \le U_k$ *(Fiduciary asset class bounds from client IPS)*

**Exact Trade Execution:**
Optimal continuous weights are mapped to integer shares:
$$S_i = \text{round}\left(\frac{w_i^* \cdot V_{\text{portfolio}}}{P_i}\right) - S_{\text{current},i}$$
Tax consequences for each sell order are computed deterministically based on FIFO/specific-identification cost basis and holding period ($\le 365$ days = Short Term, $> 365$ days = Long Term).

---

## 📊 Lyzr AIMS SEC Exam Record & Hash Chain

Every pipeline execution generates a cryptographically linked compliance ledger:
```json
{
  "proposal_id": "PROP-20260924-A1B2C3",
  "client_id": "C-2026-001",
  "created_at": "2026-09-24T15:10:00Z",
  "hash_chain": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "overall_status": "FULLY_COMPLIANT",
  "audit_entries": [
    {"event_type": "INGESTION", "status": "PASS"},
    {"event_type": "PROFILING", "status": "PASS"},
    {"event_type": "MARKET_ANALYSIS", "status": "PASS"},
    {"event_type": "ALLOCATION", "status": "PASS"},
    {"event_type": "OPTIMIZATION", "status": "PASS"},
    {"event_type": "SUITABILITY_CHECK", "status": "PASS"},
    {"event_type": "ADVISOR_DECISION", "status": "PASS"}
  ]
}
```
Any modification to an agent's reasoning chain or mathematical outputs alters the downstream SHA-256 hash, immediately flagging tamper evidence during an SEC examination.

---

## 🚀 Quickstart & Installation

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/Obedientononline/FinAI.git
cd FinAI
python -m venv venv
venv\Scripts\activate   # Windows
# or source venv/bin/activate # Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys (Optional for Simulation Mode)
```bash
cp .env.example .env
```
Edit `.env`:
```ini
LYZR_AGENT_API_KEY=your_lyzr_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```
*Note: The platform features a built-in simulation mode that runs deterministically even without external API credentials.*

### 4. Run the Automated Test Suite
```bash
python -m pytest tests/ -v
```

### 5. Launch the Platform

#### Unified Web Portal (Flask RIA Portal)
```bash
python app.py
# or: python backend/app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

#### Interactive Client UI (Streamlit)
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

#### Multi-Service Docker Run
```bash
docker-compose up --build
```

---

## 🎬 3-Minute Hackathon Demo Script

| Timestamp | Screen / View | Action & Narrative |
| :---: | :--- | :--- |
| **0:00 - 0:30** | **Slide / Intro** | *"RIAs manage thousands of portfolios under strict fiduciary duty. Traditional LLMs are catastrophic for wealth management because they hallucinate trades and fail math. We built Safe Wealth Advisory on Lyzr Agent API & Safe AI."* |
| **0:30 - 1:00** | **Tab 1: Client Intake** | Select Jane Doe. Show the **real-time deterministic risk scoring gauge (1-10)** deriving score 5/10 and imposing an equity ceiling $\le 55\%$ and cash buffer $\ge 7\%$. |
| **1:00 - 1:40** | **Tab 3: Trade Proposal** | Show the **CVXPY deterministic trade orders** with exact integer shares and tax impact. Show the Before vs. After allocation bar chart. |
| **1:40 - 2:15** | **Sidebar: Stress Injection** | Select **"Inject Blocked Meme Asset (DOGE)"** or **"Conservative Client Over-Allocation"**. Hit Re-run. Watch **Lyzr Safe AI INSTANTLY BLOCK execution** and display the red FINRA violation alert. |
| **2:15 - 2:45** | **Tab 4: Lyzr AIMS** | Show the **SEC Exam Audit Ledger** with verified SHA-256 hash chains, chronological multi-agent reasoning steps, and 1-click JSON export. |
| **2:45 - 3:00** | **Tab 3: Actions** | Hit **"1-Click Approve & Execute"** with advisor sign-off notes, and click **"Download Proposal PDF"** showing the presentation-ready document. |

---

## 📁 Required Repository Structure

```
your-repo/
├── agents/                     # Lyzr agents, configs, orchestration
│   ├── __init__.py             # Agent package exports & sys.path setup
│   ├── agent_factory.py        # Lyzr Agent API client & agent registration
│   ├── profiler_agent.py       # Agent 1: Fiduciary Profiling & Risk Scoring
│   ├── macro_agent.py          # Agent 2: Macroeconomic Regime Analyst
│   ├── allocator_agent.py      # Agent 3: Strategic Asset Allocation Specialist
│   ├── rebalancer_agent.py     # Agent 4: Quantitative Rebalancer (CVXPY tool)
│   ├── suitability_agent.py    # Agent 5: FINRA Suitability & Safe AI Gatekeeper
│   ├── manager_agent.py        # Orchestrator: End-to-end multi-agent coordinator
│   └── README.md               # Agents layer documentation
│
├── frontend/                   # UI / app clients that call agents
│   ├── app.py                  # Interactive Streamlit wealth advisory client
│   ├── templates/              # Jinja2 HTML templates for RIA advisor portal
│   │   ├── base.html           # Layout shell & navigation
│   │   ├── dashboard.html      # Portfolio overview & metrics
│   │   ├── client.html         # Client intake & risk profile
│   │   ├── proposal.html       # Rebalancing trades & allocation comparison
│   │   ├── audit.html          # Lyzr AIMS cryptographic audit chain
│   │   ├── analysis.html       # Backtest & benchmark analytics
│   │   └── upload.html         # KYC & IPS document ingestion wizard
│   ├── static/                 # Stylesheets (CSS) & JavaScript charts
│   ├── ui/                     # Modular Streamlit views (intake, dashboard, etc.)
│   └── README.md               # Frontend layer documentation
│
├── backend/                    # APIs, services, integrations
│   ├── app.py                  # Flask REST API & web service
│   ├── config.py               # Financial boundaries & API configurations
│   ├── seed_clients.py         # Relational database client seeder
│   ├── requirements.txt        # Backend dependencies
│   ├── services/               # High-level business logic & pipelines
│   │   ├── pipeline.py         # Unified end-to-end advisory pipeline
│   │   ├── document_parser.py  # OCR / PDF / DOCX client document parser
│   │   ├── aims_logger.py      # Lyzr AIMS SHA-256 cryptographic audit ledger
│   │   └── proposal_generator.py # Formal compliance PDF generator
│   ├── engine/                 # Deterministic quantitative computation
│   │   ├── optimizer.py        # CVXPY Quadratic Program & SLSQP solver
│   │   ├── risk_scorer.py      # Mathematical risk scoring engine (1-10)
│   │   ├── backtester.py       # 5-Year empirical backtest harness
│   │   └── market_data.py      # Live market data feeds & cache
│   ├── guardrails/             # Lyzr Safe AI Regulatory Policy
│   │   ├── suitability_rules.py # 12 FINRA Reg BI suitability checks
│   │   └── blocked_assets.json # Blacklisted meme coins & speculative assets
│   ├── database/               # Relational SQLite persistence layer
│   │   ├── schema.py           # Relational table DDL & connection manager
│   │   └── repository.py       # Data access object (CRUD operations)
│   ├── models/                 # Strongly-typed Pydantic v2 domain models
│   │   ├── client_profile.py   # IPS, KYC, ClientProfile models
│   │   ├── portfolio.py        # Position, Portfolio, TradeOrder models
│   │   ├── proposal.py         # TradeProposal, SuitabilityReport models
│   │   └── audit.py            # AuditEntry, ComplianceLedger models
│   ├── data/                   # Relational database & sample datasets
│   └── README.md               # Backend layer documentation
│
├── tests/                      # Automated Verification Suite (42 tests)
│   ├── conftest.py             # Pytest discovery & environment setup
│   ├── test_all_12_suitability_rules.py # Tests 12 FINRA suitability gates
│   ├── test_aims_tamper_detection.py    # Tests live SHA-256 tamper detection
│   ├── test_closed_form_benchmark.py   # Tests CVXPY analytical proof
│   ├── test_optimizer.py       # Tests quadratic rebalancing & exact shares
│   ├── test_backtester.py      # Tests 5-year empirical backtest harness
│   ├── test_pipeline.py        # Tests end-to-end multi-agent pipeline
│   ├── test_risk_scorer.py     # Tests deterministic risk scoring logic
│   └── test_suitability.py     # Tests suitability filters & veto authority
│
├── docs/                       # Regulatory & Architectural Documentation
│   ├── ARCHITECTURE_DECISION_RECORD.md # ADR-001 Hybrid Architecture Rationale
│   └── MOCK_SEC_EXAM_MEMO.md   # Regulatory review memo
│
├── Dockerfile                  # Container build
├── docker-compose.yml          # Local multi-service run (backend + frontend)
├── .env.example                # Environment keys template (no secrets)
├── README.md                   # Setup, run, architecture notes
├── requirements.txt            # Root dependencies
├── app.py                      # Root convenience runner
└── run.py                      # Root convenience script
```

---

## 🏆 Fiduciary Standards & Legal Disclaimers

Safe Wealth Advisory is engineered to operate in strict alignment with:
- **Investment Advisers Act of 1940:** Fiduciary duty to put client interests first at all times.
- **SEC Regulation Best Interest (Reg BI):** Enhanced care, disclosure, and conflict mitigation.
- **FINRA Rule 2111 (Suitability):** Quantitative, customer-specific, and reasonable-basis suitability standards.
- **SEC Rule 17a-4 / FINRA Rule 4511:** Electronic records preservation in write-once-read-many (WORM) tamper-evident storage.
