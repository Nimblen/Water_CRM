from pydantic import BaseModel

from app.core.constants import UserRole



class LoginRequest(BaseModel):
    phone: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    role: UserRole 


class RefreshRequest(BaseModel):
    refresh_token: str