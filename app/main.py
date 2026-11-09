from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.infrastructure.database import AsyncSessionLocal, Base, engine
from app.infrastructure.redis_cache import redis_cache
from app.infrastructure.repositories import WBTariffRepository
from app.presentation.api_router import router as api_v1_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize PostgreSQL schema and seed default WB category tariffs
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        tariff_repo = WBTariffRepository(session)
        await tariff_repo.seed_defaults_if_empty()
    yield
    await redis_cache.close()
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Production-grade Clean Architecture backend for Wildberries (WB) Sellers "
        "to calculate unit-economics, marketplace deductions, net profit, and "
        "target selling price for 100% ROI across 90%, 75%, and 50% buyout scenarios."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "project": settings.PROJECT_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "served_by_container": os.getenv("HOSTNAME", "wb-api-local"),
    }
