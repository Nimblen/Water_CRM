from typing import Annotated
from uuid import UUID
from app.dependencies.notification import AdminNotificationServiceDep, DriverNotificationServiceDep
from fastapi import Depends
from app.services.driver import DriverService
from app.services.driver_route import DriverRouteService
from app.dependencies.session import SessionDep
from app.dependencies.user import CurrentUserDep
from app.schemas.user import DriverFilters
from app.core.exceptions.permissions import AccessDeniedError
from app.core.constants import UserRole

def get_driver_service( 
    session: SessionDep,
) -> DriverService:
    return DriverService(session)

def get_driver_route_service(
    session: SessionDep,
    admin_notifications: AdminNotificationServiceDep,
    driver_notifications: DriverNotificationServiceDep,
) -> DriverRouteService:
    return DriverRouteService(session, admin_notifications, driver_notifications)


async def get_current_driver_id(user: CurrentUserDep) -> UUID:
    if user.role != UserRole.DRIVER:
        raise AccessDeniedError()
    if not user.driver:
        raise AccessDeniedError()
    return user.driver.id


async def get_current_driver_user_id(user: CurrentUserDep) -> UUID:
    # Отдельная зависимость, потому что get_current_driver_id возвращает
    # drivers.id, а payments.recorded_by_user_id ссылается на users.id — из
    # одного вывести другое нельзя. Существующие ручки не трогаем: этот id
    # нужен только там, где записывается платёж.
    if user.role != UserRole.DRIVER:
        raise AccessDeniedError()
    if not user.driver:
        raise AccessDeniedError()
    return user.id


DriverServiceDep = Annotated[
    DriverService,
    Depends(get_driver_service),
]


DriverFiltersDep = Annotated[
    DriverFilters,
    Depends(),
]






CurrentDriverIdDep = Annotated[UUID, Depends(get_current_driver_id)]


CurrentDriverUserIdDep = Annotated[UUID, Depends(get_current_driver_user_id)]


DriverRouteServiceDep = Annotated[
    DriverRouteService,
    Depends(get_driver_route_service),
]