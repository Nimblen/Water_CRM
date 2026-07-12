from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.core.exceptions.auth import InvalidCredentialsError
from app.core.exceptions.not_found import UserNotFoundError



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

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise InvalidCredentialsError()

        access_token = (
            create_access_token(
                user.id,
                user.role.value,
            )
        )

        refresh_token = (
            create_refresh_token(
                user.id,
            )
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }