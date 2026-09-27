"""Lyzr Multi-Agent Wealth Advisory System Agents Package.

Contains agent definitions for:
- ManagerAgent: Top-level fiduciary orchestrator
- ProfilerAgent: IPS/KYC parser & risk profiling specialist
- MacroAgent: Market regime & macroeconomic analysis specialist
- AllocatorAgent: Strategic target allocation specialist
- RebalancerAgent: Quantitative portfolio rebalancing specialist (CVXPY optimizer tool)
- SuitabilityAgent: FINRA & SEC regulatory suitability compliance gatekeeper
"""
import os
import sys

# Ensure root and backend directories are accessible for agents
_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_AGENTS_DIR)
_BACKEND_DIR = os.path.join(_ROOT_DIR, "backend")

for p in [_ROOT_DIR, _BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from .agent_factory import AgentFactory
from .profiler_agent import ProfilerAgent
from .macro_agent import MacroAgent
from .allocator_agent import AllocatorAgent
from .rebalancer_agent import RebalancerAgent
from .suitability_agent import SuitabilityAgent
from .manager_agent import ManagerAgent

__all__ = [
    "AgentFactory",
    "ProfilerAgent",
    "MacroAgent",
    "AllocatorAgent",
    "RebalancerAgent",
    "SuitabilityAgent",
    "ManagerAgent",
]
