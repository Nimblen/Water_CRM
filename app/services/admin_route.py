from datetime import date
from decimal import Decimal
from uuid import UUID
from app.db.models.route import Route
from app.services.notification import DriverNotificationService
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.route import RouteRepository
from app.repositories.driver import DriverRepository
from app.repositories.customer import CustomerRepository
from app.core.exceptions.not_found import RouteNotFoundError, DriverNotFoundError, CustomerNotFoundError, OrderNotFoundError
from app.core.exceptions.conflict import RouteAlreadyStartedError, RouteAlreadyCompletedError
from app.core.exceptions.validation import InvalidUpdateFieldsError
from app.core.constants import NotificationType, RouteStatus
from app.schemas.route import (
    CreateRoute, UpdateRoute, RouteFilters,
    AdminRouteResponse, AdminRouteListItem, OrderResponse, CustomerOrderInput
)
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.repositories.idempotency import IdempotencyRepository




class AdminRouteService:
    def __init__(self, session: AsyncSession, driver_notifications: DriverNotificationService):
        self.session = session
        self.repo = RouteRepository(session)
        self.driver_repo = DriverRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)
        self.driver_notifications = driver_notifications

    async def _notify_driver_if_in_progress(
        self, route: Route, type_: NotificationType, payload: dict
    ) -> None:
        if route.status != RouteStatus.IN_PROGRESS:
            return
        await self.driver_notifications.broadcast(
            self.session, route.driver_id, type_, payload
        )

    async def create_route(self, data: CreateRoute) -> AdminRouteResponse:
        driver = await self.driver_repo.get_by_id(data.driver_id)
        if not driver:
            raise DriverNotFoundError()
        today = date.today()
        if data.date < today:
            raise InvalidUpdateFieldsError(
                "Дата маршрута не может быть в прошлом"
            )

        status = (
            RouteStatus.IN_PROGRESS
            if data.date == today
            else RouteStatus.CREATED
        )
        route = await self.repo.create(data.driver_id, data.date, status)
        # TODO: Оптимизировать n + 1 запросы
        for index, customer_data in enumerate(data.customer_orders, start=1):
            customer = await self.customer_repo.get_by_id(customer_data.customer_id)
            if not customer or not customer.is_active:
                raise CustomerNotFoundError()
            await self.repo.add_customer(route.id, customer_data.customer_id, customer_data.order_purpose or OrderPurpose.DELIVERY_19L,  sequence=index)

        await self.session.flush()
        route = await self.repo.get_by_id(route.id)
        return self._to_response(route)

    async def get_route(self, route_id: UUID) -> AdminRouteResponse:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        return self._to_response(route)

    async def get_routes(
        self, pagination: PaginationParams, filters: RouteFilters
    ) -> PaginatedResponse[AdminRouteListItem]:
        routes, total = await self.repo.get_list(pagination, filters)
        items = [
            AdminRouteListItem(
                id=r.id,
                date=r.date,
                status=r.status,
                completed_count=r.completed_count,
                total_customers=len(r.orders),
                driver_id=r.driver_id,
                driver_full_name=r.driver.full_name,
            )
            for r in routes
        ]
        return build_paginated_response(items=items, total=total, pagination=pagination)

    async def update_route(self, route_id: UUID, data: UpdateRoute) -> AdminRouteResponse:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(route, field, value)

        await self.session.flush()
        await self._notify_driver_if_in_progress(
            route,
            NotificationType.ROUTE_UPDATED,
            {"route_id": str(route.id), "changed_fields": list(update_data.keys())},
        )
        await self.session.refresh(route)
        return self._to_response(route)

    async def assign_driver(self, route_id: UUID, driver_id: UUID) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        if route.status != RouteStatus.CREATED:
            raise RouteAlreadyStartedError()
        driver = await self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError()
        route.driver_id = driver_id
        await self.session.flush()

    async def add_customer(self, route_id: UUID, customer_data: CustomerOrderInput, sequence: int | None = None) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        customer = await self.customer_repo.get_by_id(customer_data.customer_id)
        if not customer or not customer.is_active:
            raise CustomerNotFoundError()
        await self.repo.add_customer(route_id, customer_data.customer_id, customer_data.order_purpose or OrderPurpose.DELIVERY_19L, sequence)
        await self.session.flush()
        await self._notify_driver_if_in_progress(
            route,
            NotificationType.CUSTOMER_ADDED,
            {
                "route_id": str(route.id),
                "customer_id": str(customer_id),
                "customer_full_name": customer.full_name,
                "customer_address": customer.address,
            },
        )

    async def update_customer_sequence(self, route_id: UUID, customer_id: UUID, sequence: int) -> None:
        #TODO: In the future добавить bulk update
        rc = await self.repo.get_route_customer(route_id, customer_id)
        if not rc:
            raise OrderNotFoundError()
        rc.sequence = sequence
        await self.session.flush()

    async def remove_customer(self, route_id: UUID, customer_id: UUID) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()

        rc = await self.repo.get_route_customer(route_id, customer_id)
        if not rc:
            raise OrderNotFoundError()

        was_in_progress = route.status == RouteStatus.IN_PROGRESS

        await self.repo.delete_route_customer(rc)
        await self.session.flush()

        remaining = await self.repo.count_customers(route_id)
        cancelled = False
        if remaining == 0 and route.status != RouteStatus.COMPLETED:
            route.status = RouteStatus.CANCELLED
            cancelled = True
            await self.session.flush()

        if not was_in_progress:
            return

        await self.driver_notifications.broadcast(
            self.session,
            route.driver_id,
            NotificationType.CUSTOMER_REMOVED,
            {"route_id": str(route_id), "customer_id": str(customer_id)},
        )
        if cancelled:
            await self.driver_notifications.broadcast(
                self.session,
                route.driver_id,
                NotificationType.ROUTE_CANCELLED,
                {"route_id": str(route_id)},
            )

    async def cancel_route(self, route_id: UUID) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        if route.status == RouteStatus.COMPLETED:
            raise RouteAlreadyCompletedError()
        was_in_progress = route.status == RouteStatus.IN_PROGRESS
        route.status = RouteStatus.CANCELLED
        await self.session.flush()
        if was_in_progress:
            await self.driver_notifications.broadcast(
                self.session,
                route.driver_id,
                NotificationType.ROUTE_CANCELLED,
                {"route_id": str(route.id)},
            )

    async def delete_route(self, route_id: UUID) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        await self.repo.delete(route)

    def _to_response(self, route) -> AdminRouteResponse:
        customers = [
            OrderResponse(
                id=rc.id,
                customer_id=rc.customer_id,
                customer_full_name=rc.customer.full_name,
                customer_address=rc.customer.address,
                customer_phone=rc.customer.phone,
                customer_cooler_count=rc.customer.cooler_count,
                status=rc.status,
                delivered_bottles=rc.delivered_bottles,
                payment_amount=rc.payment.amount if rc.payment else Decimal("0"),
                payment_method=rc.payment_method,
                payment_photo=rc.payment.photo_url if rc.payment else None,
                completed_at=rc.completed_at,
                sequence=rc.sequence,
            )
            for rc in route.orders
        ]
        return AdminRouteResponse(
            id=route.id,
            date=route.date,
            status=route.status,
            completed_count=route.completed_count,
            total_customers=len(customers),
            orders=customers,
            driver_id=route.driver_id,
            driver_full_name=route.driver.full_name,
        )
