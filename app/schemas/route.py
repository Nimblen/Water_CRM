from typing import Annotated
from uuid import UUID
from datetime import date as date_type, datetime
from decimal import Decimal
from app.core.exceptions.validation import PaymentAmountInvalidError
from app.schemas.order import OrderResponse
from fastapi import Form, HTTPException
from pydantic import BaseModel, Field, field_validator
from app.core.constants import DeliveryStatus, RouteStatus, PaymentMethod, OrderPurpose


ALLOWED_MANUAL_STATUSES = {DeliveryStatus.ON_WAY, DeliveryStatus.FAILED}



class RouteCashSummary(BaseModel):
    cash_collected: Decimal = Decimal("0.00")
    cashless_collected: Decimal = Decimal("0.00")
    debt_amount: Decimal = Decimal("0.00")
    expenses_total: Decimal = Decimal("0.00")
    cash_balance: Decimal = Decimal("0.00")




class UpdateDeliveryStatus(BaseModel):
    status: DeliveryStatus

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: DeliveryStatus) -> DeliveryStatus:
        if v not in ALLOWED_MANUAL_STATUSES:
            raise ValueError(
                f"Статус {v} нельзя выставить напрямую. "
                f"Разрешено: {[s.value for s in ALLOWED_MANUAL_STATUSES]}. "
                f"Для DELIVERED используйте /complete."
            )
        return v


class CompleteDelivery(BaseModel):
    purpose: OrderPurpose | None = None
    delivered_bottles: int = 0
    returned_bottles: int = 0
    damaged_bottles: int = 0
    bottle_balance: int | None = None
    bulk_5l_count: int = 0
    bulk_5l_price: Decimal | None = None
    bulk_10l_count: int = 0
    bulk_10l_price: Decimal | None = None
    picked_coolers: int = 0
    picked_bottles: int = 0
    payment_amount: Decimal
    payment_method: PaymentMethod

    @classmethod
    def as_form(
        cls,
        purpose: Annotated[OrderPurpose | None, Form()] = None,
        delivered_bottles: Annotated[int, Form(ge=0)] = 0,
        returned_bottles: Annotated[int, Form(ge=0)] = 0,
        damaged_bottles: Annotated[int, Form(ge=0)] = 0,
        bottle_balance: Annotated[int | None, Form(ge=0)] = None,
        bulk_5l_count: Annotated[int, Form(ge=0)] = 0,
        bulk_5l_price: Annotated[Decimal | None, Form()] = None,
        bulk_10l_count: Annotated[int, Form(ge=0)] = 0,
        bulk_10l_price: Annotated[Decimal | None, Form()] = None,
        picked_coolers: Annotated[int, Form(ge=0)] = 0,
        picked_bottles: Annotated[int, Form(ge=0)] = 0,
        payment_amount: Annotated[Decimal, Form(ge=0)] = Decimal("0"),
        payment_method: Annotated[PaymentMethod, Form()] = ...,
    ) -> "CompleteDelivery":
        if payment_method == PaymentMethod.DEBT:
            if payment_amount != 0:
                raise PaymentAmountInvalidError("payment_amount must be 0 when payment_method is 'debt'")
        elif payment_amount <= 0:
            raise PaymentAmountInvalidError(
                f"payment_amount must be greater than 0 for payment_method '{payment_method}'"
            )

        return cls(
            purpose=purpose,
            delivered_bottles=delivered_bottles,
            returned_bottles=returned_bottles,
            damaged_bottles=damaged_bottles,
            bottle_balance=bottle_balance,
            bulk_5l_count=bulk_5l_count,
            bulk_5l_price=bulk_5l_price,
            bulk_10l_count=bulk_10l_count,
            bulk_10l_price=bulk_10l_price,
            picked_coolers=picked_coolers,
            picked_bottles=picked_bottles,
            payment_amount=payment_amount,
            payment_method=payment_method,
        )

# class OrderResponse(BaseModel):
#     id: UUID
#     customer_id: UUID
#     customer_full_name: str
#     customer_address: str
#     customer_phone: str
#     customer_cooler_count: int
#     status: DeliveryStatus
#     delivered_bottles: int | None
#     payment_amount: Decimal | None
#     payment_method: PaymentMethod | None = None
#     payment_photo: str | None
#     completed_at: datetime | None
#     sequence: int | None

#     model_config = {"from_attributes": True}



class RouteResponse(RouteCashSummary):
    id: UUID
    date: date_type
    status: RouteStatus
    completed_count: int
    total_customers: int
    orders: list[OrderResponse]


class RouteListItem(RouteCashSummary):
    id: UUID
    date: date_type
    status: RouteStatus
    completed_count: int
    total_customers: int



class CustomerOrderInput(BaseModel):
    customer_id: UUID
    order_purpose: OrderPurpose = OrderPurpose.DELIVERY_19L
    sequence: int | None = None


class CreateRoute(BaseModel):
    driver_id: UUID | None = None
    date: date_type
    customer_orders: list[CustomerOrderInput] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date_type) -> date_type:
        if v < datetime.now().date():
            raise ValueError("Дата не может быть в прошлом")
        return v


class UpdateRoute(BaseModel):
    date: date_type | None = None
    status: RouteStatus | None = None

    model_config = {"extra": "ignore"}


class RouteFilters(BaseModel):
    driver_id: UUID | None = None
    status: RouteStatus | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None


class AdminRouteListItem(RouteCashSummary):
    id: UUID
    date: date_type
    status: RouteStatus
    completed_count: int
    total_customers: int
    driver_id: UUID | None
    driver_full_name: str | None


class AdminRouteResponse(RouteCashSummary):
    id: UUID
    date: date_type
    status: RouteStatus
    completed_count: int
    total_customers: int
    orders: list[OrderResponse]
    driver_id: UUID | None
    driver_full_name: str | None
