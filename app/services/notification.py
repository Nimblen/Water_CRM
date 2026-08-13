import asyncio
import json
from collections.abc import AsyncIterator

import structlog
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationEvent, NotificationType

logger = structlog.get_logger("notifications")

CHANNEL = "admin:notifications"
RECONNECT_DELAY = 2


class NotificationService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def broadcast(
        self,
        session: AsyncSession,
        type_: NotificationType,
        payload: dict,
        driver_id=None,
        route_id=None,
    ) -> NotificationEvent:
        repo = NotificationRepository(session)
        row = await repo.create(type_, payload, driver_id, route_id)
        event = NotificationEvent.model_validate(row)

        try:
            await self.redis.publish(CHANNEL, event.model_dump_json())
        except Exception:
            logger.warning("notification_publish_failed", event_id=event.id)

        return event

    async def event_source(
        self, session: AsyncSession, last_id: int
    ) -> AsyncIterator[NotificationEvent]:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(CHANNEL)

        max_sent_id = last_id
        try:
            repo = NotificationRepository(session)
            backlog = await repo.get_since(last_id, limit=200)
            for row in backlog:
                event = NotificationEvent.model_validate(row)
                max_sent_id = event.id
                yield event
            async for event in self._listen(pubsub):
                if event.id <= max_sent_id:
                    continue
                max_sent_id = event.id
                yield event
        finally:
            await pubsub.unsubscribe(CHANNEL)
            await pubsub.aclose()

    async def _listen(self, pubsub) -> AsyncIterator[NotificationEvent]:
        while True:
            try:
                async for message in pubsub.listen():
                    if message["type"] != "message":
                        continue
                    data = json.loads(message["data"])
                    yield NotificationEvent(**data)
            except RedisConnectionError:
                logger.warning("notification_redis_disconnected_retrying")
                await asyncio.sleep(RECONNECT_DELAY)
                try:
                    await pubsub.subscribe(CHANNEL)
                except Exception:
                    continue