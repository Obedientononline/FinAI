import numpy as np
import json
from datetime import datetime, timezone
from models.audit import AuditEntry, ComplianceLedger

def test_audit_entry_with_numpy_serialization():
    # Simulate telemetry containing numpy ndarrays, float64, int64
    opt_result = {
        "optimal_weights": np.array([0.45, 0.35, 0.10, 0.10]),
        "status": "optimal",
        "objective_value": np.float64(0.0123),
        "turnover": np.float64(0.14),
        "solver_stats": {
            "iterations": np.int64(42),
            "residuals": np.array([1e-5, 2e-5]),
        }
    }
    
    entry = AuditEntry(
        event_id="TEST-001",
        timestamp=datetime.now(timezone.utc),
        event_type="OPTIMIZATION",
        agent_name="RebalancerAgent",
        input_summary="Test Input",
        output_summary="Test Output",
        reasoning_chain="Test Reasoning",
        compliance_status="PASS",
        proposal_id="PROP-TEST",
        metadata={"solver_telemetry": opt_result}
    )
    
    # Check that model_dump(mode="json") executes without PydanticSerializationError
    dumped_json_dict = entry.model_dump(mode="json")
    assert isinstance(dumped_json_dict, dict)
    assert isinstance(dumped_json_dict["metadata"]["solver_telemetry"]["optimal_weights"], list)
    assert dumped_json_dict["metadata"]["solver_telemetry"]["optimal_weights"] == [0.45, 0.35, 0.10, 0.10]
    
    # Check that model_dump_json() executes without error
    json_str = entry.model_dump_json()
    assert isinstance(json_str, str)
    assert "0.45" in json_str
    
    # Check compliance ledger hash computation
    ledger = ComplianceLedger(
        proposal_id="PROP-TEST",
        client_id="C-TEST",
        entries=[entry],
        created_at=datetime.now(timezone.utc),
        hash_chain="HASH123",
        overall_status="FULLY_COMPLIANT"
    )
    computed_hash = ledger.compute_hash()
    assert isinstance(computed_hash, str)
    assert len(computed_hash) == 64
