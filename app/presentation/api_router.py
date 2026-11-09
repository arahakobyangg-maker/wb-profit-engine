from dataclasses import asdict
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.use_cases import CalculateUnitEconomicsUseCase
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.infrastructure.database import get_db_session
from app.infrastructure.models import UserModel
from app.infrastructure.redis_cache import redis_cache
from app.infrastructure.repositories import CalculationRepository, UserRepository
from app.infrastructure.wb_client import wb_client
from app.presentation.schemas import (
    CalculateRequest,
    CalculateResponse,
    CalculationHistoryItemDTO,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db_session: AsyncSession = Depends(get_db_session),
) -> UserModel:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer JWT token",
        )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub", 0))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Bearer JWT token",
        ) from exc

    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Seller account not found or inactive",
        )
    return user


@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
async def register_seller(
    payload: RegisterRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    user_repo = UserRepository(db_session)
    existing = await user_repo.get_by_email(payload.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller with this email is already registered",
        )

    user = await user_repo.create_user(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        seller_name=payload.seller_name,
    )
    token = create_access_token(subject=user.id, email=user.email)
    return TokenResponse(
        access_token=token,
        seller_email=user.email,
        seller_name=user.seller_name,
        served_by_container=os.getenv("HOSTNAME", "wb-api-local"),
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["Authentication"],
)
async def login_seller(
    payload: LoginRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.id, email=user.email)
    return TokenResponse(
        access_token=token,
        seller_email=user.email,
        seller_name=user.seller_name,
        served_by_container=os.getenv("HOSTNAME", "wb-api-local"),
    )


@router.post(
    "/wb/calculate",
    response_model=CalculateResponse,
    tags=["Wildberries Unit-Economics"],
)
async def calculate_wb_unit_economics(
    payload: CalculateRequest,
    current_user: UserModel = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> CalculateResponse:
    use_case = CalculateUnitEconomicsUseCase(
        db_session=db_session,
        cache=redis_cache,
        wb_api=wb_client,
    )
    result = await use_case.execute(
        user_id=current_user.id,
        nm_id=payload.nm_id,
        cogs=payload.cogs,
        custom_price=payload.custom_price,
        length_cm=payload.length_cm,
        width_cm=payload.width_cm,
        height_cm=payload.height_cm,
    )
    return CalculateResponse(**asdict(result))


@router.get(
    "/wb/history",
    response_model=List[CalculationHistoryItemDTO],
    tags=["Wildberries Unit-Economics"],
)
async def list_calculation_history(
    current_user: UserModel = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[CalculationHistoryItemDTO]:
    calc_repo = CalculationRepository(db_session)
    records = await calc_repo.list_by_user(user_id=current_user.id, limit=25)
    return [
        CalculationHistoryItemDTO(
            id=r.id,
            nm_id=r.nm_id,
            product_name=r.product_name,
            category=r.category,
            selling_price_rub=r.selling_price_rub,
            cogs_rub=r.cogs_rub,
            volume_liters=r.volume_liters,
            realistic_net_profit_rub=r.realistic_net_profit_rub,
            realistic_target_price_100_roi=r.realistic_target_price_100_roi,
            served_by_container=r.served_by_container,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/health", tags=["System Health"])
async def health_check() -> dict[str, str | bool]:
    redis_ok = await redis_cache.ping()
    return {
        "status": "healthy",
        "service": "wb-profit-engine",
        "redis_connected": redis_ok,
        "served_by_container": os.getenv("HOSTNAME", "wb-api-local"),
    }
