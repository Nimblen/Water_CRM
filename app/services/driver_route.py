from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.route import RouteRepository
from app.db.models.payment import Payment
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


class DriverRouteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.route_repo = RouteRepository(session)

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
        async with self.session.begin():
            rc = await self.route_repo.get_route_customer_for_driver(
                route_customer_id, driver_id
            )
            if not rc:
                raise RouteCustomerNotFoundError()

            if rc.status in (DeliveryStatus.DELIVERED, DeliveryStatus.PAID):
                raise InvalidDeliveryStatusError()

            rc.status = data.status

    async def complete_delivery(
        self,
        route_customer_id: UUID,
        driver_id: UUID,
        data: CompleteDelivery,
    ) -> None:
        async with self.session.begin():
            rc = await self.route_repo.get_route_customer_for_driver(
                route_customer_id, driver_id
            )
            if not rc:
                raise RouteCustomerNotFoundError()

            if rc.status in (DeliveryStatus.DELIVERED, DeliveryStatus.PAID):
                raise InvalidDeliveryStatusError()

            now = datetime.now(tz=timezone.utc)
            customer = rc.customer

            rc.delivered_bottles = data.delivered_bottles
            rc.payment_amount = data.payment_amount
            rc.payment_photo = data.payment_photo
            rc.completed_at = now
            rc.status = (
                DeliveryStatus.PAID
                if data.payment_amount > 0
                else DeliveryStatus.DELIVERED
            )

            # FR-7 / BR-4 / BR-5: пересчёт баланса заказчика
            order_cost = data.delivered_bottles * 1  # TODO: подставить актуальную цену бутыли из PriceSettings
            customer.bottle_balance += data.delivered_bottles
            customer.debt = max(customer.debt + order_cost - data.payment_amount, 0)
            customer.prepayment = max(data.payment_amount - order_cost - customer.debt, 0)
            customer.last_order_date = now

            # платёж
            payment = Payment(
                customer_id=customer.id,
                route_customer_id=rc.id,
                amount=data.payment_amount,
                photo_url=data.payment_photo,
            )
            self.session.add(payment)

            # BR-1: маршрут завершён, если все доставки завершены
            route = rc.route
            route.completed_count += 1
            pending = await self.route_repo.count_pending(route.id)
            if pending == 0:
                route.status = RouteStatus.COMPLETED