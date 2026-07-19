from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field



class CreateDriver(BaseModel):
    phone: str
    password: str
    email: EmailStr
    full_name: str


class DriverResponse(BaseModel):
    id: UUID
    user_id: UUID
    phone: str
    email: EmailStr
    full_name: str
    trip_count: int 
    today_trip_count: int
    created_at: datetime
    updated_at: datetime


    model_config = ConfigDict(from_attributes=True)



class DriverFilters(BaseModel):
    search: str | None = None


class UpdateDriver(BaseModel):
    full_name: str | None = Field(default=None)
    email: EmailStr | None = Field(default=None)
    phone: str | None = Field(default=None)

    model_config = ConfigDict(extra="ignore")
