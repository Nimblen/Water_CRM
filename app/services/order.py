from datetime import date, datetime, timezone
from uuid import UUID

from app.core.constants import DeliveryStatus, NotificationType, RouteStatus
from app.core.exceptions.conflict import OrderAlreadyCompletedError
from app.core.exceptions.not_found import OrderNotFoundError, RouteNotFoundError
from app.core.exceptions.validation import MoveDateInPastError
from app.repositories.route import RouteRepository
from app.services.notification import AdminNotificationService, DriverNotificationService
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.order import OrderRepository, OrderListFilters
from app.schemas.order import (
    AdminOrderFilters,
    DriverOrderFilters,
    MoveOrder,
    OrderResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.core.exceptions.permissions import OrderAccessDeniedError

#TODO: split into driver and admin
class OrderService:
    def __init__(self, session: AsyncSession, driver_notifications: DriverNotificationService, admin_notifications: AdminNotificationService):
        self.session = session
        self.repo = OrderRepository(session)
        self.route_repo = RouteRepository(session)
        self.driver_notifications = driver_notifications
        self.admin_notifications = admin_notifications

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
    

    async def move_order(self, order_id: UUID, payload: MoveOrder) -> None:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError()

        if order.status not in (DeliveryStatus.PENDING, DeliveryStatus.ON_WAY):
            raise OrderAlreadyCompletedError()

        old_route = order.route
        old_route_id = old_route.id
        old_driver_id = old_route.driver_id

        if payload.target_route_id is not None:
            target_route = await self.route_repo.get_by_id(payload.target_route_id)
            if not target_route:
                raise RouteNotFoundError()
        else:
            if payload.order_date < date.today():
                raise MoveDateInPastError()
            target_route = await self.route_repo.find_by_date_and_driver(
                payload.order_date, payload.driver_id
            )
            if not target_route:
                target_route = await self.route_repo.create(
                    driver_id=None,
                    date_=payload.order_date,
                    status=RouteStatus.CREATED,
                )

        target_route_id = target_route.id
        target_was_completed = target_route.status == RouteStatus.COMPLETED

        last_sequence = await self.repo.get_max_sequence(target_route_id) or 0
        order.route_id = target_route_id
        order.sequence = last_sequence + 1
        order.moved_from_route_id = old_route_id
        order.moved_at = datetime.now(timezone.utc)

        if target_was_completed:
            target_route.status = RouteStatus.IN_PROGRESS

        await self.session.flush()

        remaining = await self.repo.count_by_route(old_route_id)
        if remaining == 0 and old_route.status != RouteStatus.COMPLETED:
            old_route.status = RouteStatus.CANCELLED

        await self._notify_move(
            order_id=order.id,
            old_route_id=old_route_id,
            old_driver_id=old_driver_id,
            target_route=target_route,
        )

    async def _notify_move(
        self, order_id, old_route_id, old_driver_id, target_route
    ) -> None:
        admin_service = self.admin_notifications
        driver_service = self.driver_notifications

        if old_driver_id:
            await driver_service.broadcast(
                self.session, old_driver_id, NotificationType.CUSTOMER_REMOVED,
                {"order_id": str(order_id), "route_id": str(old_route_id)},
            )
            await driver_service.broadcast(
                self.session, old_driver_id, NotificationType.ROUTE_UPDATED,
                {"route_id": str(old_route_id)},
            )

        if target_route.driver_id and target_route.status == RouteStatus.IN_PROGRESS:
            await driver_service.broadcast(
                self.session, target_route.driver_id, NotificationType.CUSTOMER_ADDED,
                {"order_id": str(order_id), "route_id": str(target_route.id)},
            )
            await driver_service.broadcast(
                self.session, target_route.driver_id, NotificationType.ROUTE_UPDATED,
                {"route_id": str(target_route.id)},
            )

        await admin_service.broadcast(
            self.session, NotificationType.ORDER_MOVED,
            {"order_id": str(order_id), "from_route_id": str(old_route_id), "to_route_id": str(target_route.id)},
        )