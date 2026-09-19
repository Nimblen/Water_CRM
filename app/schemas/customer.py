from typing import Self
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.core.constants import OrderPurpose, PaymentMethod
from pydantic import BaseModel, Field, model_validator, field_validator


class CreateCustomer(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=20)
    phone_secondary: str | None = Field(default=None, min_length=5, max_length=20)
    address: str = Field(min_length=1)
    comment: str | None = None

    cooler_count: int = Field(default=0, ge=0)
    bottle_balance: int = Field(default=0, ge=0)

    debt: Decimal = Field(default=Decimal("0"), ge=0)
    prepayment: Decimal = Field(default=Decimal("0"), ge=0)

    custom_water_price: Decimal | None = Field(default=None, ge=0)

    last_order_date: date | None = None


    @model_validator(mode="after")
    def validate_balances(self) -> Self:
        if self.debt > 0 and self.prepayment > 0:
            raise ValueError("BOTH_BALANCES_SET")
        return self



    @field_validator("cooler_count")
    def validate_cooler_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("COOLER_COUNT_NEGATIVE")
        return value



    @field_validator("bottle_balance")
    def validate_bottle_balance(cls, value: int) -> int:
        if value < 0:
            raise ValueError("BOTTLE_BALANCE_NEGATIVE")
        return value

    @field_validator("last_order_date")
    def validate_last_order_date(cls, value: date) -> date:
        if value and  value > date.today():
            raise ValueError("LAST_ORDER_DATE_FUTURE")
        return value


class UpdateCustomer(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    phone_secondary: str | None = Field(default=None, min_length=5, max_length=20)
    address: str | None = Field(default=None, min_length=1)
    comment: str | None = None
    is_active: bool | None = None

    cooler_count: int | None = Field(default=None, ge=0)
    bottle_balance: int | None = Field(default=None, ge=0)

    debt: Decimal | None = Field(default=None, ge=0)
    prepayment: Decimal | None = Field(default=None, ge=0)

    custom_water_price: Decimal | None = Field(default=None, ge=0)
    last_order_date: date | None = None


    @field_validator("cooler_count")
    def validate_cooler_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("COOLER_COUNT_NEGATIVE")
        return value


    @field_validator("bottle_balance")
    def validate_bottle_balance(cls, value: int) -> int:
        if value < 0:
            raise ValueError("BOTTLE_BALANCE_NEGATIVE")
        return value

    @field_validator("last_order_date")
    def validate_last_order_date(cls, value: date) -> date:
        if value and  value > date.today():
            raise ValueError("LAST_ORDER_DATE_FUTURE")
        return value

class UpdateCustomerSequence(BaseModel):
    sequence: int


class CustomerResponse(BaseModel):
    id: UUID
    full_name: str
    phone: str
    phone_secondary: str | None
    address: str
    bottle_balance: int
    prepayment: Decimal
    debt: Decimal
    last_order_date: datetime | None
    is_active: bool
    cooler_count: int
    custom_water_price: Decimal | None
    comment: str | None
    created_at: datetime


    model_config = {"from_attributes": True}



class CustomerFilters(BaseModel):
    search: str | None = None
    is_active: bool | None = None
    has_debt: bool | None = None



class CustomerOrderHistoryItem(BaseModel):
    order_id: UUID
    order_date: date
    driver_full_name: str | None
    payment_method: PaymentMethod | None
    purpose: OrderPurpose | None
    delivered_bottles: int
    returned_bottles: int
    bottle_balance_after: int | None
    order_amount: Decimal