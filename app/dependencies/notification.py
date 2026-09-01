from typing import Annotated
from fastapi import Depends, Request
from app.services.notification import AdminNotificationService, DriverNotificationService


def get_notification_service(request: Request) -> AdminNotificationService:
    return AdminNotificationService(request.app.state.redis)


AdminNotificationServiceDep = Annotated[AdminNotificationService, Depends(get_notification_service)]


def get_driver_notification_service(request: Request) -> DriverNotificationService:
    return DriverNotificationService(request.app.state.redis)


DriverNotificationServiceDep = Annotated[DriverNotificationService, Depends(get_driver_notification_service)]