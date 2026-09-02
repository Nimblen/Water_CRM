from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, ConfigDict

from app.core.constants import ExpenseCategory


class CreateExpense(BaseModel):
    amount: Decimal
    category: ExpenseCategory
    comment: str | None = None

    @classmethod
    def as_form(
        cls,
        amount: Annotated[Decimal, Form(gt=0)],
        category: Annotated[ExpenseCategory, Form()],
        comment: Annotated[str | None, Form()] = None,
    ) -> "CreateExpense":
        return cls(amount=amount, category=category, comment=comment)


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    driver_id: UUID
    amount: Decimal
    category: ExpenseCategory
    comment: str | None
    photo_url: str | None
    created_at: datetime


class AdminExpenseFilters(BaseModel):
    driver_id: UUID | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None
    category: ExpenseCategory | None = None