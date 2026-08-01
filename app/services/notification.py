import json
from collections.abc import AsyncIterator

import structlog
from redis.asyncio import Redis

from app.schemas.notification import NotificationEvent

logger = structlog.get_logger("notifications")

CHANNEL = "admin:notifications"


class NotificationService:

    def __init__(self, redis: Redis):
        self.redis = redis

    async def broadcast(self, event: NotificationEvent) -> None:
        try:
            await self.redis.publish(CHANNEL, event.model_dump_json())
        except Exception:
            logger.warning("notification_broadcast_failed", event_id=event.id)

    async def stream(self, last_id: int = 0) -> AsyncIterator[NotificationEvent]:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(CHANNEL)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                if data["id"] <= last_id:
                    continue
                yield NotificationEvent(**data)
        finally:
            await pubsub.unsubscribe(CHANNEL)
            await pubsub.aclose()