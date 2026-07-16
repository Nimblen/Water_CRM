from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID
from app.core.security import verify_token
from app.core.exceptions.auth import InvalidTokenError
from app.core.exceptions.not_found import UserNotFoundError
from app.core.exceptions.permissions import AccessDeniedError
from app.repositories.user import UserRepository
from app.db.models.user import User
from app.core.constants import UserRole
from app.dependencies.session import SessionDep

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(db: SessionDep, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise InvalidTokenError()
    user = await UserRepository(db).get_by_id(UUID(payload["id"]))
    if not user:
        raise UserNotFoundError()
    if not user.is_active:
        raise AccessDeniedError()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_admin(db: SessionDep, user: CurrentUserDep):
    if user.role != UserRole.ADMIN:
        raise AccessDeniedError()
    return user


CurrentAdminDep = Annotated[User, Depends(get_current_admin)]