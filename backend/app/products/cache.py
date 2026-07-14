"""Small Redis cache for public product reads.

The cache is deliberately best-effort: checkout always reads and locks stock
from PostgreSQL, so Redis unavailability or a short-lived stale catalogue can
never oversell inventory.
"""
import json
import os
from typing import Any

from redis.asyncio import Redis, from_url


class ProductCache:
    def __init__(self) -> None:
        self.ttl_seconds = max(1, int(os.getenv("PRODUCT_CACHE_TTL_SECONDS", "300")))
        self._client: Redis | None = None

    def _redis(self) -> Redis:
        if self._client is None:
            url = os.getenv("PRODUCT_CACHE_REDIS_URL") or os.getenv("REDIS_URL")
            if not url:
                raise RuntimeError("Product cache is not configured")
            self._client = from_url(url, encoding="utf-8", decode_responses=True)
        return self._client

    async def get_json(self, key: str) -> Any | None:
        try:
            value = await self._redis().get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def set_json(self, key: str, value: Any) -> None:
        try:
            await self._redis().set(key, json.dumps(value, default=str, separators=(",", ":")), ex=self.ttl_seconds)
        except Exception:
            pass

    async def delete(self, key: str) -> None:
        try:
            await self._redis().delete(key)
        except Exception:
            pass

    async def list_version(self) -> int:
        try:
            value = await self._redis().get("products:list:version")
            return int(value) if value else 1
        except Exception:
            return 1

    async def invalidate_lists(self) -> None:
        try:
            client = self._redis()
            await client.incr("products:list:version")
            await client.expire("products:list:version", 86_400)
        except Exception:
            pass


product_cache = ProductCache()
