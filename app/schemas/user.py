from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import UserRole

class CreateDriver(BaseModel):
    phone: str
    password: str
    full_name: str


class DriverResponse(BaseModel):
    id: UUID
    user_id: UUID
    phone: str
    full_name: str
    trip_count: int 
    trip_amount: Decimal
    today_trip_count: int
    today_trip_amount: Decimal
    created_at: datetime
    updated_at: datetime


    model_config = ConfigDict(from_attributes=True)



class DriverFilters(BaseModel):
    search: str | None = None
    is_active: bool = True


class UpdateDriver(BaseModel):
    full_name: str | None = Field(default=None)
    phone: str | None = Field(default=None)

    model_config = ConfigDict(extra="ignore")

class UserResponse(BaseModel):
    id: UUID
    phone: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SetPassword(BaseModel):
    phone: str
    password: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str