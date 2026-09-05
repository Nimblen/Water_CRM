from datetime import date, datetime, timezone
from uuid import UUID
from app.repositories.price_settings import PriceSettingsRepository
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.core.constants import DeliveryStatus, NotificationType, RouteStatus
from app.core.exceptions.conflict import OrderAlreadyCompletedError, OrderNotCompletedError
from app.core.exceptions.not_found import OrderNotFoundError, RouteNotFoundError
from app.core.exceptions.validation import MoveDateInPastError
from app.repositories.route import RouteRepository
from app.services.customer_balance import CustomerBalanceService
from app.services.notification import AdminNotificationService, DriverNotificationService
from app.services.storage import save_image

from app.repositories.order import OrderRepository, OrderListFilters
from app.schemas.order import (
    AdminOrderFilters,
    AdminPaymentUpdate,
    DriverOrderFilters,
    MoveOrder,
    OrderResponse,
    order_to_response,
)
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.core.exceptions.permissions import OrderAccessDeniedError

#TODO: split into driver and admin
class OrderService:
    def __init__(self, session: AsyncSession, driver_notifications: DriverNotificationService, admin_notifications: AdminNotificationService):
        self.session = session
        self.repo = OrderRepository(session)
        self.route_repo = RouteRepository(session)
        self.balance_service = CustomerBalanceService(session)
        self.price_repo = PriceSettingsRepository(session)
        self.driver_notifications = driver_notifications
        self.admin_notifications = admin_notifications

    async def get_admin_orders(
        self, pagination: PaginationParams, filters: AdminOrderFilters
    ) -> PaginatedResponse[OrderResponse]:
        internal_filters = OrderListFilters(**filters.model_dump())
        orders, total = await self.repo.get_list(pagination, internal_filters)
        price_settings = await self.price_repo.get_current()
        return build_paginated_response(
            items=[order_to_response(o, price_settings) for o in orders],
            total=total,
            pagination=pagination,
        )

    async def get_admin_order(self, order_id: UUID) -> OrderResponse:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError()
        price_settings = await self.price_repo.get_current()
        return order_to_response(order, price_settings)

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
        price_settings = await self.price_repo.get_current()
        return build_paginated_response(
            items=[order_to_response(o, price_settings) for o in orders],
            total=total,
            pagination=pagination,
        )

    async def get_driver_order(self, order_id: UUID, driver_id: UUID) -> OrderResponse:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError()
        if order.route.driver_id != driver_id:
            raise OrderAccessDeniedError()
        price_settings = await self.price_repo.get_current()
        return order_to_response(order, price_settings)
    

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


    async def update_order_payment(
        self,
        order_id: UUID,
        payload: AdminPaymentUpdate,
        photo: UploadFile | None,
        admin_id: UUID,
    ) -> None:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError()

        if order.status != DeliveryStatus.DELIVERED:
            raise OrderNotCompletedError()

        paid_amount = await self.repo.get_total_paid(order_id)
        delta = payload.amount - paid_amount

        photo_url = await save_image(photo, directory="payments") if photo is not None else None

        if delta != 0:
            await self.repo.add_payment(
                order_id=order_id,
                customer_id=order.customer_id,
                amount=delta,
                payment_method=payload.payment_method,
                note=payload.note,
                photo_url=photo_url,
                recorded_by_user_id=admin_id,
            )
            await self.balance_service.apply_delta(
                order.customer,
                delta=delta,
                user_id=admin_id,
                reason=f"order_payment_correction:{order_id}",
            )

        order.order_amount = payload.amount
        order.payment_method = payload.payment_method

        await self._notify_payment_updated(order)

    async def _notify_payment_updated(self, order) -> None:
        admin_service = self.admin_notifications
        driver_service = self.driver_notifications
        payload = {"order_id": str(order.id), "order_amount": str(order.order_amount)}

        await admin_service.broadcast(self.session, NotificationType.ORDER_PAYMENT_UPDATED, payload)
        if order.route.driver_id:
            await driver_service.broadcast(
                self.session, order.route.driver_id, NotificationType.ORDER_PAYMENT_UPDATED, payload
            )