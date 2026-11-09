import json
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import get_settings
from app.domain.entities import ProductDimensions, WBProduct

settings = get_settings()


class RedisCache:
    """
    Async Redis cache wrapper storing WB product metadata under `wb:product:{nm_id}`
    with a strict 3600-second TTL.
    """

    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.5,
            )
        return self._client

    @staticmethod
    def build_key(nm_id: int) -> str:
        return f"wb:product:{nm_id}"

    async def get_product(self, nm_id: int) -> Optional[WBProduct]:
        try:
            client = await self.get_client()
            raw = await client.get(self.build_key(nm_id))
            if not raw:
                return None
            data: dict[str, Any] = json.loads(raw)
            dims_raw = data.get("dimensions")
            dimensions = (
                ProductDimensions(
                    length_cm=float(dims_raw["length_cm"]),
                    width_cm=float(dims_raw["width_cm"]),
                    height_cm=float(dims_raw["height_cm"]),
                )
                if dims_raw
                else None
            )
            return WBProduct(
                nm_id=int(data["nm_id"]),
                name=str(data["name"]),
                category=str(data["category"]),
                current_price=float(data["current_price"]),
                weight_kg=float(data.get("weight_kg", 0.5)),
                dimensions=dimensions,
                source=str(data.get("source", "redis_cache")),
            )
        except Exception:
            return None

    async def set_product(
        self,
        product: WBProduct,
        ttl_seconds: int = settings.REDIS_CACHE_TTL_SECONDS,
    ) -> None:
        try:
            client = await self.get_client()
            payload = {
                "nm_id": product.nm_id,
                "name": product.name,
                "category": product.category,
                "current_price": product.current_price,
                "weight_kg": product.weight_kg,
                "dimensions": (
                    {
                        "length_cm": product.dimensions.length_cm,
                        "width_cm": product.dimensions.width_cm,
                        "height_cm": product.dimensions.height_cm,
                    }
                    if product.dimensions
                    else None
                ),
                "source": product.source,
            }
            await client.setex(
                self.build_key(product.nm_id),
                ttl_seconds,
                json.dumps(payload, ensure_ascii=False),
            )
        except Exception:
            pass

    async def ping(self) -> bool:
        try:
            client = await self.get_client()
            return bool(await client.ping())
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


redis_cache = RedisCache()
