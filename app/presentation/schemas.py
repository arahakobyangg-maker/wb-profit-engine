from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    seller_name: str = Field(default="WB Seller", min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    seller_email: str
    seller_name: str
    served_by_container: str


class CalculateRequest(BaseModel):
    nm_id: int = Field(..., gt=0, description="Wildberries product article number (nm_id)")
    cogs: float = Field(
        ...,
        ge=0,
        description="Full Cost of Goods Sold (purchase + packaging + delivery to WB warehouse, RUB)",
    )
    custom_price: Optional[float] = Field(
        default=None,
        gt=0,
        description="Optional custom selling price in RUB. If omitted, uses live WB price.",
    )
    length_cm: Optional[float] = Field(default=None, gt=0, description="Optional package length (cm)")
    width_cm: Optional[float] = Field(default=None, gt=0, description="Optional package width (cm)")
    height_cm: Optional[float] = Field(default=None, gt=0, description="Optional package height (cm)")


class WBDeductionsBreakdownDTO(BaseModel):
    commission_fee_rub: float
    commission_percent: float
    forward_logistics_rub: float
    return_logistics_burden_rub: float
    effective_logistics_rub: float
    storage_30d_rub: float
    total_wb_deductions_rub: float
    total_wb_deductions_percent: float


class SellerNetMetricsDTO(BaseModel):
    payout_to_seller_rub: float
    net_profit_rub: float
    profit_margin_percent: float
    roi_percent: float
    is_profitable: bool


class ScenarioCalculationDTO(BaseModel):
    scenario_name: str
    buyout_rate: float
    buyout_percent: int
    wb_deductions_breakdown: WBDeductionsBreakdownDTO
    seller_net_metrics: SellerNetMetricsDTO
    target_price_for_100_roi: float


class CalculateResponse(BaseModel):
    nm_id: int
    product_name: str
    category: str
    selling_price_rub: float
    cogs_rub: float
    volume_liters: float
    commission_rate_wb: float
    acquiring_rate: float
    total_commission_rate: float
    warehouse_coefficient: float
    cache_hit: bool
    data_source: str
    scenarios: Dict[str, ScenarioCalculationDTO]
    served_by_container: str


class CalculationHistoryItemDTO(BaseModel):
    id: int
    nm_id: int
    product_name: str
    category: str
    selling_price_rub: float
    cogs_rub: float
    volume_liters: float
    realistic_net_profit_rub: float
    realistic_target_price_100_roi: float
    served_by_container: str
    created_at: datetime
