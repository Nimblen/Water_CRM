from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from app.core.constants import PaymentMethod


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    payment_method: PaymentMethod
    note: str | None
    photo_url: str | None
    recorded_by_user_id: UUID
    created_at: datetime