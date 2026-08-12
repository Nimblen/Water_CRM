from decimal import Decimal
from uuid import UUID
from datetime import datetime, timezone

from app.repositories.idempotency import IdempotencyRepository
from app.schemas.notification import NotificationEvent
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.repositories.route import RouteRepository
from app.repositories.price_settings import PriceSettingsRepository
from app.repositories.notification import NotificationRepository
from app.db.models.payment import Payment
from app.db.models.route import Route
from app.core.constants import DeliveryStatus, NotificationType, RouteStatus, PaymentMethod
from app.core.exceptions.not_found import RouteNotFoundError, RouteCustomerNotFoundError
from app.core.exceptions.conflict import InvalidDeliveryStatusError
from app.services.storage import save_payment_photo
from app.schemas.route import (
    RouteResponse,
    RouteCustomerResponse,
    RouteListItem,
    UpdateDeliveryStatus,
    CompleteDelivery,
)

TERMINAL_STATUSES = (DeliveryStatus.DELIVERED, DeliveryStatus.PAID, DeliveryStatus.FAILED)
DRIVER_SETTABLE_STATUSES = (DeliveryStatus.ON_WAY, DeliveryStatus.FAILED)


class DriverRouteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.route_repo = RouteRepository(session)
        self.price_repo = PriceSettingsRepository(session)
        self.notification_repo = NotificationRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)

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
                payment_amount=rc.payment.amount if rc.payment else Decimal("0"),
                payment_method=rc.payment_method,
                payment_photo=rc.payment.photo_url if rc.payment else None,
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
            route_customers=customers,
        )

    async def update_delivery_status(
        self,
        route_customer_id: UUID,
        driver_id: UUID,
        data: UpdateDeliveryStatus,
    ) -> NotificationEvent:
        rc = await self.route_repo.get_route_customer_for_driver(route_customer_id, driver_id)
        if not rc:
            raise RouteCustomerNotFoundError()

        if rc.status in TERMINAL_STATUSES:
            raise InvalidDeliveryStatusError()

        if data.status not in DRIVER_SETTABLE_STATUSES:
            raise InvalidDeliveryStatusError()

        rc.status = data.status

        if data.status == DeliveryStatus.FAILED:
            rc.completed_at = datetime.now(tz=timezone.utc)
            await self._finalize_route_if_needed(rc.route)

        row = await self.notification_repo.add(
            NotificationType.DELIVERY_STATUS_UPDATED.value,
            {
                "route_id": str(rc.route_id),
                "route_customer_id": str(rc.id),
                "driver_id": str(driver_id),
                "customer_name": rc.customer.full_name,
                "status": data.status.value,
            },
        )
        await self.session.flush()
        return NotificationEvent(
            id=row.id,
            type=NotificationType.DELIVERY_STATUS_UPDATED,
            payload=row.payload,
            created_at=row.created_at,
        )

    async def complete_delivery(
        self,
        route_customer_id: UUID,
        driver_id: UUID,
        data: CompleteDelivery,
        payment_photo: UploadFile | None = None,
    ) -> NotificationEvent:
        rc = await self.route_repo.get_route_customer_for_driver(route_customer_id, driver_id)
        if not rc:
            raise RouteCustomerNotFoundError()

        if rc.status in TERMINAL_STATUSES:
            raise InvalidDeliveryStatusError()

        now = datetime.now(tz=timezone.utc)
        customer = rc.customer
        price_settings = await self.price_repo.get_current()
        photo_url = None
        if payment_photo is not None:
            photo_url = await save_payment_photo(payment_photo)

        delivered_count = data.delivered_bottles or 0
        payment_amount = data.payment_amount if data.payment_amount is not None else Decimal("0")

        if data.bottle_balance is not None:
            rc.delivered_bottles = delivered_count
        rc.payment_method = data.payment_method
        rc.completed_at = now
        rc.status = (
            DeliveryStatus.DELIVERED
            if data.payment_method == PaymentMethod.DEBT
            else DeliveryStatus.PAID
        )

        order_cost = delivered_count * price_settings.water_price
        net = customer.prepayment - customer.debt + payment_amount - order_cost
        customer.bottle_balance = data.bottle_balance
        customer.debt = max(-net, 0)
        customer.prepayment = max(net, 0)
        customer.last_order_date = now

        if data.payment_method != PaymentMethod.DEBT:
            payment = Payment(
                customer_id=customer.id,
                route_customer_id=rc.id,
                amount=payment_amount,
                payment_method=data.payment_method,
                photo_url=photo_url,
            )
            self.session.add(payment)

        route = rc.route
        route.completed_count += 1

        driver = route.driver
        driver.trip_count += 1
        driver.today_trip_count += 1

        await self._finalize_route_if_needed(route)
        row = await self.notification_repo.add(
            NotificationType.DELIVERY_COMPLETED.value,
            {
                "route_id": str(route.id),
                "route_customer_id": str(rc.id),
                "driver_id": str(driver_id),
                "customer_name": customer.full_name,
                "status": rc.status.value,
                "payment_method": data.payment_method.value,
                "payment_amount": str(payment_amount),
                "delivered_bottles": delivered_count,
            },
        )
        await self.session.flush()
        return NotificationEvent(
            id=row.id,
            type=NotificationType.DELIVERY_COMPLETED,
            payload=row.payload,
            created_at=row.created_at,
        )

    async def _finalize_route_if_needed(self, route: Route) -> None:
        if route.status == RouteStatus.CANCELLED:
            return
        unresolved = await self.route_repo.count_unresolved(route.id)
        if unresolved == 0:
            route.status = RouteStatus.COMPLETED