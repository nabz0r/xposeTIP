"""Redis caching service for frequently accessed data."""
import json
import logging
from typing import Any, Callable

import redis as r

from api.config import settings

logger = logging.getLogger(__name__)

# Cache TTL constants (seconds)
TTL_SHORT = 60          # 1 minute
TTL_MEDIUM = 300        # 5 minutes
TTL_LONG = 600          # 10 minutes
TTL_HOUR = 3600         # 1 hour


class CacheService:
    """Redis-backed caching for frequently accessed data."""

    def __init__(self):
        try:
            self.redis = r.from_url(settings.REDIS_URL)
            self.redis.ping()
        except Exception:
            self.redis = None
            logger.warning("Redis not available for caching")

    def get(self, key: str) -> Any | None:
        """Get cached value by key."""
        if not self.redis:
            return None
        try:
            cached = self.redis.get(f"cache:{key}")
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return None

    def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM):
        """Set cache value with TTL."""
        if not self.redis:
            return
        try:
            self.redis.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
        except Exception:
            pass

    def delete(self, key: str):
        """Delete cached value."""
        if not self.redis:
            return
        try:
            self.redis.delete(f"cache:{key}")
        except Exception:
            pass

    def invalidate_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        if not self.redis:
            return
        try:
            keys = self.redis.keys(f"cache:{pattern}")
            if keys:
                self.redis.delete(*keys)
        except Exception:
            pass

    def get_or_set(self, key: str, compute_fn: Callable, ttl: int = TTL_MEDIUM) -> Any:
        """Get cached value or compute and cache it."""
        cached = self.get(key)
        if cached is not None:
            return cached
        result = compute_fn()
        self.set(key, result, ttl)
        return result


# Singleton
cache = CacheService()
