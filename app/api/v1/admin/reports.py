from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.report import AdminReportServiceDep, ReportPeriodDep
from app.schemas.report import SummaryReport, DriverReportItem

router = APIRouter(prefix="/admin/reports", tags=["admin:reports"])


@router.get("/summary", response_model=SummaryReport)
async def get_summary_report(
    _: CurrentAdminDep,
    period: ReportPeriodDep,
    service: AdminReportServiceDep,
):
    return await service.get_summary(period)


@router.get("/drivers", response_model=list[DriverReportItem])
async def get_drivers_report(
    _: CurrentAdminDep,
    period: ReportPeriodDep,
    service: AdminReportServiceDep,
):
    return await service.get_drivers_report(period)