from typing import Self
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator, field_validator


class CreateCustomer(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=20)
    address: str = Field(min_length=1)
    comment: str | None = None

    cooler_count: int = Field(default=0, ge=0)

    debt: Decimal = Field(default=Decimal("0"), ge=0)
    prepayment: Decimal = Field(default=Decimal("0"), ge=0)

    custom_water_price: Decimal | None = Field(default=None, ge=0)



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


class UpdateCustomer(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    address: str | None = Field(default=None, min_length=1)
    comment: str | None = None
    is_active: bool | None = None

    cooler_count: int | None = Field(default=None, ge=0)

    debt: Decimal | None = Field(default=None, ge=0)
    prepayment: Decimal | None = Field(default=None, ge=0)

    custom_water_price: Decimal | None = Field(default=None, ge=0)


    @field_validator("cooler_count")
    def validate_cooler_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("COOLER_COUNT_NEGATIVE")
        return value

class UpdateCustomerSequence(BaseModel):
    sequence: int


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
    cooler_count: int
    custom_water_price: Decimal | None
    comment: str | None
    created_at: datetime


    model_config = {"from_attributes": True}



class CustomerFilters(BaseModel):
    search: str | None = None
    is_active: bool | None = None
    has_debt: bool | None = None