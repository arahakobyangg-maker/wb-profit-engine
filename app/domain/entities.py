from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ProductDimensions:
    length_cm: float
    width_cm: float
    height_cm: float

    @property
    def volume_liters(self) -> float:
        if self.length_cm <= 0 or self.width_cm <= 0 or self.height_cm <= 0:
            return 2.0
        return round((self.length_cm * self.width_cm * self.height_cm) / 1000.0, 4)


@dataclass(frozen=True)
class WBProduct:
    nm_id: int
    name: str
    category: str
    current_price: float
    weight_kg: float
    dimensions: Optional[ProductDimensions]
    source: str = "wb_live_api"


@dataclass(frozen=True)
class WBDeductionsBreakdown:
    commission_fee_rub: float
    commission_percent: float
    forward_logistics_rub: float
    return_logistics_burden_rub: float
    effective_logistics_rub: float
    storage_30d_rub: float
    total_wb_deductions_rub: float
    total_wb_deductions_percent: float


@dataclass(frozen=True)
class SellerNetMetrics:
    payout_to_seller_rub: float
    net_profit_rub: float
    profit_margin_percent: float
    roi_percent: float
    is_profitable: bool


@dataclass(frozen=True)
class ScenarioCalculation:
    scenario_name: str
    buyout_rate: float
    buyout_percent: int
    wb_deductions_breakdown: WBDeductionsBreakdown
    seller_net_metrics: SellerNetMetrics
    target_price_for_100_roi: float


@dataclass(frozen=True)
class UnitEconomicsResult:
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
    scenarios: Dict[str, ScenarioCalculation]
    served_by_container: str
