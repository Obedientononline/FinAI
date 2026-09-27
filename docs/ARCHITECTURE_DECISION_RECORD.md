# Architecture Decision Record (ADR-001)

## Title
**ADR-001: Hybrid Cognitive LLM Multi-Agent System with Deterministic Convex Optimization for Wealth Rebalancing**

## Status
**ACCEPTED & IMPLEMENTED** (Production Fiduciary Architecture)

## Context & Problem Statement
Registered Investment Advisers (RIAs) managing retail and institutional portfolios are held to strict statutory fiduciary duty under the **Investment Advisers Act of 1940** and **SEC Regulation Best Interest (Reg BI)**. 

When deploying Artificial Intelligence in financial advisory:
- **Pure LLM Architectures Fail Catastrophically:** LLMs are autoregressive next-token predictors. Asking an LLM to calculate share counts, rebalance weights, or tax liabilities leads to:
  1. *Arithmetic Hallucinations:* Fractional or negative share counts, violating long-only cash constraints.
  2. *Constraint Drifting:* Weights summing to $\ne 1.0$ ($100\%$).
  3. *Unbounded Risk Violations:* Breaching IPS equity caps under market stress.
  4. *Lack of Reproducibility:* The same client prompt produces different portfolio weights on subsequent runs.
- **Pure Quantitative Engines Lack Empathy & Adaptability:** Traditional optimization algorithms cannot parse natural language client life goals, interpret qualitative IPS restrictions ("do not invest in predatory defense contractors"), or produce contextual fiduciary rationales for human advisors.

## Decision
We adopt a **Governed Hybrid Architecture**:
1. **Cognitive Tier (Lyzr Agent API):** 
   - Uses specialized LLM agents for natural-language ingestion, qualitative IPS parsing, macro market regime interpretation, and advisor narrative generation.
   - Operates behind strict input/output schemas with Pydantic v2 validation.
2. **Computational Tier (CVXPY Quadratic Program):**
   - Completely decoupled from LLM inference.
   - Solves a convex Quadratic Program (QP) using the operator-splitting quadratic program (OSQP) solver to find global optimal weights $\min \frac{1}{2}\|w - w_{\text{target}}\|_2^2 + \lambda \sum c_i |w_i - w_{\text{current},i}|$.
   - Converts optimal weights to discrete integer share trade orders deterministically.
3. **Regulatory Gatekeeper Tier (Lyzr Safe AI):**
   - 12 independent, hard-coded FINRA suitability rules with programmatic veto authority.
   - If any critical rule fails, trade transmission is locked.
4. **Audit Tier (Lyzr AIMS):**
   - Forward-chained SHA-256 hash chains across SQLite relational tables for tamper-evident compliance.

```
┌────────────────────────────────────────────────────────┐
│             Lyzr Agent API (Cognitive Tier)            │
│    • IPS/KYC Parser        • Macro Regime Analyst      │
│    • Narrative Generator   • Risk Profiler Agent       │
└───────────────────────────┬────────────────────────────┘
                            │ Structured Parameters
                            ▼
┌────────────────────────────────────────────────────────┐
│        Deterministic Financial Math (CVXPY / OSQP)      │
│    • Convex QP Solver      • Exact Integer Shares      │
│    • Zero Hallucination    • Realized Tax Drag Math    │
└───────────────────────────┬────────────────────────────┘
                            │ Draft Trade Proposal
                            ▼
┌────────────────────────────────────────────────────────┐
│            Lyzr Safe AI (12 FINRA Guardrails)          │
│    • Equity Ceilings       • Senior Safeguards         │
│    • Meme Coin Veto        • Cash Buffer Enforcement   │
└───────────────────────────┬────────────────────────────┘
                            │ Approved Proposal
                            ▼
┌────────────────────────────────────────────────────────┐
│          Lyzr AIMS (Verifiable Cryptographic Ledger)   │
│    • SHA-256 Hash Chain    • SEC Rule 17a-4 Compliance │
│    • Live Tamper Detection • Human Advisor Sign-off    │
└────────────────────────────────────────────────────────┘
```

## Consequences & Mitigations
| Risk / Trade-Off | Mitigation in Architecture |
| :--- | :--- |
| **External API Outage** | Built-in production resilience fallback: If Lyzr API is unreachable, system smoothly executes verified local fiduciary reasoning without freezing trades. |
| **Quadratic Infeasibility** | Strict constraint hierarchy: bounds relaxed gracefully with SLSQP secondary fallback, ensuring zero solver crashes. |
| **Discreet Share Rounding Drift** | Whole share allocation converts residual rounding to cash position, preserving budget equality $\sum w_i = 1.0$. |
