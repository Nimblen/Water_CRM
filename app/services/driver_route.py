from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.route import RouteRepository
from app.repositories.price_settings import PriceSettingsRepository
from app.db.models.payment import Payment
from app.db.models.route import Route
from app.core.constants import DeliveryStatus, RouteStatus
from app.core.exceptions.not_found import RouteNotFoundError, RouteCustomerNotFoundError
from app.core.exceptions.conflict import InvalidDeliveryStatusError
from app.schemas.route import (
    RouteResponse,
    RouteCustomerResponse,
    RouteListItem,
    UpdateDeliveryStatus,
    CompleteDelivery,
)

TERMINAL_STATUSES = (DeliveryStatus.DELIVERED, DeliveryStatus.PAID, DeliveryStatus.FAILED)


class DriverRouteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.route_repo = RouteRepository(session)
        self.price_repo = PriceSettingsRepository(session)

    async def get_my_routes(self, driver_id: UUID) -> list[RouteListItem]:
        routes = await self.route_repo.get_by_driver(driver_id)
        return [
            RouteListItem(
                id=r.id,
                date=r.date,
                status=r.status,
                completed_count=r.completed_count,
                total_customers=len(r.route_customers),
            )
            for r in routes
        ]

    async def get_route_detail(self, route_id: UUID, driver_id: UUID) -> RouteResponse:
        route = await self.route_repo.get_by_id_for_driver(route_id, driver_id)
        if not route:
            raise RouteNotFoundError()

        customers = [
            RouteCustomerResponse(
                id=rc.id,
                customer_id=rc.customer_id,
                customer_full_name=rc.customer.full_name,
                customer_address=rc.customer.address,
                customer_phone=rc.customer.phone,
                status=rc.status,
                delivered_bottles=rc.delivered_bottles,
                payment_amount=rc.payment_amount,
                payment_photo=rc.payment_photo,
                completed_at=rc.completed_at,
            )
            for rc in route.route_customers
        ]

        return RouteResponse(
            id=route.id,
            date=route.date,
            status=route.status,
            completed_count=route.completed_count,
            total_customers=len(customers),
            customers=customers,
        )

    async def update_delivery_status(
        self,
        route_customer_id: UUID,
        driver_id: UUID,
        data: UpdateDeliveryStatus,
    ) -> None:
        rc = await self.route_repo.get_route_customer_for_driver(
            route_customer_id, driver_id
        )
        if not rc:
            raise RouteCustomerNotFoundError()

        if rc.status in TERMINAL_STATUSES:
            raise InvalidDeliveryStatusError()

        rc.status = data.status

        if data.status == DeliveryStatus.FAILED:
            rc.completed_at = datetime.now(tz=timezone.utc)
            await self._finalize_route_if_needed(rc.route)

    async def complete_delivery(
        self,
        route_customer_id: UUID,
        driver_id: UUID,
        data: CompleteDelivery,
    ) -> None:
        rc = await self.route_repo.get_route_customer_for_driver(
            route_customer_id, driver_id
        )
        if not rc:
            raise RouteCustomerNotFoundError()

        if rc.status in TERMINAL_STATUSES:
            raise InvalidDeliveryStatusError()

        now = datetime.now(tz=timezone.utc)
        customer = rc.customer
        price_settings = await self.price_repo.get_current()

        rc.delivered_bottles = data.delivered_bottles
        rc.payment_amount = data.payment_amount
        rc.payment_photo = data.payment_photo
        rc.completed_at = now
        rc.status = (
            DeliveryStatus.PAID
            if data.payment_amount > 0
            else DeliveryStatus.DELIVERED
        )

        order_cost = data.delivered_bottles * price_settings.water_price
        net = customer.prepayment - customer.debt + data.payment_amount - order_cost

        customer.bottle_balance += data.delivered_bottles
        customer.debt = max(-net, 0)
        customer.prepayment = max(net, 0)
        customer.last_order_date = now

        payment = Payment(
            customer_id=customer.id,
            route_customer_id=rc.id,
            amount=data.payment_amount,
            photo_url=data.payment_photo,
        )
        self.session.add(payment)

        route = rc.route
        route.completed_count += 1
        await self._finalize_route_if_needed(route)

    async def _finalize_route_if_needed(self, route: Route) -> None:
        if route.status == RouteStatus.CANCELLED:
            return
        unresolved = await self.route_repo.count_unresolved(route.id)
        if unresolved == 0:
            route.status = RouteStatus.COMPLETED