from uuid import UUID
from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.driver import DriverServiceDep, DriverFiltersDep, PaginationDep
from app.schemas.user import CreateDriver, DriverResponse, UpdateDriver
from app.schemas.common import PaginatedResponse
from app.dependencies.idempotency import IdempotencyKeyDep
router = APIRouter(
    prefix="/admin/drivers",
    tags=["admin:drivers"],
)


@router.post(
    "",
    response_model=DriverResponse,
    status_code=201,
)
async def create_driver(
    data: CreateDriver,
    _: CurrentAdminDep,
    service: DriverServiceDep,
    idempotency_key: IdempotencyKeyDep,
):
    driver = await service.create_driver(
        data
    )
    if idempotency_key:
        await service.idempotency_repo.save(idempotency_key, endpoint="/admin/drivers", status_code=201, response_body=driver.model_dump(mode="json"))
    return driver


@router.get(
    "/{driver_id}",
    response_model=DriverResponse,
    status_code=200,
)
async def get_driver(
    driver_id: UUID,
    _: CurrentAdminDep,
    service: DriverServiceDep,
):
    return await service.get_driver(driver_id)



@router.get(
    "",
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


@router.delete("/{driver_id}", status_code=204)
async def delete_driver(
    driver_id: UUID,
    _: CurrentAdminDep,
    service: DriverServiceDep,
):
    return await service.deactivate_driver(driver_id)





@router.patch("/{driver_id}", status_code=200)
async def update_driver(
    driver_id: UUID,
    driver_data: UpdateDriver,
    _: CurrentAdminDep,
    service: DriverServiceDep,
):
    return await service.update_driver(dirver_id, driver_data)
    