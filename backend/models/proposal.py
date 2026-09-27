from typing import List, Literal, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, model_validator, Field
from .portfolio import TradeOrder

class SuitabilityCheck(BaseModel):
    rule_id: str
    rule_name: str
    description: str = ""
    passed: bool
    details: str
    severity: Literal['critical', 'warning', 'info']

    @property
    def status(self) -> str:
        return "PASS" if self.passed else ("FAIL" if self.severity == 'critical' else "WARN")

    @property
    def explanation(self) -> str:
        return self.details

RuleResult = SuitabilityCheck

class SuitabilityReport(BaseModel):
    checks: List[SuitabilityCheck]
    all_passed: bool = True
    critical_failures: List[SuitabilityCheck] = Field(default_factory=list)
    warnings: List[SuitabilityCheck] = Field(default_factory=list)

    @model_validator(mode='after')
    def compute_status(self) -> 'SuitabilityReport':
        self.critical_failures = [c for c in self.checks if not c.passed and c.severity == 'critical']
        self.warnings = [c for c in self.checks if not c.passed and c.severity == 'warning']
        self.all_passed = len(self.critical_failures) == 0
        return self

class TradeProposal(BaseModel):
    proposal_id: str
    client_id: str
    timestamp: datetime
    risk_score: int
    risk_category: str
    current_allocation: Dict[str, float]
    target_allocation: Dict[str, float]
    trades: List[TradeOrder]
    suitability_report: SuitabilityReport
    market_analysis: str
    allocation_rationale: str
    advisor_approved: Optional[bool] = None
    advisor_notes: Optional[str] = None
    
    total_buy_value: float = 0.0
    total_sell_value: float = 0.0
    net_tax_impact: float = 0.0

    @model_validator(mode='after')
    def compute_totals(self) -> 'TradeProposal':
        self.total_buy_value = sum(t.estimated_value for t in self.trades if t.action == 'BUY')
        self.total_sell_value = sum(t.estimated_value for t in self.trades if t.action == 'SELL')
        self.net_tax_impact = sum(t.tax_impact for t in self.trades)
        return self
