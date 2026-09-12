import asyncio
import uuid
from collections.abc import AsyncIterator

import structlog
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.core.constants import NotificationType
from app.repositories.notification import (
    AdminNotificationRepository,
    DriverNotificationRepository,
)
from app.schemas.notification import NotificationEvent
from app.services.notification_hub import NotificationHub

logger = structlog.get_logger("notifications")

BACKLOG_LIMIT = 200

HEARTBEAT_INTERVAL = 15.0


class AdminNotificationService:
    def __init__(self, redis, hub: NotificationHub):
        self.redis = redis
        self.hub = hub

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
            await self.redis.publish(
                "admin:notifications", event.model_dump_json()
            )
        except Exception:
            logger.warning("notification_publish_failed", event_id=event.id)

        return event

    async def event_source(
        self, last_id: int, request: Request
    ) -> AsyncIterator[NotificationEvent]:
        queue = self.hub.subscribe_admin()
        try:
            max_sent_id = last_id

            async for event in self._backlog(last_id):
                max_sent_id = max(max_sent_id, event.id)
                yield event

            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=HEARTBEAT_INTERVAL
                    )
                except asyncio.TimeoutError:
                    continue

                if event.id <= max_sent_id:
                    continue
                max_sent_id = event.id
                yield event
        finally:
            self.hub.unsubscribe_admin(queue)

    async def _backlog(self, since_id: int) -> AsyncIterator[NotificationEvent]:
        async with async_session() as session:
            repo = AdminNotificationRepository(session)
            rows = await repo.get_since(since_id, limit=BACKLOG_LIMIT)
        for row in rows:
            yield NotificationEvent.model_validate(row)


class DriverNotificationService:
    def __init__(self, redis, hub: NotificationHub):
        self.redis = redis
        self.hub = hub

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
        except Exception:
            logger.warning(
                "driver_notification_publish_failed",
                driver_id=str(driver_id),
                event_id=event.id,
            )

        return event

    async def event_source(
        self, driver_id: uuid.UUID, last_id: int, request: Request
    ) -> AsyncIterator[NotificationEvent]:
        queue = self.hub.subscribe_driver(driver_id)
        try:
            max_sent_id = last_id

            async for event in self._backlog(driver_id, last_id):
                max_sent_id = max(max_sent_id, event.id)
                yield event

            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=HEARTBEAT_INTERVAL
                    )
                except asyncio.TimeoutError:
                    continue

                if event.id <= max_sent_id:
                    continue
                max_sent_id = event.id
                yield event
        finally:
            self.hub.unsubscribe_driver(driver_id, queue)

    async def _backlog(
        self, driver_id: uuid.UUID, since_id: int
    ) -> AsyncIterator[NotificationEvent]:
        async with async_session() as session:
            repo = DriverNotificationRepository(session)
            rows = await repo.get_since(driver_id, since_id, limit=BACKLOG_LIMIT)
        for row in rows:
            yield NotificationEvent.model_validate(row)
