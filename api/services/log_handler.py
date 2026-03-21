"""Structured logging handler that pushes log entries to a Redis ring buffer.

Each log entry is a JSON object with timestamp, level, logger, message,
container source, and optional extras (task_id, module, target_id).

The ring buffer is capped at LOG_BUFFER_SIZE entries using LPUSH + LTRIM.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone


LOG_REDIS_KEY = "xpose:logs"
LOG_BUFFER_SIZE = 2000


class RedisLogHandler(logging.Handler):
    """Logging handler that pushes structured JSON entries to Redis."""

    def __init__(self, redis_url: str, container: str = "api", buffer_size: int = LOG_BUFFER_SIZE):
        super().__init__()
        self.redis_url = redis_url
        self.container = container
        self.buffer_size = buffer_size
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self.redis_url, socket_connect_timeout=2)
                self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def emit(self, record: logging.LogRecord):
        try:
            rc = self._get_redis()
            if rc is None:
                return

            entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "container": self.container,
            }

            # Add extras if present
            for key in ("task_id", "module", "target_id", "scan_id"):
                val = getattr(record, key, None)
                if val is not None:
                    entry[key] = str(val)

            rc.lpush(LOG_REDIS_KEY, json.dumps(entry))
            rc.ltrim(LOG_REDIS_KEY, 0, self.buffer_size - 1)
        except Exception:
            # Never let logging break the app
            pass


def setup_logging(redis_url: str, container: str = "api", level: int = logging.INFO):
    """Install the RedisLogHandler on the root logger."""
    handler = RedisLogHandler(redis_url=redis_url, container=container)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.addHandler(handler)
    if root.level > level:
        root.setLevel(level)

    return handler


def get_logs(redis_url: str, limit: int = 200, level: str | None = None, container: str | None = None) -> list[dict]:
    """Read log entries from the Redis ring buffer."""
    import redis
    rc = redis.from_url(redis_url, socket_connect_timeout=2)
    raw = rc.lrange(LOG_REDIS_KEY, 0, limit * 2 if (level or container) else limit - 1)
    rc.close()

    entries = []
    for item in raw:
        try:
            entry = json.loads(item)
        except (json.JSONDecodeError, TypeError):
            continue

        if level and entry.get("level", "").upper() != level.upper():
            continue
        if container and entry.get("container", "") != container:
            continue

        entries.append(entry)
        if len(entries) >= limit:
            break

    return entries


def clear_logs(redis_url: str) -> int:
    """Delete all log entries from the ring buffer. Returns count deleted."""
    import redis
    rc = redis.from_url(redis_url, socket_connect_timeout=2)
    count = rc.llen(LOG_REDIS_KEY)
    rc.delete(LOG_REDIS_KEY)
    rc.close()
    return count
