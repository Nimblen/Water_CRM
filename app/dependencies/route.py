from typing import Annotated
from app.dependencies.notification import DriverNotificationServiceDep
from fastapi import Depends

from app.services.admin_route import AdminRouteService
from app.schemas.route import RouteFilters
from app.dependencies.session import SessionDep


def get_admin_route_service(
    session: SessionDep,
    driver_notifications: DriverNotificationServiceDep,
) -> AdminRouteService:
    return AdminRouteService(session, driver_notifications)

AdminRouteServiceDep = Annotated[AdminRouteService, Depends(get_admin_route_service)]
RouteFiltersDep = Annotated[RouteFilters, Depends()]