"""Redis cache utilities."""
from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as redis

from .config import get_settings

settings = get_settings()

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    client = await get_redis()
    value = await client.get(key)
    if value:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Set value in cache with optional TTL."""
    client = await get_redis()
    if ttl is None:
        ttl = settings.cache_ttl
    await client.setex(key, ttl, json.dumps(value))


async def cache_delete(key: str) -> None:
    """Delete value from cache."""
    client = await get_redis()
    await client.delete(key)


async def cache_exists(key: str) -> bool:
    """Check if key exists in cache."""
    client = await get_redis()
    return await client.exists(key) > 0
