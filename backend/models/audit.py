from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import hashlib


def _sanitize_for_serialization(val: Any) -> Any:
    """Recursively convert numpy arrays, numpy scalars, and other non-JSON types to Python primitives."""
    if isinstance(val, dict):
        return {str(k): _sanitize_for_serialization(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [_sanitize_for_serialization(v) for v in val]
    elif hasattr(val, "tolist"):
        return val.tolist()
    elif hasattr(val, "item"):
        return val.item()
    return val


class AuditEntry(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: str
    agent_name: str
    input_summary: str
    output_summary: str
    reasoning_chain: str
    compliance_status: Literal['PASS', 'FAIL', 'WARNING', 'INFO']
    proposal_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def sanitize_metadata(cls, v: Any) -> Any:
        if v is None:
            return {}
        return _sanitize_for_serialization(v)

class ComplianceLedger(BaseModel):
    proposal_id: str
    client_id: str
    entries: List[AuditEntry]
    created_at: datetime
    hash_chain: str
    overall_status: str

    def compute_hash(self) -> str:
        data_to_hash = []
        for entry in self.entries:
            data_to_hash.append(entry.model_dump_json())
        hash_input = "".join(data_to_hash)
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
