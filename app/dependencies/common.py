from typing import Annotated
from pydantic import BaseModel, Field
from fastapi import Depends
from app.dependencies.session import SessionDep
from app.services.auth import AuthService



async def get_auth_service(session: SessionDep):
    return AuthService(session)


AuthDep = Annotated[AuthService, Depends(get_auth_service)]



class PaginationParams(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    @property
    def offset(self):
        return (
            self.page - 1
        ) * self.page_size