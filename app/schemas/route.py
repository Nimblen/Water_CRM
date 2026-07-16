from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import RouteStatus, DeliveryStatus


class RouteCustomerResponse(BaseModel):
    id: UUID
    customer_id: UUID
    customer_full_name: str
    customer_address: str
    customer_phone: str
    status: DeliveryStatus
    delivered_bottles: int | None = Field(default=None)
    payment_amount: Decimal | None = Field(default=None)
    payment_photo: str | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class RouteResponse(BaseModel):
    id: UUID
    date: date
    status: RouteStatus
    completed_count: int
    total_customers: int
    customers: list[RouteCustomerResponse]

    model_config = ConfigDict(from_attributes=True)


class RouteListItem(BaseModel):
    id: UUID
    date: date
    status: RouteStatus
    completed_count: int
    total_customers: int

    model_config = ConfigDict(from_attributes=True)


class UpdateDeliveryStatus(BaseModel):
    status: DeliveryStatus


class CompleteDelivery(BaseModel):
    delivered_bottles: int = Field(ge=0)
    payment_amount: Decimal = Field(ge=0)
    payment_photo: str | None = Field(default=None)