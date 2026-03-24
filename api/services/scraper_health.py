"""Scraper health tracking via Redis counters.

Fire-and-forget — never blocks the scan pipeline.
All keys TTL 24h.
"""
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

REDIS_PREFIX = "scraper_health"
TTL_SECONDS = 86400  # 24 hours


class ScraperHealth:
    def __init__(self, redis_client):
        self.redis = redis_client

    def record(self, scraper_name: str, status_code: int, response_ms: int, cached: bool = False):
        """Record a single scraper call result. Fire-and-forget."""
        try:
            pipe = self.redis.pipeline()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            prefix = f"{REDIS_PREFIX}:{scraper_name}:{today}"

            # Increment status code counter
            pipe.hincrby(f"{prefix}:codes", str(status_code), 1)
            pipe.expire(f"{prefix}:codes", TTL_SECONDS)

            # Increment total counter
            # 404/410 = "not found" (scraper worked correctly, profile doesn't exist)
            # Only 403, 429, 5xx are real errors
            pipe.hincrby(f"{prefix}:total", "calls", 1)
            if 200 <= status_code < 300 or status_code in (404, 410):
                pipe.hincrby(f"{prefix}:total", "success", 1)
            else:
                pipe.hincrby(f"{prefix}:total", "errors", 1)
            pipe.expire(f"{prefix}:total", TTL_SECONDS)

            # Track response time (running sum + count for average)
            if not cached:
                pipe.hincrby(f"{prefix}:timing", "sum_ms", response_ms)
                pipe.hincrby(f"{prefix}:timing", "count", 1)
                pipe.expire(f"{prefix}:timing", TTL_SECONDS)

            # Cache hit counter
            if cached:
                pipe.hincrby(f"{prefix}:total", "cache_hits", 1)

            # Last call timestamp
            pipe.set(f"{REDIS_PREFIX}:{scraper_name}:last_call",
                     datetime.utcnow().isoformat(), ex=TTL_SECONDS)

            # Last success timestamp (404/410 = working correctly)
            if 200 <= status_code < 300 or status_code in (404, 410):
                pipe.set(f"{REDIS_PREFIX}:{scraper_name}:last_success",
                         datetime.utcnow().isoformat(), ex=TTL_SECONDS)

            pipe.execute()
        except Exception:
            pass  # Fire-and-forget — never crash the pipeline

    def get_health(self, scraper_name: str) -> dict:
        """Get health stats for a single scraper."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        prefix = f"{REDIS_PREFIX}:{scraper_name}:{today}"

        try:
            codes = self.redis.hgetall(f"{prefix}:codes") or {}
            total = self.redis.hgetall(f"{prefix}:total") or {}
            timing = self.redis.hgetall(f"{prefix}:timing") or {}
            last_call = self.redis.get(f"{REDIS_PREFIX}:{scraper_name}:last_call")
            last_success = self.redis.get(f"{REDIS_PREFIX}:{scraper_name}:last_success")

            calls = int(total.get(b'calls', total.get('calls', 0)))
            success = int(total.get(b'success', total.get('success', 0)))
            errors = int(total.get(b'errors', total.get('errors', 0)))
            cache_hits = int(total.get(b'cache_hits', total.get('cache_hits', 0)))

            timing_sum = int(timing.get(b'sum_ms', timing.get('sum_ms', 0)))
            timing_count = int(timing.get(b'count', timing.get('count', 0)))
            avg_ms = timing_sum // timing_count if timing_count > 0 else 0

            health_pct = (success / calls * 100) if calls > 0 else None

            return {
                "scraper": scraper_name,
                "calls_24h": calls,
                "success_24h": success,
                "errors_24h": errors,
                "cache_hits_24h": cache_hits,
                "health_pct": round(health_pct, 1) if health_pct is not None else None,
                "avg_response_ms": avg_ms,
                "status_codes": {
                    (k.decode() if isinstance(k, bytes) else k): int(v)
                    for k, v in codes.items()
                },
                "last_call": (last_call.decode() if isinstance(last_call, bytes) else last_call) if last_call else None,
                "last_success": (last_success.decode() if isinstance(last_success, bytes) else last_success) if last_success else None,
            }
        except Exception:
            return {"scraper": scraper_name, "error": "Redis unavailable"}

    def get_all_health(self) -> list:
        """Get health for all scrapers that have been called today."""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            pattern = f"{REDIS_PREFIX}:*:{today}:total"
            keys = self.redis.keys(pattern)

            scraper_names = set()
            for key in keys:
                decoded = key.decode() if isinstance(key, bytes) else key
                parts = decoded.split(':')
                if len(parts) >= 4:
                    # scraper_health:SCRAPER_NAME:DATE:total
                    scraper_names.add(parts[1])

            results = []
            for name in sorted(scraper_names):
                results.append(self.get_health(name))

            # Sort by health_pct ascending (worst first)
            results.sort(key=lambda x: x.get('health_pct') if x.get('health_pct') is not None else 999)

            return results
        except Exception:
            return []


def get_scraper_health_instance():
    """Get a ScraperHealth instance using the app Redis connection."""
    try:
        import redis as r
        from api.config import settings
        rc = r.from_url(settings.REDIS_URL, decode_responses=False)
        return ScraperHealth(rc)
    except Exception:
        return None
