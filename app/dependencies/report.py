from typing import Annotated
from datetime import date, timedelta
from fastapi import Depends

from app.schemas.report import ReportPeriod
from app.services.report import AdminReportService
from app.dependencies.session import SessionDep


def get_report_period(
    date_from: date | None = None,
    date_to: date | None = None,
) -> ReportPeriod:
    today = date.today()
    return ReportPeriod(
        date_from=date_from or today - timedelta(days=30),
        date_to=date_to or today,
    )


def get_admin_report_service(session: SessionDep) -> AdminReportService:
    return AdminReportService(session)


ReportPeriodDep = Annotated[ReportPeriod, Depends(get_report_period)]
AdminReportServiceDep = Annotated[AdminReportService, Depends(get_admin_report_service)]