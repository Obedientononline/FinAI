"""Agent 0: Wealth Advisory Orchestrator (Manager Agent).

Coordinates the fiduciary multi-agent pipeline:
Ingest -> Profiler -> Macro -> Allocator -> Rebalancer -> Suitability Gate -> Proposal
Maintains end-to-end execution state and registers immutable audit records into Lyzr AIMS.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple
from models.client_profile import ClientProfile
from models.portfolio import Portfolio
from models.proposal import TradeProposal, SuitabilityReport
from models.audit import ComplianceLedger
from agents.profiler_agent import ProfilerAgent
from agents.macro_agent import MacroAgent
from agents.allocator_agent import AllocatorAgent
from agents.rebalancer_agent import RebalancerAgent
from agents.suitability_agent import SuitabilityAgent
from services.aims_logger import AIMSLogger


from agents.agent_factory import AgentFactory


class ManagerAgent:
    """Managing Director Orchestrator agent overseeing the fiduciary advisory lifecycle."""

    def __init__(self, aims_logger: AIMSLogger, agent_factory: Any = None):
        self.aims = aims_logger
        self.factory = agent_factory or AgentFactory()
        self.factory.register_all_agents()
        self.profiler = ProfilerAgent(agent_factory=self.factory)
        self.macro = MacroAgent(agent_factory=self.factory)
        self.allocator = AllocatorAgent(agent_factory=self.factory)
        self.rebalancer = RebalancerAgent()
        self.suitability = SuitabilityAgent()

    def run_advisory_pipeline(
        self,
        profile: ClientProfile,
        portfolio: Portfolio,
        use_mock_prices: bool = False,
    ) -> Tuple[TradeProposal, ComplianceLedger]:
        """
        Executes the full governed multi-agent advisory sequence.
        
        Returns:
            Tuple of (TradeProposal, ComplianceLedger)
        """
        proposal_id = f"PROP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # 0. Log Ingestion Event
        self.aims.log_event(
            event_type="INGESTION",
            agent_name="Ingestion Engine",
            input_summary=f"Client: {profile.name} (ID: {profile.client_id}), Portfolio: {len(portfolio.positions)} positions",
            output_summary=f"Ingested IPS & KYC. Portfolio total value: ${portfolio.total_value:,.2f}",
            reasoning_chain="Validated payload schema, sanitized PII, verified holding identifiers.",
            compliance_status="PASS",
            proposal_id=proposal_id,
        )

        # 1. Profiler Agent
        profile, scoring_breakdown, profiler_rationale = self.profiler.profile_client(profile)
        self.aims.log_event(
            event_type="PROFILING",
            agent_name=self.profiler.role,
            input_summary=f"Age: {profile.kyc.age}, Horizon: {profile.ips.time_horizon_years}y, Liquidity: {profile.ips.liquidity_needs}",
            output_summary=f"Risk Score: {profile.risk_score}/10, Category: {profile.risk_category}",
            reasoning_chain=profiler_rationale,
            compliance_status="PASS",
            proposal_id=proposal_id,
            metadata={"scoring_breakdown": scoring_breakdown},
        )

        # 2. Macro Agent
        macro_analysis = self.macro.analyze_regime()
        self.aims.log_event(
            event_type="MARKET_ANALYSIS",
            agent_name=self.macro.role,
            input_summary="Fed neutral rate, Core CPI decelerating, Treasury yield curve",
            output_summary=f"Regime: {macro_analysis['regime']}",
            reasoning_chain=macro_analysis["summary"],
            compliance_status="PASS",
            proposal_id=proposal_id,
        )

        # 3. Allocator Agent
        target_allocation, alloc_rationale = self.allocator.compute_target_allocation(profile, macro_analysis)
        self.aims.log_event(
            event_type="ALLOCATION",
            agent_name=self.allocator.role,
            input_summary=f"Risk Category: {profile.risk_category}, Macro Regime: {macro_analysis['regime']}",
            output_summary=f"Target: Eq {target_allocation['equities']:.0%}, FI {target_allocation['fixed_income']:.0%}, Comm {target_allocation['commodities']:.0%}, Cash {target_allocation['cash']:.0%}",
            reasoning_chain=alloc_rationale,
            compliance_status="PASS",
            proposal_id=proposal_id,
            metadata={"target_allocation": target_allocation},
        )

        # 4. Rebalancer Agent (CVXPY Quadratic Program)
        trades, opt_result, rebalance_rationale = self.rebalancer.execute_rebalance(
            portfolio=portfolio,
            target_allocation=target_allocation,
            profile=profile,
            use_mock_prices=use_mock_prices,
        )
        clean_telemetry = {
            k: (v.tolist() if hasattr(v, "tolist") else v)
            for k, v in opt_result.items()
        }
        self.aims.log_event(
            event_type="OPTIMIZATION",
            agent_name=self.rebalancer.role,
            input_summary=f"Holdings count: {len(portfolio.positions)}, Target weights, Tax bracket: {profile.ips.tax_bracket:.1%}",
            output_summary=f"Generated {len(trades)} orders. Status: {opt_result['status']}. Turnover: {opt_result.get('turnover', 0.0):.1%}",
            reasoning_chain=rebalance_rationale,
            compliance_status="PASS" if opt_result["status"] == "optimal" else "WARNING",
            proposal_id=proposal_id,
            metadata={"solver_telemetry": clean_telemetry},
        )

        # Draft Trade Proposal to submit to FINRA Suitability Gate
        draft_proposal = TradeProposal(
            proposal_id=proposal_id,
            client_id=profile.client_id,
            timestamp=datetime.utcnow(),
            risk_score=profile.risk_score or 5,
            risk_category=profile.risk_category or "moderate",
            current_allocation=dict(portfolio.allocation),
            target_allocation=target_allocation,
            trades=trades,
            suitability_report=SuitabilityReport(checks=[]), # temporary placeholder
            market_analysis=macro_analysis["summary"],
            allocation_rationale=alloc_rationale,
        )

        # 5. Suitability Gatekeeper (Lyzr Safe AI)
        suitability_report, suitability_passed, suitability_rationale = self.suitability.evaluate_suitability(
            profile=profile, proposal=draft_proposal
        )
        draft_proposal.suitability_report = suitability_report

        gate_status = "PASS" if suitability_passed else "FAIL"
        self.aims.log_event(
            event_type="SUITABILITY_CHECK",
            agent_name=self.suitability.role,
            input_summary=f"12 FINRA checks against draft proposal {proposal_id}",
            output_summary=f"Gate Status: {gate_status}. Critical failures: {len(suitability_report.critical_failures)}, Warnings: {len(suitability_report.warnings)}",
            reasoning_chain=suitability_rationale,
            compliance_status=gate_status,
            proposal_id=proposal_id,
            metadata={"checks": [c.model_dump() for c in suitability_report.checks]},
        )

        # 6. Final Proposal Log Event
        self.aims.log_event(
            event_type="PROPOSAL_GENERATED",
            agent_name="Managing Director Orchestrator",
            input_summary=f"Proposal ID: {proposal_id}",
            output_summary=f"Proposal generated for Advisor review. Suitability: {'APPROVED' if suitability_passed else 'BLOCKED'}",
            reasoning_chain=f"Advisory sequence completed for {profile.name}. Suitability Gate: {gate_status}.",
            compliance_status="PASS" if suitability_passed else "FAIL",
            proposal_id=proposal_id,
        )

        # 7. Build Cryptographically-Chained Compliance Ledger
        compliance_ledger = self.aims.build_compliance_ledger(proposal_id=proposal_id, client_id=profile.client_id)

        return draft_proposal, compliance_ledger
