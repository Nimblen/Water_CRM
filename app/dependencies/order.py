from datetime import date
from uuid import UUID
from typing import Annotated
from fastapi import Depends, Query
from app.dependencies.session import SessionDep
from app.dependencies.notification import AdminNotificationServiceDep, DriverNotificationServiceDep
from app.schemas.order import AdminOrderFilters, DriverOrderFilters
from app.services.order import OrderService
from app.core.constants import DeliveryStatus, OrderPurpose, PaymentMethod


def get_admin_order_filters(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    driver_id: UUID | None = Query(default=None),
    route_id: UUID | None = Query(default=None),
    status: DeliveryStatus | None = Query(default=None),
    purpose: OrderPurpose | None = Query(default=None),
    payment_method: PaymentMethod | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
) -> AdminOrderFilters:
    
    return AdminOrderFilters(
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        driver_id=driver_id,
        route_id=route_id,
        status=status,
        purpose=purpose,
        payment_method=payment_method,
        search=search,
    )


def get_driver_order_filters(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    route_id: UUID | None = Query(default=None),
    status: DeliveryStatus | None = Query(default=None),
    purpose: OrderPurpose | None = Query(default=None),
    payment_method: PaymentMethod | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
) -> DriverOrderFilters:
    return DriverOrderFilters(
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        route_id=route_id,
        status=status,
        purpose=purpose,
        payment_method=payment_method,
        search=search,
    )


async def get_order_service(
    session: SessionDep,
    admin_notifications: AdminNotificationServiceDep,
    driver_notifications: DriverNotificationServiceDep
) -> OrderService:
    return OrderService(session, driver_notifications, admin_notifications)


AdminOrderFiltersDep = Annotated[AdminOrderFilters, Depends(get_admin_order_filters)]
DriverOrderFiltersDep = Annotated[DriverOrderFilters, Depends(get_driver_order_filters)]
OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]