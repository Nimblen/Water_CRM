from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel
from app.core.constants import DeliveryStatus, OrderPurpose, PaymentMethod
from decimal import Decimal

class OrderCustomerBrief(BaseModel):
    id: UUID
    full_name: str
    phone: str
    address: str

    model_config = {"from_attributes": True}


class OrderRouteBrief(BaseModel):
    id: UUID
    date: date
    driver_id: UUID | None

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

    order_amount: Decimal | None
    water_price_applied: Decimal | None
    damaged_fine_applied: Decimal | None

    completed_at: datetime | None
    created_at: datetime

    customer: OrderCustomerBrief
    route: OrderRouteBrief

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