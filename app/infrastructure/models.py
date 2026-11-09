from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    seller_name: Mapped[str] = mapped_column(String(255), nullable=False, default="WB Seller")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    calculations: Mapped[list["CalculationModel"]] = relationship(
        "CalculationModel", back_populates="user", cascade="all, delete-orphan"
    )


class WBTariffModel(Base):
    __tablename__ = "wb_tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    commission_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.19)
    warehouse_coefficient: Mapped[float] = mapped_column(Float, nullable=False, default=1.7)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CalculationModel(Base):
    __tablename__ = "calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nm_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    selling_price_rub: Mapped[float] = mapped_column(Float, nullable=False)
    cogs_rub: Mapped[float] = mapped_column(Float, nullable=False)
    volume_liters: Mapped[float] = mapped_column(Float, nullable=False)
    realistic_net_profit_rub: Mapped[float] = mapped_column(Float, nullable=False)
    realistic_target_price_100_roi: Mapped[float] = mapped_column(Float, nullable=False)
    full_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    served_by_container: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="calculations")
