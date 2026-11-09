from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "WB-Profit-Engine"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "production"

    # PostgreSQL (AsyncPG)
    POSTGRES_USER: str = "wb_admin"
    POSTGRES_PASSWORD: str = "CHANGE_ME_STRONG_POSTGRES_PASSWORD"
    POSTGRES_HOST: str = "postgres-db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "wb_profit_db"

    # Redis
    REDIS_HOST: str = "redis-cache"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_CACHE_TTL_SECONDS: int = 3600

    # JWT Security
    JWT_SECRET_KEY: str = "CHANGE_ME_64_BYTE_HEX_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Wildberries Public Card API
    WB_CARD_API_URL: str = (
        "https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&nm={nm_id}"
    )
    WB_DEFAULT_COMMISSION: float = 0.19
    WB_ACQUIRING_RATE: float = 0.015
    WB_DEFAULT_WAREHOUSE_COEFF: float = 1.7
    WB_RETURN_LOGISTICS_RUB: float = 50.0
    WB_DEFAULT_VOLUME_LITERS: float = 2.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
