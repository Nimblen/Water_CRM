from decimal import Decimal
from uuid import UUID
from datetime import date
from sqlalchemy import select, func

from app.db.models.order import Order
from app.db.models.route import Route, RouteExpenses
from app.db.models.customer import Customer
from app.db.models.driver import Driver
from app.core.constants import DeliveryStatus
from app.schemas.report import ReportDateFilter


class ReportRepository:
    def __init__(self, session):
        self.session = session

    async def get_driver_report_rows(self, filters: ReportDateFilter) -> list[dict]:
        stmt = (
            select(Order, Route, Driver, Customer)
            .join(Route, Order.route_id == Route.id)
            .join(Driver, Route.driver_id == Driver.id)
            .join(Customer, Order.customer_id == Customer.id)
            .where(
                Route.date >= filters.date_from,
                Route.date <= filters.date_to,
                Order.status == DeliveryStatus.DELIVERED,
            )
        )
        if filters.driver_id:
            stmt = stmt.where(Route.driver_id == filters.driver_id)

        rows = (await self.session.execute(stmt)).all()

        route_ids = list({r.Route.id for r in rows})
        expenses_by_route = await self._get_expenses_by_route(route_ids)

        result = []
        for row in rows:
            order, route, driver, customer = row.Order, row.Route, row.Driver, row.Customer
            result.append({
                "order": order, "route": route, "driver": driver, "customer": customer,
                "route_expenses_total": expenses_by_route.get(route.id, Decimal("0.00")),
            })
        return result

    async def _get_expenses_by_route(self, route_ids: list[UUID]) -> dict[UUID, Decimal]:
        if not route_ids:
            return {}
        stmt = (
            select(RouteExpenses.route_id, func.coalesce(func.sum(RouteExpenses.amount), 0))
            .where(RouteExpenses.route_id.in_(route_ids))
            .group_by(RouteExpenses.route_id)
        )
        return {row[0]: row[1] for row in (await self.session.execute(stmt)).all()}

    async def get_customer_report_rows(self, filters: ReportDateFilter) -> list[dict]:
        # Заказы за период — для агрегатов "куплено за срок"
        orders_stmt = (
            select(
                Order.customer_id,
                func.coalesce(func.sum(Order.bulk_5l_count + Order.bulk_10l_count), 0).label("bulk_qty"),
                func.coalesce(func.sum(Order.damaged_bottles), 0).label("damaged"),
                func.coalesce(func.sum(Order.delivered_bottles), 0).label("delivered"),
                func.coalesce(func.sum(Order.order_amount), 0).label("realization"),
            )
            .join(Route, Order.route_id == Route.id)
            .where(
                Route.date >= filters.date_from,
                Route.date <= filters.date_to,
                Order.status == DeliveryStatus.DELIVERED,
            )
            .group_by(Order.customer_id)
        )
        if filters.driver_id:
            orders_stmt = orders_stmt.where(Route.driver_id == filters.driver_id)

        aggregates = {row.customer_id: row for row in (await self.session.execute(orders_stmt)).all()}

        customers_stmt = select(Customer).where(Customer.id.in_(aggregates.keys()))
        customers = (await self.session.execute(customers_stmt)).scalars().all()

        return [{"customer": c, "agg": aggregates[c.id]} for c in customers]

    async def get_general_report_rows(self, filters: ReportDateFilter) -> list[dict]:
        stmt = (
            select(Order, Route, Driver, Customer)
            .join(Route, Order.route_id == Route.id)
            .join(Driver, Route.driver_id == Driver.id)
            .join(Customer, Order.customer_id == Customer.id)
            .where(
                Route.date >= filters.date_from,
                Route.date <= filters.date_to,
                Order.status == DeliveryStatus.DELIVERED,
            )
        )
        if filters.driver_id:
            stmt = stmt.where(Route.driver_id == filters.driver_id)

        rows = (await self.session.execute(stmt)).all()
        return [{"order": r.Order, "route": r.Route, "driver": r.Driver, "customer": r.Customer} for r in rows]