import asyncio
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from celery import shared_task
from sqlalchemy import update

from app.db.models.route import Route
from app.core.constants import RouteStatus
from app.core.logging import get_logger
BUSINESS_TZ = ZoneInfo("Asia/Tashkent")
PENDING_STATUS = RouteStatus.CREATED
TERMINAL_STATUSES = (RouteStatus.COMPLETED, RouteStatus.CANCELLED)

logger = get_logger("tasks.route_status")


async def _rollover_route_statuses() -> dict[str, int]:
    from app.db.session import async_session_factory
    today = date.today() if BUSINESS_TZ is None else _today_in_tz(BUSINESS_TZ)
    yesterday = today - timedelta(days=1)
    async with async_session_factory() as session:
        cancelled_result = await session.execute(
            update(Route)
            .where(Route.date == yesterday)
            .where(Route.status.not_in(TERMINAL_STATUSES))
            .values(status=RouteStatus.CANCELLED)
        )
        started_result = await session.execute(
            update(Route)
            .where(Route.date == today)
            .where(Route.status == PENDING_STATUS)
            .values(status=RouteStatus.IN_PROGRESS)
        )
        await session.commit()
    return {
        "cancelled": cancelled_result.rowcount or 0,
        "started": started_result.rowcount or 0,
    }


def _today_in_tz(tz: ZoneInfo) -> date:
    from datetime import datetime
    return datetime.now(tz).date()


@shared_task(name="tasks.route.rollover_route_statuses", bind=True, max_retries=3)
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