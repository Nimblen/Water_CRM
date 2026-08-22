from uuid import UUID
from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.route import AdminRouteServiceDep, RouteFiltersDep
from app.dependencies.driver import PaginationDep
from app.schemas.route import CreateRoute, UpdateRoute, AdminRouteResponse, AdminRouteListItem
from app.schemas.customer import UpdateCustomerOrder
from app.schemas.common import PaginatedResponse
from app.dependencies.idempotency import IdempotencyKeyDep
router = APIRouter(prefix="/admin/routes", tags=["admin:routes"])


@router.post("", response_model=AdminRouteResponse, status_code=201)
async def create_route(data: CreateRoute, _: CurrentAdminDep, service: AdminRouteServiceDep, idempotency_key: IdempotencyKeyDep):
    route = await service.create_route(data)
    if idempotency_key:
        await service.idempotency_repo.save(idempotency_key, endpoint="/admin/routes", status_code=201, response_body=route.model_dump(mode="json"))
    return route

@router.get("", response_model=PaginatedResponse[AdminRouteListItem])
async def get_routes(
    _: CurrentAdminDep,
    pagination: PaginationDep,
    filters: RouteFiltersDep,
    service: AdminRouteServiceDep,
):
    return await service.get_routes(pagination, filters)


@router.get("/{route_id}", response_model=AdminRouteResponse)
async def get_route(route_id: UUID, _: CurrentAdminDep, service: AdminRouteServiceDep):
    return await service.get_route(route_id)


@router.patch("/{route_id}", response_model=AdminRouteResponse)
async def update_route(route_id: UUID, data: UpdateRoute, _: CurrentAdminDep, service: AdminRouteServiceDep):
    return await service.update_route(route_id, data)



@router.delete("/{route_id}", status_code=204)
async def delete_route(route_id: UUID, _: CurrentAdminDep, service: AdminRouteServiceDep):
    await service.delete_route(route_id)


@router.post("/{route_id}/cancel", status_code=204)
async def cancel_route(route_id: UUID, _: CurrentAdminDep, service: AdminRouteServiceDep):
    await service.cancel_route(route_id)


@router.patch("/{route_id}/driver/{driver_id}", status_code=204)
async def assign_driver(route_id: UUID, driver_id: UUID, _: CurrentAdminDep, service: AdminRouteServiceDep):
    await service.assign_driver(route_id, driver_id)

@router.patch("/{route_id}/customers/{customer_id}/order", status_code=204)
async def update_customer_order(
    route_id: UUID,
    customer_id: UUID,
    body: UpdateCustomerOrder,
    _: CurrentAdminDep,
    service: AdminRouteServiceDep,
):
    await service.update_customer_order(route_id, customer_id, body.order)

@router.post("/{route_id}/customers/{customer_id}", status_code=204)
async def add_customer(route_id: UUID, customer_id: UUID, _: CurrentAdminDep, service: AdminRouteServiceDep):
    await service.add_customer(route_id, customer_id)


@router.delete("/{route_id}/customers/{customer_id}", status_code=204)
async def remove_customer(route_id: UUID, customer_id: UUID, _: CurrentAdminDep, service: AdminRouteServiceDep):
    await service.remove_customer(route_id, customer_id)