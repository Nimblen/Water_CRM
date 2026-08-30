from typing import Annotated
from uuid import UUID
from datetime import date as date_type, datetime
from decimal import Decimal
from fastapi import Form, HTTPException
from pydantic import BaseModel, Field, computed_field, field_validator
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
                f"Для DELIVERED используйте /complete."
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
class OrderResponse(BaseModel):
    id: UUID
    customer_id: UUID
    customer_full_name: str
    customer_address: str
    customer_phone: str
    customer_has_cooler: bool
    status: DeliveryStatus
    delivered_bottles: int | None
    payment_amount: Decimal | None
    payment_method: PaymentMethod | None = None
    payment_photo: str | None
    completed_at: datetime | None
    sequence: int | None

    model_config = {"from_attributes": True}

    # Сборки клиента живут в сторах месяцами, и на сервере одновременно работают
    # старое и новое приложение: установленные читают `order`, новые — `sequence`.
    # Отдаём оба ключа. Именно computed_field, а не второе обычное поле — тогда
    # значения физически не могут разъехаться, если правку внесут только в одно.
    @computed_field
    @property
    def order(self) -> int | None:
        return self.sequence


class RouteResponse(BaseModel):
    id: UUID
    date: date_type
    status: RouteStatus
    completed_count: int
    total_customers: int
    orders: list[OrderResponse]

    model_config = {"from_attributes": True}

    # Установленные сборки читают route_customers. Без этого ключа маршрут
    # открывается ПУСТЫМ и у водителя, и у админа — список точек просто не
    # находится в ответе. Отдаём то же содержимое, что и в orders.
    @computed_field
    @property
    def route_customers(self) -> list[OrderResponse]:
        return self.orders


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


class AdminRouteListItem(RouteListItem):
    driver_id: UUID
    driver_full_name: str


class AdminRouteResponse(RouteResponse):
    driver_id: UUID
    driver_full_name: str