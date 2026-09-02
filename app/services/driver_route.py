from decimal import Decimal
from uuid import UUID
from datetime import datetime, timezone

from app.core.exceptions.permissions import OrderAccessDeniedError
from app.core.exceptions.validation import BulkPriceRequiredError, DeliveryQuantityRequiredError, InvalidDamagedCountError, PickupQuantityRequiredError
from app.repositories.idempotency import IdempotencyRepository
from app.repositories.order import OrderRepository
from app.schemas.notification import NotificationEvent
from app.services.customer_balance import CustomerBalanceService
from app.services.notification import AdminNotificationService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.repositories.route import RouteRepository
from app.repositories.price_settings import PriceSettingsRepository
from app.db.models.payment import Payment
from app.db.models.route import Route
from app.core.constants import DeliveryStatus, NotificationType, OrderPurpose, RouteStatus, PaymentMethod
from app.core.exceptions.not_found import RouteNotFoundError, OrderNotFoundError
from app.core.exceptions.conflict import InvalidDeliveryStatusError, OrderAlreadyCompletedError
from app.services.storage import save_payment_photo
from app.schemas.route import (
    RouteResponse,
    OrderResponse,
    RouteListItem,
    UpdateDeliveryStatus,
    CompleteDelivery,
)

TERMINAL_STATUSES = (DeliveryStatus.DELIVERED, DeliveryStatus.FAILED)
DRIVER_SETTABLE_STATUSES = (DeliveryStatus.ON_WAY, DeliveryStatus.FAILED)
DRIVER_VISIBLE_STATUSES = (RouteStatus.IN_PROGRESS,)

class DriverRouteService:
    def __init__(self, session: AsyncSession, admin_notifications: AdminNotificationService, driver_notifications: AdminNotificationService):
        self.session = session
        self.route_repo = RouteRepository(session)
        self.price_repo = PriceSettingsRepository(session)
        self.balance_service = CustomerBalanceService(session)
        self.order_repo = OrderRepository(session)
        self.admin_notifications = admin_notifications
        self.driver_notifications = driver_notifications
        self.idempotency_repo = IdempotencyRepository(session)

    async def get_my_routes(self, driver_id: UUID) -> list[RouteListItem]:
        routes = await self.route_repo.get_by_driver(driver_id, DRIVER_VISIBLE_STATUSES)
        return [
            RouteListItem(
                id=r.id,
                date=r.date,
                status=r.status,
                completed_count=r.completed_count,
                total_customers=len(r.orders),
            )
            for r in routes
        ]

    async def get_route_detail(self, route_id: UUID, driver_id: UUID) -> RouteResponse:
        route = await self.route_repo.get_by_id_for_driver(route_id, driver_id, DRIVER_VISIBLE_STATUSES)
        if not route:
            raise RouteNotFoundError()

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

        return RouteResponse(
            id=route.id,
            date=route.date,
            status=route.status,
            completed_count=route.completed_count,
            total_customers=len(customers),
            orders=customers,
        )

    async def update_delivery_status(
        self,
        route_customer_id: UUID,
        driver_id: UUID,
        data: UpdateDeliveryStatus,
    ) -> NotificationEvent:
        rc = await self.route_repo.get_route_customer_for_driver(route_customer_id, driver_id)
        if not rc:
            raise OrderNotFoundError()

        if rc.status in TERMINAL_STATUSES:
            raise InvalidDeliveryStatusError()

        if data.status not in DRIVER_SETTABLE_STATUSES:
            raise InvalidDeliveryStatusError()
        if rc.status == data.status:
            raise InvalidDeliveryStatusError()
        rc.status = data.status

        if data.status == DeliveryStatus.FAILED:
            rc.completed_at = datetime.now(tz=timezone.utc)
            await self._finalize_route_if_needed(rc.route)
        await self.session.flush()
        await self.admin_notifications.broadcast(
            self.session,
            NotificationType.DELIVERY_STATUS_UPDATED,
            {
                "route_id": str(rc.route_id),
                "route_customer_id": str(rc.id),
                "driver_id": str(driver_id),
                "customer_name": rc.customer.full_name,
                "status": data.status.value,
            },
        )


    async def complete_delivery(
        self,
        order_id: UUID,
        payload: CompleteDelivery,
        photo: UploadFile | None,
        driver_id: UUID,
    ) -> None:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError()
        if order.route.driver_id != driver_id:
            raise OrderAccessDeniedError()
        if order.status not in (DeliveryStatus.PENDING, DeliveryStatus.ON_WAY):
            raise OrderAlreadyCompletedError()

        purpose = payload.purpose or order.purpose
        _validate_completion_by_purpose(payload, purpose)

        photo_url = await save_payment_photo(photo) if photo is not None else None

        if purpose == OrderPurpose.DELIVERY_19L:
            order.delivered_bottles = payload.delivered_bottles
            order.returned_bottles = payload.returned_bottles
            order.damaged_bottles = payload.damaged_bottles
        elif purpose == OrderPurpose.BULK_WATER:
            order.bulk_5l_count = payload.bulk_5l_count
            order.bulk_5l_price = payload.bulk_5l_price or Decimal("0.00")
            order.bulk_10l_count = payload.bulk_10l_count
            order.bulk_10l_price = payload.bulk_10l_price or Decimal("0.00")
        elif purpose == OrderPurpose.PICKUP:
            order.picked_coolers = payload.picked_coolers
            order.picked_bottles = payload.picked_bottles
            order.damaged_bottles = payload.damaged_bottles

        if payload.bottle_balance is not None:
            order.customer.bottle_balance = payload.bottle_balance
        price_settings = await self.price_repo.get_current()
        price = order.customer.custom_water_price or price_settings.water_price
        fine = price_settings.damaged_bottle_fine
        water_sum = payload.delivered_bottles * price if purpose == OrderPurpose.DELIVERY_19L else Decimal("0.00")
        damage_sum = payload.damaged_bottles * fine
        bulk_sum = (
            order.bulk_5l_count * order.bulk_5l_price
            + order.bulk_10l_count * order.bulk_10l_price
        )
        order_cost = water_sum + damage_sum + bulk_sum
        order.water_price_applied = price
        order.damaged_fine_applied = fine
        order.order_amount = order_cost
        order.purpose = purpose
        order.status = DeliveryStatus.DELIVERED
        order.completed_at = datetime.now(timezone.utc)
        order.payment_method = payload.payment_method
        order.order_amount = payload.payment_amount

        if payload.payment_method != PaymentMethod.DEBT:
            await self.order_repo.add_payment(
                order_id=order.id,
                customer_id=order.customer_id,
                amount=payload.payment_amount,
                payment_method=payload.payment_method,
                note=None,
                photo_url=photo_url,
                recorded_by_user_id=order.route.driver.user_id,
            )
        delta = payload.payment_amount - order_cost
        await self.balance_service.apply_delta(
            order.customer,
            delta=delta,
            user_id=order.route.driver.user_id,
            reason=f"order_completion:{order.id}",
        )
        status = await self._finalize_route_if_needed(order.route)
        order.route.completed_count += 1
        order.customer.last_order_date = order.completed_at
        order.route.driver.trip_count += 1
        order.route.driver.today_trip_count += 1
        await self.session.flush()
        await self._notify_completion(order, status == RouteStatus.COMPLETED)

    async def _notify_completion(self, order, route_completed: bool) -> None:
        payload = {"order_id": str(order.id), "route_id": str(order.route_id)}
        if order.route.driver_id:
            await self.driver_notifications.broadcast(
                self.session, order.route.driver_id, NotificationType.DELIVERY_COMPLETED, payload
            )
        await self.admin_notifications.broadcast(self.session, NotificationType.DELIVERY_COMPLETED, payload)

        if route_completed:
            route_payload = {"route_id": str(order.route_id)}
            if order.route.driver_id:
                await self.driver_notifications.broadcast(
                    self.session, order.route.driver_id, NotificationType.ROUTE_COMPLETED, route_payload
                )
            await self.admin_notifications.broadcast(self.session, NotificationType.ROUTE_COMPLETED, route_payload)
    async def _finalize_route_if_needed(self, route: Route) -> None:
        if route.status == RouteStatus.CANCELLED:
            return
        unresolved = await self.route_repo.count_unresolved(route.id)
        if unresolved == 0:
            route.status = RouteStatus.COMPLETED
        return route.status


def _validate_completion_by_purpose(payload: CompleteDelivery, purpose: OrderPurpose) -> None:
    if purpose == OrderPurpose.BULK_WATER:
        if payload.bulk_5l_count == 0 and payload.bulk_10l_count == 0:
            raise BulkPriceRequiredError("at least one bulk quantity must be > 0")
        if payload.bulk_5l_count > 0 and not (payload.bulk_5l_price and payload.bulk_5l_price > 0):
            raise BulkPriceRequiredError("bulk_5l_price is required when bulk_5l_count > 0")
        if payload.bulk_10l_count > 0 and not (payload.bulk_10l_price and payload.bulk_10l_price > 0):
            raise BulkPriceRequiredError("bulk_10l_price is required when bulk_10l_count > 0")

    elif purpose == OrderPurpose.DELIVERY_19L:
        if payload.delivered_bottles == 0 and payload.damaged_bottles == 0:
            raise DeliveryQuantityRequiredError(
                "delivered_bottles or damaged_bottles must be > 0"
            )

    elif purpose == OrderPurpose.PICKUP:
        if payload.picked_coolers == 0 and payload.picked_bottles == 0 and payload.damaged_bottles == 0:
            raise PickupQuantityRequiredError(
                "picked_coolers, picked_bottles or damaged_bottles must be > 0"
            )
    if payload.damaged_bottles > payload.returned_bottles + payload.delivered_bottles:
        raise InvalidDamagedCountError(
            "damaged_bottles must be <= returned_bottles + delivered_bottles"
        )
