from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.driver import DriverServiceDep, DriverFiltersDep, PaginationDep
from app.schemas.user import CreateDriver, DriverResponse, UpdateDriver
from app.schemas.common import PaginatedResponse

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.post(
    "/drivers",
    response_model=DriverResponse,
    status_code=201,
)
async def create_driver(
    data: CreateDriver,
    _: CurrentAdminDep,
    service: DriverServiceDep,
):
    return await service.create_driver(
        data
    )


@router.get(
    "/drivers/{driver_id}",
    response_model=DriverResponse,
    status_code=200,
)
async def get_driver(
    driver_id: str,
    _: CurrentAdminDep,
    service: DriverServiceDep,
):
    return await service.get_driver(driver_id)



@router.get(
    "/drivers",
    response_model=PaginatedResponse[
        DriverResponse
    ],
)
async def get_drivers(
    _: CurrentAdminDep,
    pagination: PaginationDep,
    filters: DriverFiltersDep,
    service: DriverServiceDep,
):
    return await service.get_drivers(
        pagination,
        filters,
    )


@router.delete("/drivers/{driver_id}", status_code=204)
async def delete_driver(
    driver_id: str,
    _: CurrentAdminDep,
    service: DriverServiceDep,
):
    return await service.deactivate_driver(driver_id)





@router.patch("/drivers/{driver_id}", status_code=200)
async def update_driver(
    driver_data: UpdateDriver,
    _: CurrentAdminDep,
    service: DriverServiceDep,
):
    return await service.update_driver(driver_data)
    