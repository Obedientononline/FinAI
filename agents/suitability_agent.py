"""Agent 5: FINRA Suitability Gatekeeper Agent.

Enforces Lyzr Safe AI Fiduciary Guardrails and executes the 12-rule FINRA Reg BI
suitability validation suite. Has strict veto power over any proposal that violates
client IPS parameters, investor age rules, blocked asset lists, or concentration thresholds.
"""
from typing import Tuple
from models.client_profile import ClientProfile
from models.proposal import TradeProposal, SuitabilityReport
from guardrails.suitability_rules import check_all_suitability


class SuitabilityAgent:
    """Chief Compliance Officer (CCO) Agent enforcing FINRA Suitability & Safe AI guardrails."""

    def __init__(self, agent_id: str = "sim_suitability_id"):
        self.agent_id = agent_id
        self.role = "Chief Compliance Officer / Regulatory Gatekeeper"

    def evaluate_suitability(
        self, profile: ClientProfile, proposal: TradeProposal
    ) -> Tuple[SuitabilityReport, bool, str]:
        """
        Runs all 12 FINRA & Safe AI suitability checks on the draft trade proposal.

        Returns:
            Tuple of:
            - SuitabilityReport containing individual rule statuses
            - Boolean passed flag (True if zero critical violations)
            - Compliance rationale narrative
        """
        report = check_all_suitability(profile, proposal)
        passed = report.all_passed

        critical_count = len(report.critical_failures)
        warning_count = len(report.warnings)

        if passed:
            rationale = (
                f"Lyzr Safe AI Compliance Gate: APPROVED.\n"
                f"All {len(report.checks)} FINRA suitability checks passed successfully. "
                f"Zero critical policy violations. {warning_count} advisory warning(s) logged.\n"
                f"Proposal strictly conforms with Client IPS, SEC Reg BI, and fiduciary duty."
            )
        else:
            failures_desc = "; ".join([f"{c.rule_name} ({c.details})" for c in report.critical_failures])
            rationale = (
                f"Lyzr Safe AI Compliance Gate: BLOCKED (VIOLATION DETECTED).\n"
                f"{critical_count} critical suitability violation(s) identified: {failures_desc}.\n"
                f"In accordance with FINRA Rule 2111 and fiduciary mandate, trade proposal execution is inhibited."
            )

        return report, passed, rationale
