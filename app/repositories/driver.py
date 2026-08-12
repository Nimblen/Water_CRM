
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload, joinedload
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

    async def get_by_id(
            self,
            driver_id: UUID,
        ) -> Driver | None:

            stmt = (
                select(Driver)
                .join(Driver.user)
                .options(
                    joinedload(Driver.user)
                )
                .where(
                    Driver.id == driver_id,
                    User.is_active.is_(True)
                )
            )

            result = await self.session.execute(stmt)

            return result.scalar_one_or_none()
    

    async def get_all(
        self,
        pagination: PaginationParams,
        filters: DriverFilters,
    ):
        stmt = (
            select(Driver)
            .join(Driver.user)
            .options(
                selectinload(
                    Driver.user
                )
            .where(User.is_active.is_(True))
            )
        )

        if filters.search:
            search = f"%{filters.search}%"

            stmt = stmt.where(
                or_(
                    Driver.full_name.ilike(search),
                    Driver.email.ilike(search),
                    User.phone.ilike(search),
                )
            )

        count_stmt = (
            select(func.count())
            .select_from(
                stmt.subquery()
            )
        )

        total_result = await self.session.execute(
            count_stmt
        )

        total = total_result.scalar_one()
        stmt = (
            stmt
            .order_by(Driver.full_name)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        result = await self.session.execute(
            stmt
        )
        drivers = result.scalars().all()
        return drivers, total