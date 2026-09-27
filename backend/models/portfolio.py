from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, model_validator, Field

class Position(BaseModel):
    symbol: str
    shares: float
    cost_basis_per_share: float
    current_price: float
    holding_period_days: int
    asset_class: str
    
    market_value: float = 0.0
    weight: float = 0.0
    unrealized_gain_loss: float = 0.0

    @model_validator(mode='after')
    def compute_fields(self) -> 'Position':
        self.market_value = self.shares * self.current_price
        self.unrealized_gain_loss = self.market_value - (self.shares * self.cost_basis_per_share)
        return self

class Portfolio(BaseModel):
    positions: List[Position]
    total_value: float = 0.0
    allocation: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode='after')
    def compute_fields(self) -> 'Portfolio':
        self.total_value = sum(p.market_value for p in self.positions)
        alloc = {}
        for p in self.positions:
            p.weight = p.market_value / self.total_value if self.total_value > 0 else 0.0
            alloc[p.asset_class] = alloc.get(p.asset_class, 0.0) + p.weight
        self.allocation = alloc
        return self

class TradeOrder(BaseModel):
    symbol: str
    action: Literal['BUY', 'SELL', 'HOLD']
    shares: float
    estimated_price: float
    estimated_value: float
    tax_impact: float = 0.0
    rationale: str = ""
    asset_class: str = "other"
    target_weight: Optional[float] = None
