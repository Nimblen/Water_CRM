from typing import Annotated
from fastapi import Depends

from app.services.admin_route import AdminRouteService
from app.schemas.route import RouteFilters
from app.dependencies.session import SessionDep


def get_admin_route_service(session: SessionDep) -> AdminRouteService:
    return AdminRouteService(session)


AdminRouteServiceDep = Annotated[AdminRouteService, Depends(get_admin_route_service)]
RouteFiltersDep = Annotated[RouteFilters, Depends()]