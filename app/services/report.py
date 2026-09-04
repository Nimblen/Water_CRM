import io
from decimal import Decimal
import openpyxl
from fastapi.responses import StreamingResponse

from app.repositories.report import ReportRepository
from app.schemas.report import (
    ReportDateFilter, DriverReportRow, CustomerReportRow, GeneralReportRow,
)


class ReportService:
    def __init__(self, session):
        self.repo = ReportRepository(session)

    async def get_driver_report(self, filters: ReportDateFilter) -> list[DriverReportRow]:
        rows = await self.repo.get_driver_report_rows(filters)
        result = []
        for r in rows:
            order, route, driver = r["order"], r["route"], r["driver"]
            bulk_sale_amount = (
                order.bulk_5l_count * order.bulk_5l_price
                + order.bulk_10l_count * order.bulk_10l_price
            )
            result.append(DriverReportRow(
                route_id=route.id,
                route_date=route.date,
                driver_id=driver.id,
                driver_full_name=driver.full_name,
                customer_name_or_address=order.customer.full_name or order.customer.address,
                delivered_bottles=order.delivered_bottles or 0,
                returned_bottles=order.returned_bottles or 0,
                bottle_balance_after=order.bottle_balance_after,
                order_amount=order.order_amount or Decimal("0.00"),
                payment_method=order.payment_method,
                purpose=order.purpose,
                bulk_liters_sold_count=(order.bulk_5l_count or 0) + (order.bulk_10l_count or 0),
                bulk_sale_amount=bulk_sale_amount,
                route_expenses_total=r["route_expenses_total"],
            ))
        return result

    async def get_customer_report(self, filters: ReportDateFilter) -> list[CustomerReportRow]:
        rows = await self.repo.get_customer_report_rows(filters)
        return [
            CustomerReportRow(
                customer_id=r["customer"].id,
                full_name=r["customer"].full_name,
                address=r["customer"].address,
                phone=r["customer"].phone,
                bulk_liters_purchased=r["agg"].bulk_qty,
                damaged_bottles_count=r["agg"].damaged,
                bottles_purchased_in_period=r["agg"].delivered,
                current_bottle_balance=r["customer"].bottle_balance,
                current_cooler_count=r["customer"].cooler_count,
                prepayment=r["customer"].prepayment,
                debt=r["customer"].debt,
                total_realization=r["agg"].realization,
            )
            for r in rows
        ]

    async def get_general_report(self, filters: ReportDateFilter) -> list[GeneralReportRow]:
        rows = await self.repo.get_general_report_rows(filters)
        return [
            GeneralReportRow(
                date=r["route"].date,
                driver_full_name=r["driver"].full_name,
                customer_name_or_address=r["customer"].full_name or r["customer"].address,
                delivered_bottles=r["order"].delivered_bottles or 0,
                returned_bottles=r["order"].returned_bottles or 0,
                order_amount=r["order"].order_amount or Decimal("0.00"),
                damaged_bottles=r["order"].damaged_bottles or 0,
                cooler_count=r["customer"].cooler_count,
            )
            for r in rows
        ]

    def to_excel(self, rows: list, filename: str) -> StreamingResponse:
        if not rows:
            headers = []
        else:
            headers = list(rows[0].model_dump().keys())

        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.append(headers)
        for row in rows:
            sheet.append([str(v) if v is not None else "" for v in row.model_dump().values()])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )