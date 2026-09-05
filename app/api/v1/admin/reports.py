from fastapi import APIRouter
from app.dependencies.user import CurrentAdminDep
from app.dependencies.report import ReportServiceDep, ReportDateFilterDep
from app.schemas.report import DriverReportRow, CustomerReportRow, GeneralReportRow

router = APIRouter(prefix="/admin/reports", tags=["admin:reports"])


@router.get("/drivers", response_model=list[DriverReportRow])
async def get_driver_report(_: CurrentAdminDep, filters: ReportDateFilterDep, service: ReportServiceDep):
    return await service.get_driver_report(filters)


@router.get("/drivers/export")
async def export_driver_report(_: CurrentAdminDep, filters: ReportDateFilterDep, service: ReportServiceDep):
    rows = await service.get_driver_report(filters)
    return service.to_excel(rows, "driver_report.xlsx")


@router.get("/customers", response_model=list[CustomerReportRow])
async def get_customer_report(_: CurrentAdminDep, filters: ReportDateFilterDep, service: ReportServiceDep):
    return await service.get_customer_report(filters)


@router.get("/customers/export")
async def export_customer_report(_: CurrentAdminDep, filters: ReportDateFilterDep, service: ReportServiceDep):
    rows = await service.get_customer_report(filters)
    return service.to_excel(rows, "customer_report.xlsx")


@router.get("/general", response_model=list[GeneralReportRow])
async def get_general_report(_: CurrentAdminDep, filters: ReportDateFilterDep, service: ReportServiceDep):
    return await service.get_general_report(filters)


@router.get("/general/export")
async def export_general_report(_: CurrentAdminDep, filters: ReportDateFilterDep, service: ReportServiceDep):
    rows = await service.get_general_report(filters)
    return service.to_excel(rows, "general_report.xlsx")