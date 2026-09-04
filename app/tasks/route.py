import asyncio
from datetime import date
from zoneinfo import ZoneInfo
from app.db.models.driver import Driver
from app.db.models.order import Order
from celery import shared_task
from sqlalchemy import update, select, exists
from app.db.session import async_session
from app.db.models.route import Route
from app.core.constants import DeliveryStatus, RouteStatus
from app.core.logging import get_logger
BUSINESS_TZ = ZoneInfo("Asia/Tashkent")
PENDING_STATUS = RouteStatus.CREATED
TERMINAL_STATUSES = (RouteStatus.COMPLETED, RouteStatus.CANCELLED)

logger = get_logger("tasks.route_status")

async def _reset_today_trip_counts() -> None:
    async with async_session() as session:
        await session.execute(update(Driver).values(today_trip_count=0))
        await session.commit()


async def _rollover_route_statuses() -> dict[str, int]:
    today = date.today() if BUSINESS_TZ is None else _today_in_tz(BUSINESS_TZ)
    async with async_session() as session:
        completed_result = await session.execute(
            update(Route)
            .where(Route.date < today)
            .where(Route.status.not_in(TERMINAL_STATUSES))
            .where(
                exists(
                    select(Order.id)
                    .where(Order.route_id == Route.id)
                )
            )
            .where(
                ~exists(
                    select(Order.id)
                    .where(Order.route_id == Route.id)
                    .where(Order.status != DeliveryStatus.DELIVERED)
                )
            )
            .values(status=RouteStatus.COMPLETED)
        )
        cancelled_result = await session.execute(
            update(Route)
            .where(Route.date < today)
            .where(Route.status.not_in(TERMINAL_STATUSES))
            .values(status=RouteStatus.CANCELLED)
        )
        started_result = await session.execute(
            update(Route)
            .where(Route.date == today)
            .where(Route.driver_id.isnot(None))
            .where(Route.status == PENDING_STATUS)
            .values(status=RouteStatus.IN_PROGRESS)
        )
        await session.commit()
    return {
        "completed": completed_result.rowcount or 0,
        "cancelled": cancelled_result.rowcount or 0,
        "started": started_result.rowcount or 0,
    }


def _today_in_tz(tz: ZoneInfo) -> date:
    from datetime import datetime
    return datetime.now(tz).date()


@shared_task(name="app.tasks.route.rollover_route_statuses", bind=True, max_retries=3)
def rollover_route_statuses(self):
    try:
        result = asyncio.run(_rollover_route_statuses())
    except Exception as exc:
        logger.error("route_status_rollover_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)

    logger.info(
        "route_status_rollover_done",
        cancelled=result["cancelled"],
        started=result["started"],
    )
    return result



@shared_task(name="app.tasks.route.reset_today_trip_counts", bind=True, max_retries=3)
def reset_today_trip_counts(self):
    try:
        asyncio.run(_reset_today_trip_counts())
    except Exception as exc:
        logger.error("reset_today_trip_counts_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)

    logger.info("reset_today_trip_counts_done")
    return
