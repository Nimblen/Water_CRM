from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.report import ReportRepository
from app.repositories.driver import DriverRepository
from app.core.constants import DeliveryStatus
from app.schemas.report import ReportPeriod, SummaryReport, DriverReportItem


class AdminReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ReportRepository(session)
        self.driver_repo = DriverRepository(session)

    async def get_summary(self, period: ReportPeriod) -> SummaryReport:
        routes_count = await self.repo.count_routes(period)
        completed = await self.repo.count_deliveries_by_status(period, DeliveryStatus.DELIVERED)
        failed = await self.repo.count_deliveries_by_status(period, DeliveryStatus.FAILED)
        revenue = await self.repo.sum_revenue(period)
        debt = await self.repo.sum_total_debt()

        return SummaryReport(
            routes_count=routes_count,
            completed_deliveries_count=completed,
            failed_deliveries_count=failed,
            total_revenue=revenue,
            total_debt=debt,
        )

    async def get_drivers_report(self, period: ReportPeriod) -> list[DriverReportItem]:
        rows = await self.repo.get_drivers_report(period)

        items = []
        for row in rows:
            driver_full_name = row["driver_full_name"]
            if driver_full_name is None:
                driver = await self.driver_repo.get_by_id(row["driver_id"])
                driver_full_name = driver.full_name if driver else "—"

            items.append(DriverReportItem(
                driver_id=row["driver_id"],
                driver_full_name=driver_full_name,
                routes_count=row["routes_count"],
                completed_deliveries_count=row["completed_deliveries_count"],
                total_revenue=row["total_revenue"],
            ))
        return sorted(items, key=lambda x: x.total_revenue, reverse=True)