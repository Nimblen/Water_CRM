import math
from pydantic import BaseModel, Field
from typing import Generic, TypeVar


T = TypeVar("T")

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
    





class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


def build_paginated_response(items, total, pagination) -> PaginatedResponse:
    pages = math.ceil(total / pagination.page_size) if total else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    )