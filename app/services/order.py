from uuid import UUID

from app.core.exceptions.not_found import OrderNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.order import OrderRepository, OrderListFilters
from app.schemas.order import (
    AdminOrderFilters,
    DriverOrderFilters,
    OrderResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.core.exceptions.permissions import OrderAccessDeniedError


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OrderRepository(session)

    async def get_admin_orders(
        self, pagination: PaginationParams, filters: AdminOrderFilters
    ) -> PaginatedResponse[OrderResponse]:
        internal_filters = OrderListFilters(**filters.model_dump())
        orders, total = await self.repo.get_list(pagination, internal_filters)
        return build_paginated_response(
            items=[OrderResponse.model_validate(o) for o in orders],
            total=total,
            pagination=pagination,
        )

    async def get_admin_order(self, order_id: UUID) -> OrderResponse:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError()
        return OrderResponse.model_validate(order)

    async def get_driver_orders(
        self,
        pagination: PaginationParams,
        filters: DriverOrderFilters,
        driver_id: UUID,
    ) -> PaginatedResponse[OrderResponse]:
        internal_filters = OrderListFilters(
            **filters.model_dump(),
            driver_id=driver_id,
        )
        orders, total = await self.repo.get_list(pagination, internal_filters)
        return build_paginated_response(
            items=[OrderResponse.model_validate(o) for o in orders],
            total=total,
            pagination=pagination,
        )

    async def get_driver_order(self, order_id: UUID, driver_id: UUID) -> OrderResponse:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError()
        if order.route.driver_id != driver_id:
            raise OrderAccessDeniedError()
        return OrderResponse.model_validate(order)