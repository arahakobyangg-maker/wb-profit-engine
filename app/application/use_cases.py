from __future__ import annotations
from dataclasses import asdict
import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.domain.calculator import UnitEconomicsCalculator
from app.domain.entities import ProductDimensions, UnitEconomicsResult
from app.infrastructure.redis_cache import RedisCache
from app.infrastructure.repositories import CalculationRepository, WBTariffRepository
from app.infrastructure.wb_client import WBClient

settings = get_settings()


class CalculateUnitEconomicsUseCase:
    """
    Application Use Case orchestrating:
    1. Redis cache lookup (`wb:product:{nm_id}`)
    2. Live WB Card API fetch + 3600s Redis cache write on miss
    3. Category commission & warehouse coefficient lookup in PostgreSQL (`wb_tariffs`)
    4. Pure mathematical calculation across 90%, 75%, and 50% buyout scenarios
    5. Audit persistence to PostgreSQL (`calculations`)
    """

    def __init__(
        self,
        db_session: AsyncSession,
        cache: RedisCache,
        wb_api: WBClient,
    ) -> None:
        self.db_session = db_session
        self.cache = cache
        self.wb_api = wb_api
        self.tariff_repo = WBTariffRepository(db_session)
        self.calc_repo = CalculationRepository(db_session)

    async def execute(
        self,
        user_id: int,
        nm_id: int,
        cogs: float,
        custom_price: Optional[float] = None,
        length_cm: Optional[float] = None,
        width_cm: Optional[float] = None,
        height_cm: Optional[float] = None,
    ) -> UnitEconomicsResult:
        # Step 1: Check Redis cache
        cached_product = await self.cache.get_product(nm_id)
        if cached_product is not None:
            product = cached_product
            cache_hit = True
        else:
            product = await self.wb_api.fetch_product(nm_id)
            await self.cache.set_product(product, ttl_seconds=settings.REDIS_CACHE_TTL_SECONDS)
            cache_hit = False

        # Step 2: Fetch category tariff from PostgreSQL
        tariff = await self.tariff_repo.get_by_category(product.category)
        k_wb = tariff.commission_rate if tariff else settings.WB_DEFAULT_COMMISSION
        c_wh = (
            tariff.warehouse_coefficient
            if tariff
            else settings.WB_DEFAULT_WAREHOUSE_COEFF
        )

        # Step 3: Optional package dimension overrides
        override_dims: Optional[ProductDimensions] = None
        if (
            length_cm is not None
            and width_cm is not None
            and height_cm is not None
            and length_cm > 0
            and width_cm > 0
            and height_cm > 0
        ):
            override_dims = ProductDimensions(
                length_cm=length_cm,
                width_cm=width_cm,
                height_cm=height_cm,
            )

        # Step 4: Execute pure domain calculator
        served_by = os.getenv("HOSTNAME", "wb-api-local")
        result = UnitEconomicsCalculator.calculate(
            product=product,
            cogs=cogs,
            custom_price=custom_price,
            override_dimensions=override_dims,
            k_wb=k_wb,
            k_acq=settings.WB_ACQUIRING_RATE,
            c_wh=c_wh,
            l_return=settings.WB_RETURN_LOGISTICS_RUB,
            default_volume_liters=settings.WB_DEFAULT_VOLUME_LITERS,
            cache_hit=cache_hit,
            served_by_container=served_by,
        )

        # Step 5: Persist calculation audit record
        realistic = result.scenarios["realistic_75"]
        await self.calc_repo.save_calculation(
            user_id=user_id,
            nm_id=result.nm_id,
            product_name=result.product_name,
            category=result.category,
            selling_price_rub=result.selling_price_rub,
            cogs_rub=result.cogs_rub,
            volume_liters=result.volume_liters,
            realistic_net_profit_rub=realistic.seller_net_metrics.net_profit_rub,
            realistic_target_price_100_roi=realistic.target_price_for_100_roi,
            full_payload=asdict(result),
            served_by_container=served_by,
        )

        return result


class WBProductFetcherProtocol:
    async def fetch_product(self, nm_id: int):  # pragma: no cover
        raise NotImplementedError
