from typing import Annotated

from fastapi import Depends, Request

from app.dependencies.session import SessionDep
from app.repositories.notification import NotificationRepository
from app.services.notification import NotificationService


def get_redis(request: Request):
    return request.app.state.redis


def get_notification_service(redis=Depends(get_redis)) -> NotificationService:
    return NotificationService(redis)


def get_notification_repo(session: SessionDep) -> NotificationRepository:
    return NotificationRepository(session)


NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
NotificationRepositoryDep = Annotated[NotificationRepository, Depends(get_notification_repo)]