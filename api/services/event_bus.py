"""Event bus — publishes events to Redis pubsub for SSE streaming."""
import json
import logging

import redis as r
from api.config import settings

logger = logging.getLogger(__name__)
CHANNEL = "xpose:events"
_redis = None


def _get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = r.from_url(settings.REDIS_URL)
            _redis.ping()
        except Exception:
            logger.warning("Redis not available for event bus")
    return _redis


def publish_event(event_type: str, data: dict):
    redis = _get_redis()
    if not redis:
        return
    try:
        redis.publish(CHANNEL, json.dumps({"type": event_type, **data}))
    except Exception:
        logger.debug("Failed to publish event: %s", event_type)
