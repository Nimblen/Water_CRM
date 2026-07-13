from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, EmailStr, ConfigDict



class CreateDriver(BaseModel):
    phone: str
    password: str
    email: EmailStr
    full_name: str


class DriverResponse(BaseModel):
    id: uuid4
    user_id: uuid4
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


