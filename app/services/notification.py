import asyncio
import json
from collections.abc import AsyncIterator
import uuid

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.repositories.notification import AdminNotificationRepository, DriverNotificationRepository
from app.schemas.notification import NotificationEvent
from app.core.constants import NotificationType

logger = structlog.get_logger("notifications")

CHANNEL = "admin:notifications"
RECONNECT_DELAY = 2
BACKLOG_LIMIT = 200


class AdminNotificationService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def broadcast(
        self,
        session: AsyncSession,
        type_: NotificationType,
        payload: dict,
    ) -> NotificationEvent:
        repo = AdminNotificationRepository(session)
        row = await repo.add(type_.value, payload)
        event = NotificationEvent.model_validate(row)

        try:
            await self.redis.publish(CHANNEL, event.model_dump_json())
        except RedisError:
            logger.warning("notification_publish_failed", event_id=event.id)

        return event

    async def event_source(self, last_id: int) -> AsyncIterator[NotificationEvent]:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(CHANNEL)

        max_sent_id = last_id
        try:
            async for event in self._backlog(last_id):
                max_sent_id = max(max_sent_id, event.id)
                yield event

            while True:
                try:
                    async for raw in pubsub.listen():
                        if raw["type"] != "message":
                            continue
                        event = self._parse(raw["data"])
                        if event is None or event.id <= max_sent_id:
                            continue
                        max_sent_id = event.id
                        yield event
                except RedisError:
                    logger.warning("notification_redis_disconnected_retrying")
                    await asyncio.sleep(RECONNECT_DELAY)
                    try:
                        await pubsub.subscribe(CHANNEL)
                    except RedisError:
                        continue
                    async for event in self._backlog(max_sent_id):
                        max_sent_id = max(max_sent_id, event.id)
                        yield event
        finally:
            await pubsub.unsubscribe(CHANNEL)
            await pubsub.aclose()

    async def _backlog(self, since_id: int) -> AsyncIterator[NotificationEvent]:
        async with async_session() as session:
            repo = AdminNotificationRepository(session)
            rows = await repo.get_since(since_id, limit=BACKLOG_LIMIT)
        for row in rows:
            yield NotificationEvent.model_validate(row)

    def _parse(self, raw: str) -> NotificationEvent | None:
        try:
            return NotificationEvent(**json.loads(raw))
        except Exception:
            logger.warning("notification_parse_failed", raw=raw)
            return None
        


class DriverNotificationService:
    def __init__(self, redis: Redis):
        self.redis = redis

    @staticmethod
    def _channel(driver_id: uuid.UUID) -> str:
        return f"driver:{driver_id}:notifications"

    async def broadcast(
        self,
        session: AsyncSession,
        driver_id: uuid.UUID,
        type_: NotificationType,
        payload: dict,
    ) -> NotificationEvent:
        repo = DriverNotificationRepository(session)
        row = await repo.add(driver_id, type_.value, payload)
        event = NotificationEvent.model_validate(row)

        try:
            await self.redis.publish(self._channel(driver_id), event.model_dump_json())
        except RedisError:
            logger.warning("driver_notification_publish_failed", driver_id=str(driver_id), event_id=event.id)

        return event

    async def event_source(self, driver_id: uuid.UUID, last_id: int) -> AsyncIterator[NotificationEvent]:
        channel = self._channel(driver_id)
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)

        max_sent_id = last_id
        try:
            async for event in self._backlog(driver_id, last_id):
                max_sent_id = max(max_sent_id, event.id)
                yield event

            while True:
                try:
                    async for raw in pubsub.listen():
                        if raw["type"] != "message":
                            continue
                        event = self._parse(raw["data"])
                        if event is None or event.id <= max_sent_id:
                            continue
                        max_sent_id = event.id
                        yield event
                except RedisError:
                    logger.warning("driver_notification_redis_disconnected_retrying", driver_id=str(driver_id))
                    await asyncio.sleep(RECONNECT_DELAY)
                    try:
                        await pubsub.subscribe(channel)
                    except RedisError:
                        continue
                    async for event in self._backlog(driver_id, max_sent_id):
                        max_sent_id = max(max_sent_id, event.id)
                        yield event
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    async def _backlog(self, driver_id: uuid.UUID, since_id: int) -> AsyncIterator[NotificationEvent]:
        async with async_session() as session:
            repo = DriverNotificationRepository(session)
            rows = await repo.get_since(driver_id, since_id, limit=BACKLOG_LIMIT)
        for row in rows:
            yield NotificationEvent.model_validate(row)

    def _parse(self, raw: str) -> NotificationEvent | None:
        try:
            return NotificationEvent(**json.loads(raw))
        except Exception:
            logger.warning("driver_notification_parse_failed", raw=raw)
            return None