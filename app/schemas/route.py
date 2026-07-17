from uuid import UUID
from datetime import date as date_type, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.core.constants import DeliveryStatus, RouteStatus


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
    delivered_bottles: int = Field(ge=0)
    payment_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    payment_photo: str | None = Field(default=None, max_length=500)


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