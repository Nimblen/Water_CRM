from typing import Annotated
from fastapi import Depends, Request
from app.services.notification import NotificationService


def get_notification_service(request: Request) -> NotificationService:
    return NotificationService(request.app.state.redis)


NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]