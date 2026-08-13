from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class CreateCustomer(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=20)
    address: str = Field(min_length=1)
    comment: str | None = None
    has_cooler: bool | None = None


class UpdateCustomer(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    address: str | None = Field(default=None, min_length=1)
    comment: str | None = None
    has_cooler: bool | None = None
    is_active: bool | None = None


class CustomerResponse(BaseModel):
    id: UUID
    full_name: str
    phone: str
    address: str
    bottle_balance: int
    prepayment: Decimal
    debt: Decimal
    last_order_date: datetime | None
    is_active: bool
    has_cooler: bool
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerFilters(BaseModel):
    search: str | None = None
    is_active: bool | None = None
    has_debt: bool | None = None
    has_cooler: bool | None = None