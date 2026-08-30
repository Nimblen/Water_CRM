from typing import Self
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field, model_validator, field_validator


class CreateCustomer(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=20)
    address: str = Field(min_length=1)
    comment: str | None = None

    cooler_count: int = Field(default=0, ge=0)

    debt: Decimal = Field(default=Decimal("0"), ge=0)
    prepayment: Decimal = Field(default=Decimal("0"), ge=0)

    custom_water_price: Decimal | None = Field(default=None, ge=0)

    # Установленные сборки админки не знают про cooler_count и шлют булев
    # has_cooler. exclude=True — чтобы поле не попало в model_dump() и не ушло
    # в setattr на ORM-объект: колонки has_cooler в БД больше нет.
    has_cooler: bool | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def validate_balances(self) -> Self:
        if self.debt > 0 and self.prepayment > 0:
            raise ValueError("BOTH_BALANCES_SET")
        return self

    @model_validator(mode="after")
    def apply_legacy_has_cooler(self) -> Self:
        # Явно переданный cooler_count выигрывает: его шлёт только новый клиент,
        # и он несёт точное число, тогда как has_cooler — лишь признак наличия.
        if self.has_cooler is None or "cooler_count" in self.model_fields_set:
            return self
        self.cooler_count = max(self.cooler_count, 1) if self.has_cooler else 0
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

    # То же legacy-поле, что и в CreateCustomer. Здесь оно НЕ разрешается в
    # схеме: правило "true -> max(cooler_count, 1)" опирается на текущее
    # значение из БД, которого схема не видит. Иначе старая сборка админки,
    # прислав has_cooler=true, срезала бы заказчика с 3 кулерами до 1.
    # Разрешается в CustomerService.update_customer.
    has_cooler: bool | None = Field(default=None, exclude=True)

    @field_validator("cooler_count")
    def validate_cooler_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("COOLER_COUNT_NEGATIVE")
        return value

class UpdateCustomerSequence(BaseModel):
    # Установленные сборки шлют {"order": N}, новые — {"sequence": N}.
    # Принимаем оба имени, иначе старый клиент получает 422 на смене порядка.
    sequence: int | None = None
    order: int | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def resolve_sequence(self) -> Self:
        if self.sequence is None:
            if self.order is None:
                raise ValueError("SEQUENCE_REQUIRED")
            self.sequence = self.order
        return self


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

    # Колонки has_cooler в БД больше нет — считаем в ответе, чтобы установленные
    # сборки, которые читают этот ключ, продолжали работать.
    @computed_field
    @property
    def has_cooler(self) -> bool:
        return self.cooler_count > 0

class CustomerFilters(BaseModel):
    search: str | None = None
    is_active: bool | None = None
    has_debt: bool | None = None
    has_cooler: bool | None = None