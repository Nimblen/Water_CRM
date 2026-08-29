import uuid
from sqlalchemy import select, func, nulls_last
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.route import Route
from app.db.models.order import  Order
from app.core.constants import DeliveryStatus, RouteStatus
from app.schemas.route import RouteFilters
from app.schemas.common import PaginationParams


class RouteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_driver(self, driver_id: uuid.UUID, statuses: list[RouteStatus] | None = None) -> list[Route]:
        stmt = (
            select(Route)
            .where(Route.driver_id == driver_id)
            .join(Order)
            .options(selectinload(Route.order))
            .order_by(nulls_last(Order.sequence.asc()))
        )
        if statuses:
            stmt = stmt.where(Route.status.in_(statuses))
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_id_for_driver(self, route_id: uuid.UUID, driver_id: uuid.UUID, statuses: list[RouteStatus] | None = None) -> Route | None:
        stmt = (
            select(Route)
            .where(Route.id == route_id, Route.driver_id == driver_id)
            .options(
                selectinload(Route.order).selectinload(Order.customer),
                selectinload(Route.order).selectinload(Order.payment),
            )
        )
        if statuses:
            stmt = stmt.where(Route.status.in_(statuses))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_route_customer_for_driver(
        self, order_id: uuid.UUID, driver_id: uuid.UUID
    ) -> Order | None:
        stmt = (
            select(Order)
            .join(Route)
            .where(Order.id == order_id, Route.driver_id == driver_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.route),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_unresolved(self, route_id: uuid.UUID) -> int:
        stmt = select(func.count(Order.id)).where(
            Order.route_id == route_id,
            Order.status.in_([DeliveryStatus.PENDING, DeliveryStatus.ON_WAY]),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _apply_filters(self, stmt, filters: RouteFilters):
        if filters.driver_id:
            stmt = stmt.where(Route.driver_id == filters.driver_id)
        if filters.status:
            stmt = stmt.where(Route.status == filters.status)
        if filters.date_from:
            stmt = stmt.where(Route.date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Route.date <= filters.date_to)
        return stmt

    async def create(self, driver_id: uuid.UUID, date_, status: RouteStatus = RouteStatus.CREATED) -> Route:
        route = Route(driver_id=driver_id, date=date_, status=status)
        self.session.add(route)
        await self.session.flush()
        return route

    async def get_by_id(self, route_id: uuid.UUID) -> Route | None:
        stmt = (
            select(Route)
            .where(Route.id == route_id)
            .options(
                selectinload(Route.driver),
                selectinload(Route.order).selectinload(Order.customer),
                selectinload(Route.order).selectinload(Order.payment),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
            self, pagination: PaginationParams, filters: RouteFilters
        ) -> tuple[list[Route], int]:
            base_stmt = self._apply_filters(
                select(Route).options(selectinload(Route.driver), selectinload(Route.order)),
                filters,
            )

            count_stmt = self._apply_filters(select(func.count(Route.id)), filters)
            total = (await self.session.execute(count_stmt)).scalar_one()

            stmt = (
                base_stmt
                .order_by(Route.date.desc())
                .offset(pagination.offset)
                .limit(pagination.page_size)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().unique().all()), total

    async def add_customer(self, route_id: uuid.UUID, customer_id: uuid.UUID, sequence: int | None = None) -> Order:
        rc = Order(route_id=route_id, customer_id=customer_id, status=DeliveryStatus.PENDING, sequence=sequence)
        self.session.add(rc)
        await self.session.flush()
        return rc

    async def get_route_customer(self, route_id: uuid.UUID, customer_id: uuid.UUID) -> Order | None:
        stmt = select(Order).where(
            Order.route_id == route_id,
            Order.customer_id == customer_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, route: Route) -> None:
        await self.session.delete(route)

    async def delete_route_customer(self, rc: Order) -> None:
        await self.session.delete(rc)

    async def count_customers(self, route_id: uuid.UUID) -> int:
        result = await self.session.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.route_id == route_id)
        )
        return result or 0