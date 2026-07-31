from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.dependencies.common import AuthDep
from app.dependencies.user import CurrentUserDep



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



@router.get("/me", response_model=UserResponse)
async def get_me(
    user: CurrentUserDep,
    ):
    return user