from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.core.exceptions.auth import InvalidCredentialsError, TokenTypeError
from app.core.exceptions.not_found import UserNotFoundError
from app.core.exceptions.permissions import AccessDeniedError
from app.core.security import create_access_token, create_refresh_token, verify_password, verify_token


class AuthService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.user_repo = UserRepository(
            session
        )

    async def login(
        self,
        phone: str,
        password: str,
    ):
        user = (
            await self.user_repo
            .get_by_phone(phone)
        )

        if not user:
            raise UserNotFoundError()

        if not user.is_active:
            raise AccessDeniedError()

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise InvalidCredentialsError()

        access_token = (
            create_access_token(
                {"id": str(user.id),}
            )
        )

        refresh_token = (
            create_refresh_token(
                {"id": str(user.id)},
            )
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(
        self,
        refresh_token: str,
    ):
        payload = verify_token(refresh_token)

        if not payload:
            raise InvalidCredentialsError()
        if payload["token_type"] != "refresh":
            raise TokenTypeError()
        user = await self.user_repo.get_by_id(UUID(payload["id"]))
        if not user:
            raise UserNotFoundError()
        if not user.is_active:
            raise AccessDeniedError()
        access_token = (
            create_access_token(
                {"id": str(user.id),}
            )
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
