from uuid import UUID
from fastapi import APIRouter

from app.dependencies.driver import CurrentDriverIdDep
from app.dependencies.common import PaginationDep
from app.dependencies.order import DriverOrderFiltersDep, OrderServiceDep
from app.schemas.order import OrderResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/driver/orders", tags=["driver:orders"])


@router.get("", response_model=PaginatedResponse[OrderResponse])
async def get_my_orders(
    driver_id: CurrentDriverIdDep,
    pagination: PaginationDep,
    filters: DriverOrderFiltersDep,
    service: OrderServiceDep,
):
    return await service.get_driver_orders(pagination, filters, driver_id)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_my_order(
    order_id: UUID,
    driver_id: CurrentDriverIdDep,
    service: OrderServiceDep,
):
    return await service.get_driver_order(order_id, driver_id)