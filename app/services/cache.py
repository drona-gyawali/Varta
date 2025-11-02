import json
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from redis.asyncio import Redis

from app.core.conf import REDISCONF
from app.core.logger import setup_logger

logger = setup_logger("services.cache")


class Cache:
    def __init__(self):
        self.cache = Redis(
            host=REDISCONF.get("redisHost"),
            port=int(REDISCONF.get("redisPort")),
            password=REDISCONF.get("redisPassword"),
            decode_responses=True,
        )

    async def get_cache(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis by key."""
        try:
            data = await self.cache.get(key)
            if data is None:
                logger.info(f"Cache miss for key: {key}")
                return None
            logger.info(f"Cache hit for key: {key}")
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting cache for {key}: {e}")
            return None

    async def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in Redis with optional TTL (default 1 hour)."""
        try:
            safe_value = jsonable_encoder(value)
            await self.cache.set(key, json.dumps(safe_value), ex=ttl)
            logger.info(f"Cache set for key: {key} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache for {key}: {e}")
            return False

    async def del_cache(self, pattern: str) -> bool:
        """Delete all keys matching a pattern."""
        try:
            keys = await self.cache.keys(pattern)
            if not keys:
                logger.warning(f"No cache keys matched pattern: {pattern}")
                return False

            result = await self.cache.delete(*keys)  # Unpack the list of keys
            logger.info(f"Deleted {result} cache entries matching pattern: {pattern}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting cache for pattern {pattern}: {e}")
            return False


# Singleton instance
cache = Cache()
