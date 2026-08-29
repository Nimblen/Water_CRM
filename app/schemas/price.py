from typing import Self
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class PriceSettingsResponse(BaseModel):
    id: UUID
    water_price: Decimal
    deposit_price: Decimal
    damaged_bottle_fine: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class CreatePriceSettings(BaseModel):
    water_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    deposit_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    damaged_bottle_fine: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)

    @model_validator(mode="after")
    def validate_at_least_one_field_present(self) -> Self:
        provided_fields = self.model_fields_set
        if not provided_fields:
            raise ValueError("At least one price field must be provided")
        has_valid_value = any(
            getattr(self, field) is not None 
            for field in provided_fields
        )

        if not has_valid_value:
            raise ValueError("At least one price field must have a non-null value")

        return self