from typing import Annotated

from fastapi import Depends
from app.services.driver import DriverService
from app.dependencies.session import SessionDep
from app.schemas.user import DriverFilters
from app.schemas.common import PaginationParams

def get_driver_service(
    session: SessionDep,
) -> DriverService:
    return DriverService(session)
    

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