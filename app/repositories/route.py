from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.route import Route
from app.db.models.route_customer import RouteCustomer


class RouteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_driver(self, driver_id: UUID) -> list[Route]:
        stmt = (
            select(Route)
            .where(Route.driver_id == driver_id)
            .options(selectinload(Route.route_customers))
            .order_by(Route.date.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id_for_driver(
        self, route_id: UUID, driver_id: UUID
    ) -> Route | None:
        stmt = (
            select(Route)
            .where(Route.id == route_id, Route.driver_id == driver_id)
            .options(
                selectinload(Route.route_customers).selectinload(
                    RouteCustomer.customer
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_route_customer_for_driver(
        self, route_customer_id: UUID, driver_id: UUID
    ) -> RouteCustomer | None:
        stmt = (
            select(RouteCustomer)
            .join(Route, RouteCustomer.route_id == Route.id)
            .where(
                RouteCustomer.id == route_customer_id,
                Route.driver_id == driver_id,
            )
            .options(
                selectinload(RouteCustomer.route),
                selectinload(RouteCustomer.customer),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_pending(self, route_id: UUID) -> int:
        stmt = select(func.count()).where(
            RouteCustomer.route_id == route_id,
            RouteCustomer.status.in_(["pending", "on_way"]),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()