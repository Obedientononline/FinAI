import uuid
import pytest
from services.aims_logger import AIMSLogger
from database.repository import WealthRepository


def test_aims_hash_chain_verification():
    """Verify standard pipeline execution creates a cryptographically verified hash chain."""
    repo = WealthRepository()
    aims = AIMSLogger(repo=repo)
    proposal_id = f"PROP-TEST-{uuid.uuid4().hex[:8]}"
    client_id = "C-TEST-001"

    # Log 3 sequential fiduciary events
    e1 = aims.log_event(
        event_type="PROFILING",
        agent_name="Certified Financial Planner",
        input_summary="Age 42, 15y horizon",
        output_summary="Score 5/10 (Moderate)",
        reasoning_chain="Fiduciary risk assessment completed according to rubric.",
        proposal_id=proposal_id,
        client_id=client_id,
    )
    e2 = aims.log_event(
        event_type="OPTIMIZATION",
        agent_name="Quantitative Rebalancer",
        input_summary="Holdings count: 8",
        output_summary="Optimal solution found via CVXPY",
        reasoning_chain="Minimized tracking error with tax penalty.",
        proposal_id=proposal_id,
        client_id=client_id,
    )
    e3 = aims.log_event(
        event_type="SUITABILITY_CHECK",
        agent_name="Chief Compliance Officer",
        input_summary="12 FINRA rules",
        output_summary="Gate Status: PASS",
        reasoning_chain="Zero suitability violations detected.",
        proposal_id=proposal_id,
        client_id=client_id,
    )

    # Live verification
    res = aims.verify_integrity(proposal_id)
    assert res["verified"] is True
    assert res["tampered"] is False
    assert res["entry_count"] >= 3


def test_aims_live_tamper_detection():
    """Verify deliberate record tampering is caught and flags the exact compromised node."""
    repo = WealthRepository()
    aims = AIMSLogger(repo=repo)
    proposal_id = f"PROP-TAMPER-{uuid.uuid4().hex[:8]}"
    client_id = "C-TEST-002"

    e1 = aims.log_event(
        event_type="PROFILING",
        agent_name="CFP Agent",
        input_summary="Client risk inquiry",
        output_summary="Score 3/10 (Conservative)",
        reasoning_chain="Original authentic fiduciary recommendation: Max 20% equity.",
        proposal_id=proposal_id,
        client_id=client_id,
    )

    # Verify initial chain is intact
    initial_check = aims.verify_integrity(proposal_id)
    assert initial_check["verified"] is True

    # Deliberately inject unauthorized tampering into database
    tamper_success = aims.deliberate_tamper_demo(
        event_id=e1.event_id,
        new_reasoning="MALICIOUS ALTERATION: Change score to 9/10 and permit 90% equities."
    )
    assert tamper_success is True

    # Run integrity verification -> MUST catch the tampered record!
    tamper_check = aims.verify_integrity(proposal_id)
    assert tamper_check["verified"] is False
    assert tamper_check["tampered"] is True
    assert tamper_check["compromised_node"] == e1.event_id
    assert "Tampering detected" in tamper_check["details"]
