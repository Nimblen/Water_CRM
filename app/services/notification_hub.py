
import asyncio
import json
import uuid
from collections import defaultdict
from contextlib import suppress

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.schemas.notification import NotificationEvent

logger = structlog.get_logger("notifications.hub")

ADMIN_CHANNEL = "admin:notifications"
DRIVER_CHANNEL_PATTERN = "driver:*:notifications"

QUEUE_MAXSIZE = 256

RECONNECT_DELAY_INITIAL = 1.0
RECONNECT_DELAY_MAX = 30.0

class NotificationHub:
    """Единая точка Redis Pub/Sub + локальный fan-out."""

    def __init__(self, redis: Redis):
        self.redis = redis
        self._pubsub = None
        self._reader_task: asyncio.Task | None = None

        self._admin_subscribers: set[asyncio.Queue[NotificationEvent]] = set()
        self._driver_subscribers: dict[
            uuid.UUID, set[asyncio.Queue[NotificationEvent]]
        ] = defaultdict(set)

        self.stats = {
            "reconnects": 0,
            "parse_errors": 0,
            "dropped_for_slow_consumer": 0,
        }

    async def start(self) -> None:
        await self._connect()
        self._reader_task = asyncio.create_task(
            self._reader_loop(), name="notification-hub-reader"
        )

    async def stop(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        if self._pubsub is not None:
            with suppress(RedisError):
                await self._pubsub.aclose()
            self._pubsub = None

    async def _connect(self) -> None:
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe(ADMIN_CHANNEL, DRIVER_CHANNEL_PATTERN)
        self._pubsub = pubsub
    async def _reader_loop(self) -> None:
        delay = RECONNECT_DELAY_INITIAL
        while True:
            try:
                assert self._pubsub is not None
                async for raw in self._pubsub.listen():
                    if raw["type"] not in ("message", "pmessage"):
                        continue
                    delay = RECONNECT_DELAY_INITIAL  # успешный трафик — сброс backoff
                    self._handle_raw(raw)
            except asyncio.CancelledError:
                raise
            except RedisError:
                self.stats["reconnects"] += 1
                logger.warning(
                    "notification_hub_redis_disconnected",
                    retry_in=delay,
                    reconnects_total=self.stats["reconnects"],
                )
                if self._pubsub is not None:
                    with suppress(RedisError):
                        await self._pubsub.aclose()
                    self._pubsub = None
                await asyncio.sleep(delay)
                delay = min(delay * 2, RECONNECT_DELAY_MAX)
                try:
                    await self._connect()
                except RedisError:
                    continue

    def _handle_raw(self, raw: dict) -> None:
        channel = raw.get("channel")
        if isinstance(channel, bytes):
            channel = channel.decode()
        event = self._parse(raw["data"])
        if event is None:
            return
        self._dispatch(channel, event)

    def _parse(self, raw: bytes | str) -> NotificationEvent | None:
        try:
            return NotificationEvent(**json.loads(raw))
        except Exception:
            self.stats["parse_errors"] += 1
            logger.warning("notification_hub_parse_failed")
            return None

    def _dispatch(self, channel: str, event: NotificationEvent) -> None:
        if channel == ADMIN_CHANNEL:
            targets = tuple(self._admin_subscribers)
        elif channel.startswith("driver:"):
            try:
                driver_id = uuid.UUID(channel.split(":")[1])
            except (IndexError, ValueError):
                return
            targets = tuple(self._driver_subscribers.get(driver_id, ()))
        else:
            return

        for queue in targets:
            self._put_nowait_with_backpressure(queue, event)

    def _put_nowait_with_backpressure(
        self, queue: asyncio.Queue, event: NotificationEvent
    ) -> None:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            self.stats["dropped_for_slow_consumer"] += 1
            with suppress(asyncio.QueueEmpty):
                queue.get_nowait()
            with suppress(asyncio.QueueFull):
                queue.put_nowait(event)

    def subscribe_admin(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self._admin_subscribers.add(queue)
        return queue

    def unsubscribe_admin(self, queue: asyncio.Queue) -> None:
        self._admin_subscribers.discard(queue)

    def subscribe_driver(self, driver_id: uuid.UUID) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self._driver_subscribers[driver_id].add(queue)
        return queue

    def unsubscribe_driver(self, driver_id: uuid.UUID, queue: asyncio.Queue) -> None:
        subs = self._driver_subscribers.get(driver_id)
        if subs is None:
            return
        subs.discard(queue)
        if not subs:
            del self._driver_subscribers[driver_id]
