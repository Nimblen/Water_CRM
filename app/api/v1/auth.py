from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import AuthService




router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    data: LoginRequest,
    service: AuthService
):
    return await service.login(
        phone=data.phone,
        password=data.password,
    )