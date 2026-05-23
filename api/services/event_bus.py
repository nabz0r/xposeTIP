"""Event bus — publishes events to Redis pubsub for SSE streaming.

Default channel `xpose:events` is consumed by the in-app SSE stream
(`api/routers/events.py`). Additional channels (e.g. `bfp:events` for the
future public BFP trust-log widget) can be used by passing the `channel=`
kwarg to `publish_event`.

Channels are intentionally isolated: a future public BFP SSE consumer must
not be exposed to internal scan/discovery events, and the in-app stream
shouldn't be cluttered by BFP-protocol chatter.
"""
import json
import logging

import redis as r
from api.config import settings

logger = logging.getLogger(__name__)
CHANNEL = "xpose:events"          # in-app SSE stream (S101+)
BFP_CHANNEL = "bfp:events"        # S172 — future public BFP trust-log stream
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


def publish_event(event_type: str, data: dict, channel: str = CHANNEL):
    """Publish an event to Redis pubsub.

    Args:
        event_type: dotted event name, e.g. "scan.started", "bfp.merkle_root_committed"
        data: JSON-serializable payload (merged with {"type": event_type} as top-level)
        channel: Redis channel name. Defaults to `xpose:events` for backward compat
                 with all existing callers. Pass `BFP_CHANNEL` for BFP protocol events.
    """
    redis = _get_redis()
    if not redis:
        return
    try:
        redis.publish(channel, json.dumps({"type": event_type, **data}))
    except Exception:
        logger.debug("Failed to publish event: %s on %s", event_type, channel)
