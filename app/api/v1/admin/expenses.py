from uuid import UUID
from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.common import PaginationDep
from app.dependencies.expense import ExpenseServiceDep, AdminExpenseFiltersDep
from app.schemas.expense import ExpenseResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/admin", tags=["admin:expenses"])


@router.get("/routes/{route_id}/expenses", response_model=list[ExpenseResponse])
async def get_route_expenses(route_id: UUID, _: CurrentAdminDep, service: ExpenseServiceDep):
    return await service.get_admin_route_expenses(route_id)


@router.get("/expenses", response_model=PaginatedResponse[ExpenseResponse])
async def get_expenses(
    _: CurrentAdminDep,
    pagination: PaginationDep,
    filters: AdminExpenseFiltersDep,
    service: ExpenseServiceDep,
):
    return await service.get_admin_expenses(pagination, filters)


@router.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(expense_id: UUID, _: CurrentAdminDep, service: ExpenseServiceDep):
    await service.delete_admin_expense(expense_id)