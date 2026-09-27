from typing import Literal, List, Optional
from pydantic import BaseModel, Field

class IPS(BaseModel):
    investment_objective: Literal['growth', 'growth_and_income', 'income', 'capital_preservation']
    risk_tolerance: Literal['conservative', 'moderate_conservative', 'moderate', 'moderate_aggressive', 'aggressive']
    time_horizon_years: int
    liquidity_needs: Literal['high', 'moderate', 'low']
    tax_bracket: float = Field(ge=0, le=0.37)
    restrictions: List[str]
    max_single_position_pct: float
    rebalance_threshold_pct: float

class KYC(BaseModel):
    age: int
    annual_income: float
    net_worth: float
    investment_experience: Literal['none', 'limited', 'experienced', 'sophisticated']
    employment_status: str
    dependents: int

class ClientProfile(BaseModel):
    client_id: str
    name: str
    ips: IPS
    kyc: KYC
    risk_score: Optional[int] = Field(None, ge=1, le=10)
    risk_category: Optional[str] = None
