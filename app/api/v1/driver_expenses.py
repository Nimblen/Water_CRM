from typing import Annotated
from uuid import UUID
from app.dependencies.idempotency import IdempotencyKeyDep
from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies.driver import CurrentDriverIdDep
from app.dependencies.common import PaginationDep
from app.dependencies.expense import ExpenseServiceDep
from app.schemas.expense import CreateExpense, ExpenseResponse

router = APIRouter(prefix="/driver", tags=["driver:expenses"])


@router.post("/routes/{route_id}/expenses", response_model=ExpenseResponse)
async def create_expense(
    route_id: UUID,
    driver_id: CurrentDriverIdDep,
    service: ExpenseServiceDep,
    idempotency_key: IdempotencyKeyDep,
    payload: CreateExpense = Depends(CreateExpense.as_form),
    photo: UploadFile | None = File(None),
):
    expense = await service.create_expense(route_id, payload, photo, driver_id=driver_id)
    if idempotency_key:
        await service.idempotency_repo.save(idempotency_key, endpoint="/driver/routes/{route_id}/expenses", status_code=201, response_body=expense.model_dump(mode="json"))
    return expense
@router.get("/routes/{route_id}/expenses", response_model=list[ExpenseResponse])
async def get_route_expenses(
    route_id: UUID,
    driver_id: CurrentDriverIdDep,
    service: ExpenseServiceDep,
):
    return await service.get_driver_route_expenses(route_id, driver_id=driver_id)


@router.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: UUID,
    driver_id: CurrentDriverIdDep,
    service: ExpenseServiceDep,
):
    await service.delete_driver_expense(expense_id, driver_id=driver_id)