from fastapi import APIRouter, Header, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.dependencies.user import CurrentAdminDep
from app.dependencies.session import SessionDep
from app.dependencies.notification import NotificationServiceDep

router = APIRouter(prefix="/admin/notifications", tags=["admin:notifications"])


@router.get("/stream")
async def stream_notifications(
    request: Request,
    admin: CurrentAdminDep,
    session: SessionDep,
    service: NotificationServiceDep,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    since: int = Query(default=0, description="Fallback for the very first connect"),
):

    last_id = int(last_event_id) if last_event_id else since

    async def event_source():
        for event in await service.backlog_since(session, last_id):
            if await request.is_disconnected():
                return
            yield {"id": str(event.id), "event": event.type.value, "data": event.model_dump_json()}

        async for event in service.stream(last_id=last_id):
            if await request.is_disconnected():
                return
            yield {"id": str(event.id), "event": event.type.value, "data": event.model_dump_json()}

    return EventSourceResponse(
        event_source(),
        ping=15,
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )