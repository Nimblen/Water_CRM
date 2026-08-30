from uuid import UUID
from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.common import PaginationDep
from app.dependencies.order import AdminOrderFiltersDep, OrderServiceDep
from app.schemas.order import OrderResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/admin/orders", tags=["admin:orders"])


@router.get("", response_model=PaginatedResponse[OrderResponse])
async def get_orders(
    _: CurrentAdminDep,
    pagination: PaginationDep,
    filters: AdminOrderFiltersDep,
    service: OrderServiceDep,
):
    return await service.get_admin_orders(pagination, filters)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    _: CurrentAdminDep,
    service: OrderServiceDep,
):
    return await service.get_admin_order(order_id)