from typing import Any, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import CalculationModel, UserModel, WBTariffModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        seller_name: str = "WB Seller",
    ) -> UserModel:
        user = UserModel(
            email=email.lower().strip(),
            seller_name=seller_name.strip(),
            hashed_password=hashed_password,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user


class WBTariffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_category(self, category_name: str) -> Optional[WBTariffModel]:
        stmt = select(WBTariffModel).where(
            WBTariffModel.category_name.ilike(category_name.strip())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[WBTariffModel]:
        stmt = select(WBTariffModel).order_by(WBTariffModel.category_name.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def seed_defaults_if_empty(self) -> None:
        existing = await self.list_all()
        if existing:
            return
        defaults = [
            WBTariffModel(
                category_name="Худи и свитшоты",
                commission_rate=0.245,
                warehouse_coefficient=1.7,
            ),
            WBTariffModel(
                category_name="Футболки",
                commission_rate=0.23,
                warehouse_coefficient=1.7,
            ),
            WBTariffModel(
                category_name="Кроссовки и кеды",
                commission_rate=0.225,
                warehouse_coefficient=1.7,
            ),
            WBTariffModel(
                category_name="Наушники и гарнитуры",
                commission_rate=0.15,
                warehouse_coefficient=1.7,
            ),
            WBTariffModel(
                category_name="Увлажнители воздуха",
                commission_rate=0.17,
                warehouse_coefficient=1.7,
            ),
            WBTariffModel(
                category_name="Кремы для лица",
                commission_rate=0.21,
                warehouse_coefficient=1.7,
            ),
            WBTariffModel(
                category_name="Термокружки и термосы",
                commission_rate=0.19,
                warehouse_coefficient=1.7,
            ),
            WBTariffModel(
                category_name="Default",
                commission_rate=0.19,
                warehouse_coefficient=1.7,
            ),
        ]
        self.session.add_all(defaults)
        await self.session.commit()


class CalculationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_calculation(
        self,
        user_id: int,
        nm_id: int,
        product_name: str,
        category: str,
        selling_price_rub: float,
        cogs_rub: float,
        volume_liters: float,
        realistic_net_profit_rub: float,
        realistic_target_price_100_roi: float,
        full_payload: dict[str, Any],
        served_by_container: str,
    ) -> CalculationModel:
        record = CalculationModel(
            user_id=user_id,
            nm_id=nm_id,
            product_name=product_name,
            category=category,
            selling_price_rub=selling_price_rub,
            cogs_rub=cogs_rub,
            volume_liters=volume_liters,
            realistic_net_profit_rub=realistic_net_profit_rub,
            realistic_target_price_100_roi=realistic_target_price_100_roi,
            full_payload=full_payload,
            served_by_container=served_by_container,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def list_by_user(self, user_id: int, limit: int = 25) -> Sequence[CalculationModel]:
        stmt = (
            select(CalculationModel)
            .where(CalculationModel.user_id == user_id)
            .order_by(CalculationModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
