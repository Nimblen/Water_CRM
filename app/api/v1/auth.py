from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest
from app.schemas.user import ChangePassword, UserResponse, SetPassword
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



@router.post("/change-password", status_code=204)
async def change_password(
    user: CurrentUserDep,
    data: ChangePassword,
    service: AuthDep
):
    return await service.change_password(
        user=user,
        old_password=data.old_password,
        new_password=data.new_password,
    )