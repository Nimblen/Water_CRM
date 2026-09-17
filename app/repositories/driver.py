from datetime import date as date_type
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select, func, or_, case
from sqlalchemy.orm import selectinload, joinedload, with_expression
from app.core.constants import DeliveryStatus
from app.db.models.order import Order
from app.db.models.route import Route
from app.schemas.user import DriverFilters
from app.schemas.common import PaginationParams
from app.db.models.driver import Driver
from app.db.models.user import User


class DriverRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        driver: Driver,
    ) -> Driver:
        self.session.add(driver)
        return driver

    @staticmethod
    def _amounts_subquery(today: date_type | None = None):
        today = today or date_type.today()
        return (
            select(
                Route.driver_id.label("driver_id"),
                func.coalesce(func.sum(Order.order_amount), 0).label("trip_amount"),
                func.coalesce(
                    func.sum(case((Route.date == today, Order.order_amount), else_=0)), 0
                ).label("today_trip_amount"),
            )
            .join(Order, Order.route_id == Route.id)
            .where(Order.status == DeliveryStatus.DELIVERED)
            .group_by(Route.driver_id)
            .subquery()
        )

    def _with_amounts(self, stmt, amounts):
        return (
            stmt.outerjoin(amounts, amounts.c.driver_id == Driver.id)
            .options(
                with_expression(Driver.trip_amount, func.coalesce(amounts.c.trip_amount, 0)),
                with_expression(Driver.today_trip_amount, func.coalesce(amounts.c.today_trip_amount, 0)),
            )
        )

    async def get_by_id(self, driver_id: UUID) -> Driver | None:
        amounts = self._amounts_subquery()
        stmt = (
            select(Driver)
            .join(Driver.user)
            .options(joinedload(Driver.user))
            .where(Driver.id == driver_id, User.is_active.is_(True))
        )
        stmt = self._with_amounts(stmt, amounts)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_all(
        self,
        pagination: PaginationParams,
        filters: DriverFilters,
    ) -> tuple[list[Driver], int]:
        base_stmt = select(Driver).join(Driver.user).where(User.is_active.is_(True))
        if filters.search:
            search = f"%{filters.search}%"
            base_stmt = base_stmt.where(
                or_(Driver.full_name.ilike(search), User.phone.ilike(search))
            )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        amounts = self._amounts_subquery()
        stmt = base_stmt.options(selectinload(Driver.user))
        stmt = self._with_amounts(stmt, amounts)
        stmt = (
            stmt.order_by(Driver.full_name)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(stmt)
        drivers = result.unique().scalars().all()
        return drivers, total