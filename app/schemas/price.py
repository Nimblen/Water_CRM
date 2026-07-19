from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PriceSettingsResponse(BaseModel):
    id: UUID
    water_price: Decimal
    deposit_price: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class CreatePriceSettings(BaseModel):
    water_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    deposit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)