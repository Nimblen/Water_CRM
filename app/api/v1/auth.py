from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest
from app.dependencies.common import AuthDep




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
    service: AuthDep
):
    return await service.login(
        phone=data.phone,
        password=data.password,
    )



@router.post(
    "/refresh",
    response_model=LoginResponse,
)
async def refresh(
    data: RefreshRequest,
    service: AuthDep
):
    return await service.refresh(
        refresh_token=data.refresh_token,
    )