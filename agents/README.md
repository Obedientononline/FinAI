# 🤖 Lyzr Agents & Orchestration Layer

This directory contains the Lyzr agent definitions, cognitive pipelines, and multi-agent fiduciary orchestration engine.

## 📁 Agents Overview

| Agent | File | Responsibilities |
| :--- | :--- | :--- |
| **Orchestrator** | `manager_agent.py` | Top-level fiduciary orchestrator, manages workflow state, audits, and pipeline execution. |
| **Agent Factory** | `agent_factory.py` | Configures and instantiates Lyzr Agent API instances with prompt templates and tools. |
| **Profiler Agent** | `profiler_agent.py` | Ingests KYC & IPS inputs, calculates deterministic risk scores (1–10) and assigns fiduciary risk tiers. |
| **Macro Agent** | `macro_agent.py` | Evaluates macroeconomic regimes (inflation, rates, growth) and advises macro asset tilts. |
| **Allocator Agent** | `allocator_agent.py` | Produces strategic target asset allocations (equities, fixed income, commodities, cash). |
| **Rebalancer Agent** | `rebalancer_agent.py` | Integrates with deterministic CVXPY quadratic optimizer to compute trade orders and tax-loss harvesting. |
| **Suitability Agent** | `suitability_agent.py` | Gatekeeper enforcing 12 FINRA Reg BI & IPS compliance rules with veto authority. |

## 🚀 Usage

```python
from agents.manager_agent import ManagerAgent
from models.client_profile import ClientProfile
from models.portfolio import Portfolio

# Instantiate the fiduciary orchestrator
manager = ManagerAgent()
```
