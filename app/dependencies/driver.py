from typing import Annotated
from uuid import UUID
from fastapi import Depends
from app.services.driver import DriverService
from app.services.driver_route import DriverRouteService
from app.dependencies.session import SessionDep
from app.dependencies.user import CurrentUserDep
from app.schemas.user import DriverFilters
from app.schemas.common import PaginationParams
from app.core.exceptions.permissions import AccessDeniedError
from app.core.constants import UserRole

def get_driver_service( 
    session: SessionDep,
) -> DriverService:
    return DriverService(session)

def get_driver_route_service(
    session: SessionDep,
) -> DriverRouteService:
    return DriverRouteService(session)


async def get_current_driver_id(user: CurrentUserDep) -> UUID:
    if user.role != UserRole.DRIVER:
        raise AccessDeniedError()
    if not user.driver:
        raise AccessDeniedError()
    return user.driver.id


DriverServiceDep = Annotated[
    DriverService,
    Depends(get_driver_service),
]


DriverFiltersDep = Annotated[
    DriverFilters,
    Depends(),
]


PaginationDep = Annotated[
    PaginationParams,
    Depends(),
]



CurrentDriverIdDep = Annotated[UUID, Depends(get_current_driver_id)]


DriverRouteServiceDep = Annotated[
    DriverRouteService,
    Depends(get_driver_route_service),
]