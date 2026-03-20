"""Rate limiter — per-service rate limiting using Redis.

Prevents hitting external API rate limits when running multiple scans.
"""
import asyncio
import logging

import redis as r

from api.config import settings

logger = logging.getLogger(__name__)

LIMITS = {
    # Free APIs
    "ip-api.com": {"requests": 45, "window": 60},
    "emailrep.io": {"requests": 1, "window": 2},
    "crt.sh": {"requests": 10, "window": 60},
    "ipapi.co": {"requests": 30, "window": 60},
    # GitHub
    "api.github.com": {"requests": 60, "window": 3600},
    "api.github.com:auth": {"requests": 5000, "window": 3600},
    # Paid APIs
    "haveibeenpwned.com": {"requests": 10, "window": 60},
    "api.virustotal.com": {"requests": 4, "window": 60},
    "api.shodan.io": {"requests": 10, "window": 60},
    "2.intelx.io": {"requests": 10, "window": 60},
    "api.hunter.io": {"requests": 15, "window": 60},
    "api.dehashed.com": {"requests": 5, "window": 60},
    "api.fullcontact.com": {"requests": 60, "window": 60},
    # Scanner rate limits
    "holehe": {"requests": 30, "window": 60},
    "sherlock": {"requests": 5, "window": 60},
}


class RateLimiter:
    """Redis-backed rate limiter for external API calls."""

    def __init__(self):
        try:
            self.redis = r.from_url(settings.REDIS_URL)
            self.redis.ping()
        except Exception:
            self.redis = None
            logger.warning("Redis not available for rate limiting")

    def acquire(self, service: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        if not self.redis:
            return True

        limit = LIMITS.get(service, {"requests": 30, "window": 60})
        key = f"ratelimit:{service}"

        try:
            current = self.redis.incr(key)
            if current == 1:
                self.redis.expire(key, limit["window"])
            return current <= limit["requests"]
        except Exception:
            return True

    def wait_and_acquire(self, service: str, max_wait: float = 30.0) -> bool:
        """Wait until rate limit allows, then proceed. Returns False if timeout."""
        import time
        deadline = time.time() + max_wait
        while time.time() < deadline:
            if self.acquire(service):
                return True
            time.sleep(1)
        return False

    def get_remaining(self, service: str) -> int:
        """Get remaining requests for a service."""
        if not self.redis:
            return 999

        limit = LIMITS.get(service, {"requests": 30, "window": 60})
        key = f"ratelimit:{service}"

        try:
            current = self.redis.get(key)
            if current is None:
                return limit["requests"]
            return max(0, limit["requests"] - int(current))
        except Exception:
            return limit["requests"]


# Singleton
rate_limiter = RateLimiter()
