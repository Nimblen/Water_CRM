from uuid import UUID
from datetime import date as date_type
from decimal import Decimal
from pydantic import BaseModel


class ReportPeriod(BaseModel):
    date_from: date_type
    date_to: date_type


class SummaryReport(BaseModel):
    routes_count: int
    completed_deliveries_count: int
    failed_deliveries_count: int
    total_revenue: Decimal
    total_debt: Decimal


class DriverReportItem(BaseModel):
    driver_id: UUID
    driver_full_name: str
    routes_count: int
    completed_deliveries_count: int
    total_revenue: Decimal

    model_config = {"from_attributes": True}




class ReportExportFilters(BaseModel):
    date_from: date_type
    date_to: date_type
    driver_id: UUID | None = None