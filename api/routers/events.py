"""SSE endpoint for real-time event streaming."""
import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from api.auth.dependencies import get_current_user, get_current_workspace
from api.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
CHANNEL = "xpose:events"


@router.get("/stream")
async def event_stream(
    request: Request,
    workspace_id=Depends(get_current_workspace),
    user=Depends(get_current_user),
):
    async def generate():
        redis = aioredis.from_url(settings.REDIS_URL)
        pubsub = redis.pubsub()
        await pubsub.subscribe(CHANNEL)
        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0,
                )
                if message and message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        if event.get("workspace_id") == str(workspace_id):
                            yield f"data: {json.dumps(event)}\n\n"
                    except (json.JSONDecodeError, TypeError):
                        pass
                else:
                    yield ": keepalive\n\n"
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(CHANNEL)
            await redis.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
