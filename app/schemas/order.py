from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, model_validator
from app.core.constants import DeliveryStatus, OrderPurpose, PaymentMethod
from app.schemas.payment import PaymentResponse
from decimal import Decimal

class OrderCustomerBrief(BaseModel):
    customer_id: UUID
    customer_full_name: str
    customer_phone: str
    customer_address: str
    customer_cooler_count: int
    customer_debt: Decimal
    customer_prepayment: Decimal
    model_config = {"from_attributes": True}


class OrderRouteBrief(BaseModel):
    route_id: UUID
    route_date: date
    driver_id: UUID | None
    driver_full_name: str| None
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    number: int
    sequence: int | None
    status: DeliveryStatus
    purpose: OrderPurpose
    payment_method: PaymentMethod | None
    delivered_bottles: int | None
    returned_bottles: int | None
    damaged_bottles: int | None
    bottle_balance_after: int | None

    bulk_5l_count: int | None
    bulk_5l_price: Decimal | None
    bulk_10l_count: int | None
    bulk_10l_price: Decimal | None
    picked_coolers: int | None
    picked_bottles: int | None

    water_price_applied: Decimal | None
    damaged_fine_applied: Decimal | None
    order_amount: Decimal | None
    paid_amount: Decimal | None
    effective_water_price: Decimal | None = None
    damaged_bottle_fine: Decimal | None = None

    completed_at: datetime | None
    created_at: datetime

    customer: OrderCustomerBrief
    route: OrderRouteBrief
    payments: list[PaymentResponse]

    model_config = {"from_attributes": True}



class AdminOrderFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    customer_id: UUID | None = None
    driver_id: UUID | None = None
    route_id: UUID | None = None
    status: DeliveryStatus | None = None
    purpose: OrderPurpose | None = None
    payment_method: PaymentMethod | None = None
    search: str | None = None




class DriverOrderFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    customer_id: UUID | None = None
    route_id: UUID | None = None
    status: DeliveryStatus | None = None
    purpose: OrderPurpose | None = None
    payment_method: PaymentMethod | None = None
    search: str | None = None



class MoveOrder(BaseModel):
    target_route_id: Optional[UUID] = None
    order_date: Optional[date] = None
    driver_id: Optional[UUID] = None

    @model_validator(mode="after")
    def check_exactly_one_variant(self):
        if self.target_route_id is not None and self.order_date is not None:
            raise ValueError("Provide either target_route_id or order_date, not both")
        if self.target_route_id is None and self.order_date is None:
            raise ValueError("Either target_route_id or order_date is required")
        if self.target_route_id is not None and self.driver_id is not None:
            raise ValueError("driver_id is only used with the order_date variant")
        return self

    @property
    def is_by_date(self) -> bool:
        return self.order_date is not None
    




class AdminPaymentUpdate(BaseModel):
    amount: Decimal
    payment_method: PaymentMethod
    note: Optional[str] = None


def order_to_response(order, price_settings=None) -> "OrderResponse":
    payments = [
    PaymentResponse.model_validate(payment)
    for payment in order.payments
    ]
    paid_amount = sum((p.amount for p in payments), Decimal("0"))
    is_completed = order.completed_at is not None

    effective_water_price = None
    damaged_bottle_fine = None
    if not is_completed and price_settings is not None:
        effective_water_price = order.customer.custom_water_price or price_settings.water_price
        damaged_bottle_fine = price_settings.damaged_bottle_fine

    return OrderResponse(
        id=order.id,
        number=order.number,
        sequence=order.sequence,
        status=order.status,
        purpose=order.purpose,
        payment_method=order.payment_method,
        delivered_bottles=order.delivered_bottles,
        returned_bottles=order.returned_bottles,
        damaged_bottles=order.damaged_bottles,
        bottle_balance_after=order.bottle_balance_after,
        bulk_5l_count=order.bulk_5l_count,
        bulk_5l_price=order.bulk_5l_price,
        bulk_10l_count=order.bulk_10l_count,
        bulk_10l_price=order.bulk_10l_price,
        picked_coolers=order.picked_coolers,
        picked_bottles=order.picked_bottles,
        water_price_applied=order.water_price_applied,
        damaged_fine_applied=order.damaged_fine_applied,
        order_amount=order.order_amount,
        paid_amount=paid_amount,
        effective_water_price=effective_water_price,
        damaged_bottle_fine=damaged_bottle_fine,
        completed_at=order.completed_at,
        created_at=order.created_at,
        customer=OrderCustomerBrief(
            customer_id=order.customer_id,
            customer_full_name=order.customer.full_name,
            customer_phone=order.customer.phone,
            customer_address=order.customer.address,
            customer_cooler_count=order.customer.cooler_count,
            customer_debt=order.customer.debt,
            customer_prepayment=order.customer.prepayment,
        ),
        route=OrderRouteBrief(
            route_id=order.route.id,
            route_date=order.route.date,
            driver_id=order.route.driver_id,
            driver_full_name=order.route.driver.full_name if order.route.driver else None,
        ),
        payments=payments,
    )