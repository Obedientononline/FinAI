"""Lyzr Agent Factory.

Handles registration and initialization of all fiduciary advisory agents with
the Lyzr Agent API and Lyzr Safe AI ecosystem.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import config

logger = logging.getLogger(__name__)

# System prompts for each specialized agent in the fiduciary chain
PROFILER_INSTRUCTIONS = """You are a Certified Financial Planner (CFP) and Fiduciary Risk Profiling Agent in an RIA firm.
Your role is to analyze a client's Investment Policy Statement (IPS) and Know Your Customer (KYC) documentation.
You must:
1. Validate completeness of IPS constraints, horizon, tax bracket, and liquidity needs.
2. Calculate the deterministic risk score (1-10) using mathematical rubric weights.
3. Categorize into risk buckets: Conservative (1-3), Moderate Conservative (4), Moderate (5-6), Moderate Aggressive (7), Aggressive (8-10).
4. Strictly respect any client exclusion requests (e.g. tobacco, firearms, weapons).
Never invent numbers. Follow FINRA Rule 2111 and SEC Reg BI standards."""

MACRO_INSTRUCTIONS = """You are a Chief Investment Strategist and Quantitative Macro Market Analyst.
Your role is to assess the current macroeconomic regime, inflation expectations, yield curve dynamics,
and asset class valuations across Equities, Fixed Income, Commodities, and Cash.
Provide a clear, disciplined perspective on overweight/underweight asset class tilts for the current regime."""

ALLOCATOR_INSTRUCTIONS = """You are a Fiduciary Strategic Asset Allocator.
Your goal is to define target asset class percentage allocations across:
- Equities (Domestic & International)
- Fixed Income (Core & Credit)
- Commodities (Gold & Real Assets)
- Cash & Short-Term Equivalents
Ensure the target allocation strictly honors the client's risk bucket bounds and IPS guidelines.
Conservative clients must NEVER exceed 20% equity."""

REBALANCER_INSTRUCTIONS = """You are a Quantitative Portfolio Rebalancing and Execution Agent.
You operate deterministic quadratic programming tools (CVXPY / OSQP) to compute the exact share-level
trade orders required to transition current holdings to target allocations with minimal tracking error,
turnover limits, and tax drag."""

SUITABILITY_INSTRUCTIONS = """You are the Chief Compliance Officer and FINRA / SEC Suitability Gatekeeper.
Equipped with Lyzr Safe AI Guardrails, you enforce 12 non-negotiable regulatory checks:
1. Equity Cap limits by risk profile
2. Equity Floor appropriateness
3. Mandatory Cash Buffers for liquidity
4. Position Concentration ceilings
5. Blocked Asset screening (meme coins, penny stocks, speculative options)
6. Time Horizon matching
7. Senior Investor Age-based safeguards
8. IPS Restriction compliance (ESG / negative screening)
9. Portfolio Turnover / Churn prevention
10. Short-term Capital Gains tax efficiency
11. Multi-asset diversification requirements
12. 30-day Wash Sale avoidance
You have absolute veto authority. If any critical check fails, you BLOCK the proposal."""

MANAGER_INSTRUCTIONS = """You are the Wealth Advisory Orchestrator.
You coordinate the multi-agent fiduciary workflow:
Client Ingest -> Profiler -> Macro Analyst -> Strategic Allocator -> Quantitative Rebalancer -> FINRA Suitability Gate -> Advisor Proposal.
You ensure auditability across all reasoning steps and register events to Lyzr AIMS."""


class AgentFactory:
    """Factory to create and initialize Lyzr agents."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.LYZR_API_KEY
        self.client = None
        self.is_connected = False
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        
        if self.api_key:
            try:
                from lyzr_python_sdk import LyzrAgentAPI
                self.client = LyzrAgentAPI(api_key=self.api_key)
                self.is_connected = True
                logger.info("Successfully connected to Lyzr Agent API.")
            except Exception as e:
                logger.warning(f"Could not connect to live Lyzr Agent API: {e}. Running in local simulation mode.")

    def register_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Register all 5 pipeline agents + Manager orchestrator."""
        configs = {
            "profiler": {
                "name": "Fiduciary Profiler Agent",
                "role": "Certified Financial Planner",
                "goal": "Accurately score risk and validate IPS parameters according to fiduciary standards.",
                "instructions": PROFILER_INSTRUCTIONS,
            },
            "macro": {
                "name": "Macro Market Analyst Agent",
                "role": "Chief Investment Strategist",
                "goal": "Analyze macroeconomic regime, yield trends, and sector factors.",
                "instructions": MACRO_INSTRUCTIONS,
            },
            "allocator": {
                "name": "Strategic Allocator Agent",
                "role": "Portfolio Strategist",
                "goal": "Determine target asset class weights aligned with risk tier.",
                "instructions": ALLOCATOR_INSTRUCTIONS,
            },
            "rebalancer": {
                "name": "Tax-Aware Rebalancer Agent",
                "role": "Quantitative Portfolio Manager",
                "goal": "Execute deterministic CVXPY optimization to output exact share trade orders.",
                "instructions": REBALANCER_INSTRUCTIONS,
                "tools": ["cvxpy_optimizer", "tax_engine"],
            },
            "suitability": {
                "name": "FINRA Suitability Gatekeeper",
                "role": "Chief Compliance Officer (CCO)",
                "goal": "Enforce 12 FINRA Reg BI checks and Safe AI asset filters.",
                "instructions": SUITABILITY_INSTRUCTIONS,
                "tools": ["finra_suitability_checker", "blocked_asset_filter"],
            },
            "manager": {
                "name": "Wealth Advisory Orchestrator",
                "role": "Managing Director / Lead Orchestrator",
                "goal": "Coordinate multi-agent fiduciary workflow with full AIMS trace.",
                "instructions": MANAGER_INSTRUCTIONS,
            }
        }

        for agent_key, cfg in configs.items():
            if self.is_connected and self.client:
                try:
                    payload = {
                        "name": cfg["name"],
                        "agent_role": cfg["role"],
                        "agent_goal": cfg["goal"],
                        "agent_instructions": cfg["instructions"],
                        "provider_id": config.DEFAULT_PROVIDER,
                        "model": config.DEFAULT_MODEL,
                        "tools": cfg.get("tools", []),
                    }
                    response = self.client.agents.create_agent(agent_config=payload)
                    agent_id = response.get("id", f"lyzr_{agent_key}_id")
                    self.agent_registry[agent_key] = {**cfg, "agent_id": agent_id, "live": True}
                    logger.info(f"Registered {cfg['name']} with Lyzr ID: {agent_id}")
                except Exception as e:
                    logger.warning(f"Failed to register {agent_key} with Lyzr API: {e}. Using simulated ID.")
            else:
                self.agent_registry[agent_key] = {**cfg, "agent_id": f"sim_{agent_key}_id", "live": False}

        return self.agent_registry

    def chat_agent(
        self,
        agent_key: str,
        message: str,
        user_id: str = "advisor@wealthfirm.com",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes inference via the live Lyzr Agent API if connected.
        Implements enterprise resilience fallback if API is unreachable.
        """
        registry_entry = self.agent_registry.get(agent_key, {})
        agent_id = registry_entry.get("agent_id", f"sim_{agent_key}_id")
        is_live = registry_entry.get("live", False)

        if self.is_connected and self.client and is_live:
            try:
                payload = {
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "message": message,
                    "session_id": session_id or f"sess_{agent_key}",
                }
                response = self.client.inference.chat(payload)
                response_text = response.get("response", str(response)) if isinstance(response, dict) else str(response)
                return {
                    "text": response_text,
                    "mode": "LIVE_LYZR_API",
                    "agent_id": agent_id,
                    "status": "SUCCESS"
                }
            except Exception as e:
                logger.warning(
                    f"[PRODUCTION RESILIENCE FALLBACK] Lyzr Agent API call for {agent_key} failed ({e}). "
                    f"Engaging deterministic local fiduciary fallback."
                )

        return {
            "text": None,
            "mode": "RESILIENT_LOCAL_FALLBACK",
            "agent_id": agent_id,
            "status": "FALLBACK"
        }
