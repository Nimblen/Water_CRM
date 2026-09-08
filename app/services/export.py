import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from fastapi.responses import StreamingResponse
from app.core.constants import PaymentMethod, OrderPurpose, ExpenseCategory

PAYMENT_METHOD_LABELS: dict[PaymentMethod, str] = {
    PaymentMethod.CASH: "Наличные",
    PaymentMethod.CARD: "Карта",
    PaymentMethod.TRANSFER: "Перевод",
    PaymentMethod.DEBT: "В долг",
}

ORDER_PURPOSE_LABELS: dict[OrderPurpose, str] = {
    OrderPurpose.DELIVERY_19L: "Доставка 19л",
    OrderPurpose.PICKUP: "Самовывоз / возврат тары",
    OrderPurpose.BULK_WATER: "Опт (5л/10л)",
}

EXPENSE_CATEGORY_LABELS: dict[ExpenseCategory, str] = {
    ExpenseCategory.FUEL: "Топливо",
    ExpenseCategory.LUNCH: "Обед",
    ExpenseCategory.REPAIR: "Ремонт",
    ExpenseCategory.OTHER: "Прочее",
}





HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=True)

TOTAL_FILL = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
TOTAL_FONT = Font(bold=True)

THIN_SIDE = Side(style="thin", color="B7B7B7")
CELL_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)

ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center")

CURRENCY_FORMAT = "#,##0.00 сум"
DATE_FORMAT = "DD.MM.YYYY"
INT_FORMAT = "#,##0"


class ColumnType(str, Enum):
    TEXT = "text"
    INT = "int"
    CURRENCY = "currency"
    DATE = "date"
    ENUM = "enum"


@dataclass
class ExcelColumn:
    field: str                              # имя поля в pydantic-модели строки
    header: str                             # заголовок колонки на русском
    type: ColumnType = ColumnType.TEXT
    labels: dict[Any, str] | None = None    # переводы значений — только для ColumnType.ENUM
    width: int | None = None                # если не задано — считается автоматически
    totals: bool = False                    # включать колонку в строку "ИТОГО"


def _enum_label(value: Any, labels: dict[Any, str] | None) -> str:
    if value is None:
        return "—"
    raw = value.value if isinstance(value, Enum) else value
    if labels and raw in labels:
        return labels[raw]
    # запасной вариант, если для значения ещё не завели перевод:
    # "BULK_5L" -> "Bulk 5l", чтобы в файле не было пусто
    return str(raw).replace("_", " ").capitalize()


def _cell_alignment(col_type: ColumnType) -> Alignment:
    if col_type == ColumnType.DATE:
        return ALIGN_CENTER
    if col_type in (ColumnType.INT, ColumnType.CURRENCY):
        return ALIGN_RIGHT
    return ALIGN_LEFT


def _write_value(sheet: Worksheet, r: int, c: int, column: ExcelColumn, value: Any) -> None:
    cell = sheet.cell(row=r, column=c)
    cell.border = CELL_BORDER
    cell.alignment = _cell_alignment(column.type)

    if column.type == ColumnType.CURRENCY:
        cell.value = float(value) if value is not None else 0
        cell.number_format = CURRENCY_FORMAT
    elif column.type == ColumnType.INT:
        cell.value = int(value) if value is not None else 0
        cell.number_format = INT_FORMAT
    elif column.type == ColumnType.DATE:
        cell.value = value if isinstance(value, (date, datetime)) else "—"
        if isinstance(value, (date, datetime)):
            cell.number_format = DATE_FORMAT
    elif column.type == ColumnType.ENUM:
        cell.value = _enum_label(value, column.labels)
    else:
        cell.value = "" if value is None else str(value)


def _autosize_columns(sheet: Worksheet, columns: list[ExcelColumn]) -> None:
    for idx, column in enumerate(columns, start=1):
        letter = get_column_letter(idx)
        if column.width:
            sheet.column_dimensions[letter].width = column.width
            continue
        max_len = len(column.header)
        for cell in sheet[letter][1:]:
            text = str(cell.value) if cell.value is not None else ""
            max_len = max(max_len, len(text))
        sheet.column_dimensions[letter].width = min(max(max_len + 4, 12), 45)


def build_excel_response(
    rows: list,
    columns: list[ExcelColumn],
    filename: str,
    sheet_title: str = "Отчёт",
    show_totals: bool = True,
) -> StreamingResponse:
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = sheet_title[:31]

    # Шапка
    sheet.append([c.header for c in columns])
    for col_idx in range(1, len(columns) + 1):
        cell = sheet.cell(row=1, column=col_idx)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGNMENT
        cell.border = CELL_BORDER
    sheet.freeze_panes = "A2"
    sheet.row_dimensions[1].height = 28

    # Данные
    row_idx = 1
    dumped_rows = [row.model_dump() for row in rows]
    for data in dumped_rows:
        row_idx += 1
        for col_idx, column in enumerate(columns, start=1):
            _write_value(sheet, row_idx, col_idx, column, data.get(column.field))

    if rows:
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{row_idx}"

    # Строка "ИТОГО" — по колонкам с totals=True
    if show_totals and rows and any(c.totals for c in columns):
        row_idx += 1
        for col_idx, column in enumerate(columns, start=1):
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.fill = TOTAL_FILL
            cell.font = TOTAL_FONT
            cell.border = CELL_BORDER
            if col_idx == 1:
                cell.value = "ИТОГО"
                cell.alignment = ALIGN_LEFT
            elif column.totals:
                total = sum((data.get(column.field) or 0) for data in dumped_rows)
                cell.value = float(total) if column.type == ColumnType.CURRENCY else int(total)
                cell.number_format = (
                    CURRENCY_FORMAT if column.type == ColumnType.CURRENCY else INT_FORMAT
                )
                cell.alignment = ALIGN_RIGHT

    if not rows:
        sheet.cell(row=2, column=1, value="Нет данных за выбранный период")

    _autosize_columns(sheet, columns)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )