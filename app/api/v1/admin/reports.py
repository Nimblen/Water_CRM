from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Query
from uuid import UUID
from starlette.responses import StreamingResponse
from datetime import date as date_type
from app.dependencies.user import CurrentAdminDep
from app.dependencies.report import AdminReportServiceDep, ReportPeriodDep
from app.schemas.report import SummaryReport, DriverReportItem, ReportExportFilters

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



@router.get("/export", status_code=200)
async def export_summary_report(
    admin: CurrentAdminDep,
    service: AdminReportServiceDep,
    date_from: date_type = Query(...),
    date_to: date_type = Query(...),
    driver_id: UUID | None = Query(default=None),
):
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть позже date_to")

    filters = ReportExportFilters(date_from=date_from, date_to=date_to, driver_id=driver_id)
    buffer = await service.export_deliveries(filters)

    suffix = f"_{driver_id}" if driver_id else ""
    filename = f"report_{date_from}_{date_to}{suffix}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"
        },
    )