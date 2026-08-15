from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import NotificationType


class NotificationEvent(BaseModel):
    id: int
    type: NotificationType = Field(validation_alias="event_type")
    payload: dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)