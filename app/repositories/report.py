from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from app.db.models.route import Route
from app.db.models.order import Order
from app.db.models.payment import Payment
from app.db.models.customer import Customer
from app.db.models.driver import Driver
from app.core.constants import DeliveryStatus
from app.schemas.report import ReportExportFilters, ReportPeriod


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def count_routes(self, period: ReportPeriod) -> int:
        stmt = select(func.count(Route.id)).where(
            Route.date >= period.date_from,
            Route.date <= period.date_to,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_deliveries_by_status(self, period: ReportPeriod, status: DeliveryStatus) -> int:
        stmt = select(func.count(Order.id)).where(
            Order.status == status,
            Order.completed_at.isnot(None),
            func.date(Order.completed_at) >= period.date_from,
            func.date(Order.completed_at) <= period.date_to,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def sum_revenue(self, period: ReportPeriod) -> "Decimal":
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            func.date(Payment.created_at) >= period.date_from,
            func.date(Payment.created_at) <= period.date_to,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def sum_total_debt(self) -> "Decimal":
        stmt = select(func.coalesce(func.sum(Customer.debt), 0))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_drivers_report(self, period: ReportPeriod) -> list[dict]:
        # маршруты и выручка по каждому водителю за период
        routes_stmt = (
            select(
                Driver.id.label("driver_id"),
                Driver.full_name.label("driver_full_name"),
                func.count(func.distinct(Route.id)).label("routes_count"),
            )
            .join(Route, Route.driver_id == Driver.id)
            .where(Route.date >= period.date_from, Route.date <= period.date_to)
            .group_by(Driver.id, Driver.full_name)
        )
        routes_result = await self.session.execute(routes_stmt)
        routes_rows = {row.driver_id: row for row in routes_result.all()}

        deliveries_stmt = (
            select(
                Driver.id.label("driver_id"),
                func.count(Order.id).label("completed_deliveries_count"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_revenue"),
            )
            .join(Route, Route.driver_id == Driver.id)
            .join(Order, Order.route_id == Route.id)
            .join(Payment, Payment.route_customer_id == Order.id)
            .where(
                Order.status == DeliveryStatus.DELIVERED,
                Order.completed_at.isnot(None),
                func.date(Order.completed_at) >= period.date_from,
                func.date(Order.completed_at) <= period.date_to,
            )
            .group_by(Driver.id)
        )
        deliveries_result = await self.session.execute(deliveries_stmt)
        deliveries_rows = {row.driver_id: row for row in deliveries_result.all()}

        driver_ids = set(routes_rows) | set(deliveries_rows)
        report = []
        for driver_id in driver_ids:
            r = routes_rows.get(driver_id)
            d = deliveries_rows.get(driver_id)
            report.append({
                "driver_id": driver_id,
                "driver_full_name": r.driver_full_name if r else None,
                "routes_count": r.routes_count if r else 0,
                "completed_deliveries_count": d.completed_deliveries_count if d else 0,
                "total_revenue": d.total_revenue if d else 0,
            })
        return report
    
    async def get_deliveries_for_export(self, filters: ReportExportFilters) -> list[Order]:
        stmt = (
            select(Order)
            .where(
                Order.status == DeliveryStatus.DELIVERED,
                Order.completed_at.isnot(None),
                func.date(Order.completed_at) >= filters.date_from,
                func.date(Order.completed_at) <= filters.date_to,
            )
            .options(
                selectinload(Order.customer),
                selectinload(Order.route),
                selectinload(Order.payment),
            )
            .order_by(Order.completed_at)
        )
        if filters.driver_id:
                stmt = stmt.join(Route, Order.route_id == Route.id).where(
                    Route.driver_id == filters.driver_id
                )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    