from typing import Annotated
from uuid import UUID
from datetime import date as date_type

from fastapi import Depends, Query
from app.dependencies.session import SessionDep
from app.core.constants import ExpenseCategory
from app.schemas.expense import AdminExpenseFilters
from app.services.expense import ExpenseService
from app.dependencies.notification import (
    AdminNotificationServiceDep, DriverNotificationServiceDep
)


def get_expense_service(
    session: SessionDep,
    admin_notifications: AdminNotificationServiceDep,
    driver_notifications: DriverNotificationServiceDep,
) -> ExpenseService:
    return ExpenseService(
        session=session,
        admin_notifications=admin_notifications,
        driver_notifications=driver_notifications,
    )


ExpenseServiceDep = Annotated[ExpenseService, Depends(get_expense_service)]


def get_admin_expense_filters(
    driver_id: UUID | None = Query(None),
    date_from: date_type | None = Query(None),
    date_to: date_type | None = Query(None),
    category: ExpenseCategory | None = Query(None),
) -> AdminExpenseFilters:
    return AdminExpenseFilters(
        driver_id=driver_id,
        date_from=date_from,
        date_to=date_to,
        category=category,
    )


AdminExpenseFiltersDep = Annotated[AdminExpenseFilters, Depends(get_admin_expense_filters)]