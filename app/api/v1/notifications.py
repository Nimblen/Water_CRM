from fastapi import APIRouter, Request, Header, Query
from sse_starlette.sse import EventSourceResponse

from app.dependencies.user import CurrentUserDep
from app.dependencies.notification import DriverNotificationServiceDep

router = APIRouter(prefix="/driver/notifications", tags=["driver-notifications"])


@router.get("/stream")
async def stream_driver_notifications(
    request: Request,
    user: CurrentUserDep,
    service: DriverNotificationServiceDep,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    since: int = Query(default=0),
):
    last_id = int(last_event_id) if last_event_id else since

    async def event_generator():
        async for event in service.event_source(user.driver.id, last_id):
            if await request.is_disconnected():
                return
            yield {
                "id": str(event.id),
                "event": event.type.value,
                "data": event.model_dump_json(),
            }

    return EventSourceResponse(
        event_generator(),
        ping=15,
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )