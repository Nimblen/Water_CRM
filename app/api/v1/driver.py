from uuid import UUID
from fastapi import APIRouter, File, UploadFile
from app.dependencies.driver import CurrentDriverIdDep, DriverRouteServiceDep
from app.schemas.route import RouteResponse, RouteListItem, UpdateDeliveryStatus, CompleteDelivery
from app.dependencies.idempotency import IdempotencyKeyDep
router = APIRouter(prefix="/driver", tags=["driver"])


@router.get("/routes", response_model=list[RouteListItem])
async def get_my_routes(
    driver_id: CurrentDriverIdDep,
    service: DriverRouteServiceDep,
):
    return await service.get_my_routes(driver_id)


@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route_detail(
    route_id: UUID,
    driver_id: CurrentDriverIdDep,
    service: DriverRouteServiceDep,
):
    return await service.get_route_detail(route_id, driver_id)


@router.patch("/routes/customers/{route_customer_id}/status", status_code=204)
async def update_delivery_status(
    route_customer_id: UUID,
    data: UpdateDeliveryStatus,
    driver_id: CurrentDriverIdDep,
    service: DriverRouteServiceDep,
):
    await service.update_delivery_status(route_customer_id, driver_id, data)


@router.post("/routes/customers/{route_customer_id}/complete", status_code=204)
async def complete_delivery(
    route_customer_id: UUID,
    data: CompleteDelivery,
    driver_id: CurrentDriverIdDep,
    service: DriverRouteServiceDep,
    idempotency_key: IdempotencyKeyDep,
    payment_photo: UploadFile | None = File(default=None),
):
    await service.complete_delivery(route_customer_id, driver_id, data, payment_photo)
    if idempotency_key:
        await service.idempotency_repo.save(
            idempotency_key, endpoint="/driver/routes/customers/{route_customer_id}/complete",
            status_code=204, response_body={},
        )