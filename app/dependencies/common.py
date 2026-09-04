from typing import Annotated
from pydantic import BaseModel, Field
from fastapi import Depends
from app.dependencies.session import SessionDep
from app.services.auth import AuthService
from app.schemas.common import PaginationParams


async def get_auth_service(session: SessionDep):
    return AuthService(session)


AuthDep = Annotated[AuthService, Depends(get_auth_service)]


PaginationDep = Annotated[
    PaginationParams,
    Depends(),
]