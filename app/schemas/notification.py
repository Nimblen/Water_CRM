from typing import Any
from datetime import datetime
from pydantic import BaseModel

from app.core.constants import NotificationType





class NotificationEvent(BaseModel):
    id: int
    type: NotificationType
    payload: dict[str, Any]
    created_at: datetime
