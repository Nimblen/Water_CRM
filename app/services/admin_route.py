from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.route import RouteRepository
from app.repositories.driver import DriverRepository
from app.repositories.customer import CustomerRepository
from app.core.exceptions.not_found import RouteNotFoundError, DriverNotFoundError, CustomerNotFoundError, RouteCustomerNotFoundError
from app.core.exceptions.conflict import RouteAlreadyStartedError, RouteAlreadyCompletedError
from app.core.exceptions.validation import InvalidUpdateFieldsError
from app.core.constants import RouteStatus
from app.schemas.route import (
    CreateRoute, UpdateRoute, RouteFilters,
    AdminRouteResponse, AdminRouteListItem, RouteCustomerResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.repositories.idempotency import IdempotencyRepository

ALLOWED_ROUTE_UPDATE_FIELDS = {"date"}


class AdminRouteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RouteRepository(session)
        self.driver_repo = DriverRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)

    async def create_route(self, data: CreateRoute) -> AdminRouteResponse:
        driver = await self.driver_repo.get_by_id(data.driver_id)
        if not driver:
            raise DriverNotFoundError()

        route = await self.repo.create(data.driver_id, data.date)
        for customer_id in data.customer_ids:
            customer = await self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.is_active:
                raise CustomerNotFoundError()
            await self.repo.add_customer(route.id, customer_id)

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
                total_customers=len(r.route_customers),
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
        disallowed = set(update_data) - ALLOWED_ROUTE_UPDATE_FIELDS
        if disallowed:
            raise InvalidUpdateFieldsError(disallowed)

        for field, value in update_data.items():
            setattr(route, field, value)

        await self.session.flush()
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

    async def add_customer(self, route_id: UUID, customer_id: UUID) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        customer = await self.customer_repo.get_by_id(customer_id)
        if not customer or not customer.is_active:
            raise CustomerNotFoundError()
        await self.repo.add_customer(route_id, customer_id)

    async def remove_customer(self, route_id: UUID, customer_id: UUID) -> None:
        rc = await self.repo.get_route_customer(route_id, customer_id)
        if not rc:
            raise RouteCustomerNotFoundError()

        await self.repo.delete_route_customer(rc)
        await self.session.flush()

        remaining = await self.repo.count_customers(route_id)
        if remaining == 0:
            route = await self.repo.get_by_id(route_id)
            route.status = RouteStatus.CANCELLED
            await self.session.flush()

    async def cancel_route(self, route_id: UUID) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        if route.status == RouteStatus.COMPLETED:
            raise RouteAlreadyCompletedError()
        route.status = RouteStatus.CANCELLED
        await self.session.flush()

    async def delete_route(self, route_id: UUID) -> None:
        route = await self.repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        await self.repo.delete(route)

    def _to_response(self, route) -> AdminRouteResponse:
        customers = [
            RouteCustomerResponse(
                id=rc.id,
                customer_id=rc.customer_id,
                customer_full_name=rc.customer.full_name,
                customer_address=rc.customer.address,
                customer_phone=rc.customer.phone,
                status=rc.status,
                delivered_bottles=rc.delivered_bottles,
                payment_amount=rc.payment.amount if rc.payment else Decimal("0"),
                payment_method=rc.payment_method,
                payment_photo=rc.payment.photo_url if rc.payment else None,
                completed_at=rc.completed_at,
            )
            for rc in route.route_customers
        ]
        return AdminRouteResponse(
            id=route.id,
            date=route.date,
            status=route.status,
            completed_count=route.completed_count,
            total_customers=len(customers),
            route_customers=customers,
            driver_id=route.driver_id,
            driver_full_name=route.driver.full_name,
        )
