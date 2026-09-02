import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.route import RouteExpenses
from app.schemas.common import PaginationParams
from app.schemas.expense import AdminExpenseFilters


class ExpenseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        route_id: uuid.UUID,
        driver_id: uuid.UUID,
        amount,
        category,
        comment: str | None,
        photo_url: str | None,
    ) -> RouteExpenses:
        expense = RouteExpenses(
            route_id=route_id,
            driver_id=driver_id,
            amount=amount,
            category=category,
            comment=comment,
            photo_url=photo_url,
        )
        self.session.add(expense)
        await self.session.flush()
        return expense

    async def get_by_id(self, expense_id: uuid.UUID) -> RouteExpenses | None:
        return await self.session.get(RouteExpenses, expense_id)

    async def get_by_route(self, route_id: uuid.UUID) -> list[RouteExpenses]:
        result = await self.session.execute(
            select(RouteExpenses)
            .where(RouteExpenses.route_id == route_id)
            .order_by(RouteExpenses.created_at)
        )
        return list(result.scalars().all())

    async def delete(self, expense: RouteExpenses) -> None:
        await self.session.delete(expense)
        await self.session.flush()

    async def get_list(
        self, pagination: PaginationParams, filters: AdminExpenseFilters
    ) -> tuple[list[RouteExpenses], int]:
        stmt = select(RouteExpenses)
        count_stmt = select(func.count()).select_from(RouteExpenses)

        if filters.driver_id:
            stmt = stmt.where(RouteExpenses.driver_id == filters.driver_id)
            count_stmt = count_stmt.where(RouteExpenses.driver_id == filters.driver_id)
        if filters.category:
            stmt = stmt.where(RouteExpenses.category == filters.category)
            count_stmt = count_stmt.where(RouteExpenses.category == filters.category)
        if filters.date_from:
            stmt = stmt.where(RouteExpenses.created_at >= filters.date_from)
            count_stmt = count_stmt.where(RouteExpenses.created_at >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(RouteExpenses.created_at < filters.date_to)
            count_stmt = count_stmt.where(RouteExpenses.created_at < filters.date_to)

        stmt = (
            stmt.order_by(RouteExpenses.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )

        total = (await self.session.execute(count_stmt)).scalar_one()
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total