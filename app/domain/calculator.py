from typing import Dict, Optional
from app.domain.entities import (
    ProductDimensions,
    ScenarioCalculation,
    SellerNetMetrics,
    UnitEconomicsResult,
    WBDeductionsBreakdown,
    WBProduct,
)


class UnitEconomicsCalculator:
    """
    Pure mathematical engine implementing the Wildberries Unit-Economics specification.
    100% deterministic and zero-dependency for fast isolated unit testing.
    """

    BUYOUT_SCENARIOS: Dict[str, float] = {
        "optimistic_90": 0.90,
        "realistic_75": 0.75,
        "pessimistic_50": 0.50,
    }

    @staticmethod
    def compute_volume_liters(
        dimensions: Optional[ProductDimensions],
        default_volume_liters: float = 2.0,
    ) -> float:
        if dimensions is None:
            return round(default_volume_liters, 4)
        if (
            dimensions.length_cm <= 0
            or dimensions.width_cm <= 0
            or dimensions.height_cm <= 0
        ):
            return round(default_volume_liters, 4)
        return round(
            (dimensions.length_cm * dimensions.width_cm * dimensions.height_cm) / 1000.0,
            4,
        )

    @staticmethod
    def compute_forward_logistics(
        volume_liters: float,
        warehouse_coeff: float = 1.7,
    ) -> float:
        if volume_liters <= 1.0:
            l_base = 46.0
        else:
            l_base = 46.0 + (volume_liters - 1.0) * 14.0
        return round(l_base * warehouse_coeff, 2)

    @staticmethod
    def compute_effective_logistics(
        l_forward: float,
        buyout_rate: float,
        l_return: float = 50.0,
    ) -> float:
        if buyout_rate <= 0 or buyout_rate > 1.0:
            raise ValueError("buyout_rate must be in (0, 1.0]")
        l_effective = (l_forward + (1.0 - buyout_rate) * l_return) / buyout_rate
        return round(l_effective, 2)

    @staticmethod
    def compute_storage_30d(volume_liters: float) -> float:
        return round(volume_liters * 0.14 * 30.0, 2)

    @staticmethod
    def compute_target_price_100_roi(
        cogs: float,
        l_effective: float,
        s_storage: float,
        k_total: float,
    ) -> float:
        if k_total >= 1.0:
            raise ValueError("Total commission rate k_total must be < 1.0")
        target = (2.0 * cogs + l_effective + s_storage) / (1.0 - k_total)
        return round(target, 2)

    @classmethod
    def calculate(
        cls,
        product: WBProduct,
        cogs: float,
        custom_price: Optional[float] = None,
        override_dimensions: Optional[ProductDimensions] = None,
        k_wb: float = 0.19,
        k_acq: float = 0.015,
        c_wh: float = 1.7,
        l_return: float = 50.0,
        default_volume_liters: float = 2.0,
        cache_hit: bool = False,
        served_by_container: str = "wb-api-local",
    ) -> UnitEconomicsResult:
        selling_price = (
            float(custom_price)
            if custom_price is not None and custom_price > 0
            else float(product.current_price)
        )
        if selling_price <= 0:
            raise ValueError("Selling price must be greater than 0 RUB")
        if cogs < 0:
            raise ValueError("COGS cannot be negative")

        active_dimensions = override_dimensions or product.dimensions
        volume_liters = cls.compute_volume_liters(
            active_dimensions, default_volume_liters=default_volume_liters
        )

        # 2. WB Commission & Acquiring
        k_total = round(k_wb + k_acq, 4)
        commission_fee = round(selling_price * k_total, 2)

        # 3. Forward Logistics
        l_forward = cls.compute_forward_logistics(
            volume_liters=volume_liters, warehouse_coeff=c_wh
        )

        # 5. Storage (30 days turnover)
        s_storage = cls.compute_storage_30d(volume_liters=volume_liters)

        # 4. Evaluate across 3 Buyout Rate scenarios (90%, 75%, 50%)
        scenarios: Dict[str, ScenarioCalculation] = {}
        for scenario_key, buyout_rate in cls.BUYOUT_SCENARIOS.items():
            l_effective = cls.compute_effective_logistics(
                l_forward=l_forward,
                buyout_rate=buyout_rate,
                l_return=l_return,
            )
            return_burden = round(l_effective - l_forward, 2)
            total_deductions = round(commission_fee + l_effective + s_storage, 2)
            deductions_pct = round((total_deductions / selling_price) * 100.0, 2)

            payout_to_seller = round(selling_price - total_deductions, 2)
            net_profit = round(selling_price - total_deductions - cogs, 2)
            profit_margin_pct = round((net_profit / selling_price) * 100.0, 2)
            roi_pct = round((net_profit / cogs) * 100.0, 2) if cogs > 0 else 0.0

            target_price_100_roi = cls.compute_target_price_100_roi(
                cogs=cogs,
                l_effective=l_effective,
                s_storage=s_storage,
                k_total=k_total,
            )

            scenarios[scenario_key] = ScenarioCalculation(
                scenario_name=scenario_key,
                buyout_rate=buyout_rate,
                buyout_percent=int(buyout_rate * 100),
                wb_deductions_breakdown=WBDeductionsBreakdown(
                    commission_fee_rub=commission_fee,
                    commission_percent=round(k_total * 100.0, 2),
                    forward_logistics_rub=l_forward,
                    return_logistics_burden_rub=return_burden,
                    effective_logistics_rub=l_effective,
                    storage_30d_rub=s_storage,
                    total_wb_deductions_rub=total_deductions,
                    total_wb_deductions_percent=deductions_pct,
                ),
                seller_net_metrics=SellerNetMetrics(
                    payout_to_seller_rub=payout_to_seller,
                    net_profit_rub=net_profit,
                    profit_margin_percent=profit_margin_pct,
                    roi_percent=roi_pct,
                    is_profitable=net_profit > 0,
                ),
                target_price_for_100_roi=target_price_100_roi,
            )

        return UnitEconomicsResult(
            nm_id=product.nm_id,
            product_name=product.name,
            category=product.category,
            selling_price_rub=round(selling_price, 2),
            cogs_rub=round(cogs, 2),
            volume_liters=volume_liters,
            commission_rate_wb=k_wb,
            acquiring_rate=k_acq,
            total_commission_rate=k_total,
            warehouse_coefficient=c_wh,
            cache_hit=cache_hit,
            data_source=product.source,
            scenarios=scenarios,
            served_by_container=served_by_container,
        )
