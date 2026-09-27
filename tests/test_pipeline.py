"""End-to-end integration tests for Safe Wealth Advisory pipeline and AIMS audit trails."""
import pytest
from services.pipeline import AdvisoryPipeline


def test_full_pipeline_run():
    """Verify entire 5-agent pipeline executes smoothly and produces verified ledger."""
    pipeline = AdvisoryPipeline()
    proposal, ledger = pipeline.run_advisory(use_mock_prices=True)

    # Validate Proposal
    assert proposal is not None
    assert proposal.proposal_id.startswith("PROP-")
    assert proposal.risk_score >= 1 and proposal.risk_score <= 10
    assert len(proposal.trades) > 0
    assert proposal.suitability_report is not None
    assert len(proposal.suitability_report.checks) == 12

    # Validate AIMS Ledger
    assert ledger is not None
    assert ledger.proposal_id == proposal.proposal_id
    assert len(ledger.entries) >= 5 # Ingestion, Profiler, Macro, Allocator, Rebalancer, Suitability, Ledger
    assert len(ledger.hash_chain) == 64 # SHA-256 hex string length

    # Verify Cryptographic Tamper-Evidence
    verification = pipeline.aims.verify_integrity(proposal.proposal_id)
    assert verification["verified"] is True
    assert verification["hash_chain"] == ledger.hash_chain


def test_stress_test_and_tlh_scans():
    """Verify market shock simulator and tax loss harvesting tools work."""
    pipeline = AdvisoryPipeline()
    portfolio = pipeline.load_sample_portfolio(use_mock_prices=True)
    proposal, _ = pipeline.run_advisory(portfolio=portfolio, use_mock_prices=True)

    # Stress testing
    stress_results = pipeline.run_stress_test(portfolio, proposal)
    assert "2008 Global Financial Crisis" in stress_results
    assert "2020 COVID Liquidity Shock" in stress_results
    assert "2022 Inflation & Rate Hike Surge" in stress_results

    # Tax Loss Harvesting
    tlh_results = pipeline.run_tax_loss_harvesting_scan(portfolio)
    assert isinstance(tlh_results, list)
