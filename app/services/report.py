from decimal import Decimal

from app.repositories.report import ReportRepository
from app.schemas.report import (
    ReportDateFilter, DriverReportRow, CustomerReportRow, GeneralReportRow,
)
from app.services.export import ExcelColumn, ColumnType, build_excel_response, ORDER_PURPOSE_LABELS, PAYMENT_METHOD_LABELS, EXPENSE_CATEGORY_LABELS


DRIVER_REPORT_COLUMNS = [
    ExcelColumn("route_date", "Дата маршрута", ColumnType.DATE),
    ExcelColumn("driver_full_name", "Водитель", ColumnType.TEXT, width=22),
    ExcelColumn("customer_name_or_address", "Заказчик", ColumnType.TEXT, width=28),
    ExcelColumn("delivered_bottles", "Доставлено бутылей (19л)", ColumnType.INT, totals=True),
    ExcelColumn("returned_bottles", "Возвращено бутылей", ColumnType.INT, totals=True),
    ExcelColumn("bottle_balance_after", "Баланс бутылей у клиента", ColumnType.INT, totals=True),
    ExcelColumn("order_amount", "Сумма заказа", ColumnType.CURRENCY, totals=True),
    ExcelColumn("payment_method", "Способ оплаты", ColumnType.ENUM, labels=PAYMENT_METHOD_LABELS),
    ExcelColumn("purpose", "Цель заказа", ColumnType.ENUM, labels=ORDER_PURPOSE_LABELS),
    ExcelColumn("bulk_liters_sold_count", "Продано бутылей (опт)", ColumnType.INT, totals=True),
    ExcelColumn("bulk_sale_amount", "Сумма опт. продаж", ColumnType.CURRENCY, totals=True),
    ExcelColumn("route_expenses_total", "Расходы по маршруту", ColumnType.CURRENCY, totals=True),
]


CUSTOMER_REPORT_COLUMNS = [
    ExcelColumn("full_name", "Заказчик", ColumnType.TEXT, width=26),
    ExcelColumn("address", "Адрес", ColumnType.TEXT, width=32),
    ExcelColumn("phone", "Телефон", ColumnType.TEXT, width=16),
    ExcelColumn("bulk_liters_purchased", "Куплено бутылей (опт)", ColumnType.INT, totals=True),
    ExcelColumn("bottles_purchased_in_period", "Куплено бутылей за период", ColumnType.INT, totals=True),
    ExcelColumn("damaged_bottles_count", "Повреждено бутылей", ColumnType.INT, totals=True),
    ExcelColumn("current_bottle_balance", "Текущий баланс бутылей", ColumnType.INT, totals=True),
    ExcelColumn("current_cooler_count", "Кулеров у заказчика", ColumnType.INT, totals=True),
    ExcelColumn("prepayment", "Предоплата", ColumnType.CURRENCY, totals=True),
    ExcelColumn("debt", "Долг", ColumnType.CURRENCY, totals=True),
    ExcelColumn("total_realization", "Сумма реализации", ColumnType.CURRENCY, totals=True),
]

GENERAL_REPORT_COLUMNS = [
    ExcelColumn("date", "Дата", ColumnType.DATE),
    ExcelColumn("driver_full_name", "Водитель", ColumnType.TEXT, width=22),
    ExcelColumn("customer_name_or_address", "Заказчик", ColumnType.TEXT, width=28),
    ExcelColumn("delivered_bottles", "Доставлено бутылей", ColumnType.INT, totals=True),
    ExcelColumn("order_amount", "Сумма заказа", ColumnType.CURRENCY, totals=True),
    ExcelColumn("returned_bottles", "Возвращено бутылей", ColumnType.INT, totals=True),
    ExcelColumn("damaged_bottles", "Повреждено бутылей", ColumnType.INT, totals=True),
    ExcelColumn("cooler_count", "Кулеров у заказчика", ColumnType.INT, totals=True),
    ExcelColumn("bottle_balance", "Баланс бутылей у клиента", ColumnType.INT, totals=True),
]

_REPORT_SPECS = {
    DriverReportRow: (DRIVER_REPORT_COLUMNS, "Отчёт по водителям"),
    CustomerReportRow: (CUSTOMER_REPORT_COLUMNS, "Отчёт по клиентам"),
    GeneralReportRow: (GENERAL_REPORT_COLUMNS, "Общий отчёт"),
}


class ReportService:
    def __init__(self, session):
        self.repo = ReportRepository(session)

    async def get_driver_report(self, filters: ReportDateFilter) -> list[DriverReportRow]:
        rows = await self.repo.get_driver_report_rows(filters)
        result = []
        for r in rows:
            order, route, driver = r["order"], r["route"], r["driver"]
            customer = r["customer"]
            bulk_sale_amount = (
                (order.bulk_5l_count or 0) * (order.bulk_5l_price or Decimal("0.00"))
                + (order.bulk_10l_count or 0) * (order.bulk_10l_price or Decimal("0.00"))
            )
            result.append(DriverReportRow(
                route_id=route.id,
                route_date=route.date,
                driver_id=driver.id,
                driver_full_name=driver.full_name,
                customer_name_or_address=customer.full_name or customer.address,
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
                bottle_balance=r["customer"].bottle_balance,
            )
            for r in rows
        ]

    def to_excel(self, rows: list, filename: str, report_type: type | None = None) -> "StreamingResponse":
        row_type = report_type or (type(rows[0]) if rows else None)
        spec = _REPORT_SPECS.get(row_type)
        if spec is None:
            raise ValueError(
                "Не удалось определить колонки для Excel: список пуст и "
                "report_type не передан, либо это неизвестный тип отчёта."
            )
        columns, sheet_title = spec
        return build_excel_response(rows, columns, filename, sheet_title)