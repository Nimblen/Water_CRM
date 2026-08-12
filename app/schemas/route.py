from typing import Annotated
from uuid import UUID
from datetime import date as date_type, datetime
from decimal import Decimal
from fastapi import Form, HTTPException
from pydantic import BaseModel, Field, field_validator
from app.core.constants import DeliveryStatus, RouteStatus, PaymentMethod


ALLOWED_MANUAL_STATUSES = {DeliveryStatus.ON_WAY, DeliveryStatus.FAILED}


class UpdateDeliveryStatus(BaseModel):
    status: DeliveryStatus

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: DeliveryStatus) -> DeliveryStatus:
        if v not in ALLOWED_MANUAL_STATUSES:
            raise ValueError(
                f"Статус {v} нельзя выставить напрямую. "
                f"Разрешено: {[s.value for s in ALLOWED_MANUAL_STATUSES]}. "
                f"Для DELIVERED/PAID используйте /complete."
            )
        return v


class CompleteDelivery(BaseModel):
    delivered_bottles: int
    payment_amount: Decimal
    payment_method: PaymentMethod
    bottle_balance: int | None = None

    @classmethod
    def as_form(
        cls,
        delivered_bottles: Annotated[int, Form()],
        payment_amount: Annotated[Decimal, Form()],
        payment_method: Annotated[PaymentMethod, Form()],
        bottle_balance: Annotated[int | None, Form()] = None,
    ) -> "CompleteDelivery":
        if payment_method == PaymentMethod.DEBT:
            if payment_amount != 0:
                raise HTTPException(
                    422, "payment_amount must be 0 when payment_method is 'debt'"
                )
        elif payment_amount <= 0:
            raise HTTPException(
                422, f"payment_amount must be greater than 0 for payment_method '{payment_method}'"
            )

        return cls(
            delivered_bottles=delivered_bottles,
            payment_amount=payment_amount,
            payment_method=payment_method,
            bottle_balance=bottle_balance,
        )
class RouteCustomerResponse(BaseModel):
    id: UUID
    customer_id: UUID
    customer_full_name: str
    customer_address: str
    customer_phone: str
    status: DeliveryStatus
    delivered_bottles: int | None
    payment_amount: Decimal | None
    payment_photo: str | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}

class RouteResponse(BaseModel):
    id: UUID
    date: date_type
    status: RouteStatus
    completed_count: int
    total_customers: int
    route_customers: list[RouteCustomerResponse]

    model_config = {"from_attributes": True}


class RouteListItem(BaseModel):
    id: UUID
    date: date_type
    status: RouteStatus
    completed_count: int
    total_customers: int

    model_config = {"from_attributes": True}





class CreateRoute(BaseModel):
    driver_id: UUID
    date: date_type
    customer_ids: list[UUID] = Field(default_factory=list)


class UpdateRoute(BaseModel):
    date: date_type | None = None
    status: RouteStatus | None = None


class RouteFilters(BaseModel):
    driver_id: UUID | None = None
    status: RouteStatus | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None


class AdminRouteListItem(RouteListItem):
    driver_id: UUID
    driver_full_name: str


class AdminRouteResponse(RouteResponse):
    driver_id: UUID
    driver_full_name: str