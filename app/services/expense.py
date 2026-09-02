from uuid import UUID

from app.repositories.idempotency import IdempotencyRepository
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import NotificationType, RouteStatus
from app.core.exceptions.conflict import RouteNotInProgressError
from app.core.exceptions.not_found import ExpenseNotFoundError, RouteNotFoundError
from app.core.exceptions.permissions import ExpenseAccessDeniedError
from app.repositories.expense import ExpenseRepository
from app.repositories.route import RouteRepository
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.schemas.expense import AdminExpenseFilters, CreateExpense, ExpenseResponse
from app.services.notification import AdminNotificationService, DriverNotificationService
from app.services.storage import save_image

class ExpenseService:
    def __init__(
        self,
        session: AsyncSession,
        admin_notifications: AdminNotificationService,
        driver_notifications: DriverNotificationService,
    ):
        self.session = session
        self.repo = ExpenseRepository(session)
        self.route_repo = RouteRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)
        self.admin_notifications = admin_notifications
        self.driver_notifications = driver_notifications

    async def create_expense(
        self,
        route_id: UUID,
        payload: CreateExpense,
        photo: UploadFile | None,
        driver_id: UUID,
    ) -> ExpenseResponse:
        route = await self.route_repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        if route.driver_id != driver_id:
            raise ExpenseAccessDeniedError()
        if route.status != RouteStatus.IN_PROGRESS:
            raise RouteNotInProgressError()

        photo_url = await save_image(photo, directory="expenses") if photo is not None else None

        expense = await self.repo.create(
            route_id=route_id,
            driver_id=driver_id,
            amount=payload.amount,
            category=payload.category,
            comment=payload.comment,
            photo_url=photo_url,
        )

        await self.admin_notifications.broadcast(
            self.session,
            NotificationType.EXPENSE_CREATED,
            {
                "expense_id": str(expense.id),
                "route_id": str(route_id),
                "driver_id": str(driver_id),
                "amount": str(expense.amount),
                "category": expense.category.value,
            },
        )

        return ExpenseResponse.model_validate(expense)

    async def get_driver_route_expenses(
        self, route_id: UUID, driver_id: UUID
    ) -> list[ExpenseResponse]:
        route = await self.route_repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        if route.driver_id != driver_id:
            raise ExpenseAccessDeniedError()

        expenses = await self.repo.get_by_route(route_id)
        return [ExpenseResponse.model_validate(e) for e in expenses]

    async def delete_driver_expense(self, expense_id: UUID, driver_id: UUID) -> None:
        expense = await self.repo.get_by_id(expense_id)
        if not expense:
            raise ExpenseNotFoundError()
        if expense.driver_id != driver_id:
            raise ExpenseAccessDeniedError()

        route = await self.route_repo.get_by_id(expense.route_id)
        if route.status == RouteStatus.COMPLETED:
            raise RouteNotInProgressError()

        await self.repo.delete(expense)
        await self._notify_deleted(expense)

    async def get_admin_route_expenses(self, route_id: UUID) -> list[ExpenseResponse]:
        route = await self.route_repo.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError()
        expenses = await self.repo.get_by_route(route_id)
        return [ExpenseResponse.model_validate(e) for e in expenses]

    async def get_admin_expenses(
        self, pagination: PaginationParams, filters: AdminExpenseFilters
    ) -> PaginatedResponse[ExpenseResponse]:
        expenses, total = await self.repo.get_list(pagination, filters)
        return build_paginated_response(
            items=[ExpenseResponse.model_validate(e) for e in expenses],
            total=total,
            pagination=pagination,
        )

    async def delete_admin_expense(self, expense_id: UUID) -> None:
        expense = await self.repo.get_by_id(expense_id)
        if not expense:
            raise ExpenseNotFoundError()

        await self.repo.delete(expense)
        await self._notify_deleted(expense)

    async def _notify_deleted(self, expense) -> None:
        await self.admin_notifications.broadcast(
            self.session,
            NotificationType.EXPENSE_DELETED,
            {
                "expense_id": str(expense.id),
                "route_id": str(expense.route_id),
                "driver_id": str(expense.driver_id),
            },
        )