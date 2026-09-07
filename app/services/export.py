from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


# =========================
# Styles
# =========================

HEADER_FILL = PatternFill(
    start_color="1F4E78",
    end_color="1F4E78",
    fill_type="solid",
)

HEADER_FONT = Font(
    name="Arial",
    size=11,
    bold=True,
    color="FFFFFF",
)

BODY_FONT = Font(
    name="Arial",
    size=10,
)

TOTAL_FONT = Font(
    name="Arial",
    size=10,
    bold=True,
)

THIN_BORDER = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)

DRIVER_COLUMNS = [
    ("Дата", "route_date", 14),
    ("Водитель", "driver_full_name", 25),
    ("Клиент / адрес", "customer_name_or_address", 35),
    ("Выдано бутылей", "delivered_bottles", 18),
    ("Возвращено бутылей", "returned_bottles", 20),
    ("Баланс бутылей", "bottle_balance_after", 18),
    ("Сумма заказа", "order_amount", 18),
    ("Способ оплаты", "payment_method", 18),
    ("Назначение", "purpose", 20),
    ("Наливные литры", "bulk_liters_sold_count", 18),
    ("Сумма наливной продажи", "bulk_sale_amount", 24),
    ("Расходы маршрута", "route_expenses_total", 20),
]


CUSTOMER_COLUMNS = [
    ("ФИО", "full_name", 30),
    ("Адрес", "address", 40),
    ("Телефон", "phone", 20),
    ("Куплено наливных литров", "bulk_liters_purchased", 25),
    ("Повреждено бутылей", "damaged_bottles_count", 22),
    ("Куплено бутылей за период", "bottles_purchased_in_period", 25),
    ("Текущий баланс бутылей", "current_bottle_balance", 24),
    ("Кулеры", "current_cooler_count", 15),
    ("Предоплата", "prepayment", 18),
    ("Долг", "debt", 18),
    ("Общая реализация", "total_realization", 20),
]


GENERAL_COLUMNS = [
    ("Дата", "date", 14),
    ("Водитель", "driver_full_name", 25),
    ("Клиент / адрес", "customer_name_or_address", 35),
    ("Выдано бутылей", "delivered_bottles", 18),
    ("Возвращено бутылей", "returned_bottles", 20),
    ("Сумма заказа", "order_amount", 18),
    ("Повреждено бутылей", "damaged_bottles", 22),
    ("Кулеры", "cooler_count", 15),
]


# =========================
# Helpers
# =========================

DECIMAL_FIELDS = {
    "order_amount",
    "bulk_sale_amount",
    "prepayment",
    "debt",
    "total_realization",
    "route_expenses_total",
}

INTEGER_FIELDS = {
    "delivered_bottles",
    "returned_bottles",
    "bottle_balance_after",
    "bulk_liters_sold_count",
    "bulk_liters_purchased",
    "damaged_bottles_count",
    "bottles_purchased_in_period",
    "current_bottle_balance",
    "current_cooler_count",
    "damaged_bottles",
    "cooler_count",
}

DATE_FIELDS = {
    "route_date",
    "date",
}


def _set_cell_value(
    cell,
    field: str,
    value,
) -> None:
    """
    Записывает значение в Excel с правильным типом
    и форматированием.
    """

    if value is None:
        cell.value = ""

    elif isinstance(value, Decimal):
        cell.value = float(value)

    else:
        cell.value = value

    if field in DECIMAL_FIELDS:
        cell.number_format = "#,##0.00"

    elif field in INTEGER_FIELDS:
        cell.number_format = "#,##0"

    elif field in DATE_FIELDS:
        cell.number_format = "DD.MM.YYYY"


def _style_header(ws, columns) -> None:
    for col_idx, (title, _, width) in enumerate(
        columns,
        start=1,
    ):
        cell = ws.cell(
            row=1,
            column=col_idx,
            value=title,
        )

        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

        ws.column_dimensions[
            get_column_letter(col_idx)
        ].width = width

    ws.row_dimensions[1].height = 32


def _style_body_row(
    ws,
    row_idx: int,
    column_count: int,
) -> None:
    for col_idx in range(1, column_count + 1):
        cell = ws.cell(
            row=row_idx,
            column=col_idx,
        )

        cell.font = BODY_FONT
        cell.border = THIN_BORDER

        cell.alignment = Alignment(
            vertical="center",
            wrap_text=True,
        )

    ws.row_dimensions[row_idx].height = 20


def _add_total_row(
    ws,
    rows: list,
    columns,
) -> None:
    """
    Добавляет строку Итого.

    Суммируются только числовые поля,
    для которых это имеет смысл.
    """

    total_row = len(rows) + 2

    for col_idx, (_, field, _) in enumerate(
        columns,
        start=1,
    ):
        cell = ws.cell(
            row=total_row,
            column=col_idx,
        )

        cell.font = TOTAL_FONT
        cell.border = THIN_BORDER

        if col_idx == 1:
            cell.value = "Итого"
            continue

        if field in INTEGER_FIELDS or field in DECIMAL_FIELDS:
            column_letter = get_column_letter(col_idx)

            cell.value = (
                f"=SUM("
                f"{column_letter}2:"
                f"{column_letter}{total_row - 1}"
                f")"
            )

            if field in DECIMAL_FIELDS:
                cell.number_format = "#,##0.00"
            else:
                cell.number_format = "#,##0"

    ws.row_dimensions[total_row].height = 22


# =========================
# Main builder
# =========================

def build_report_excel(
    rows: list,
    columns: list[tuple[str, str, int]],
    sheet_title: str = "Отчет",
) -> BytesIO:
    """
    Универсальная генерация Excel.

    rows:
        список Pydantic-моделей.

    columns:
        список колонок:
        ("Название", "поле", ширина)

    sheet_title:
        название листа Excel.
    """

    wb = Workbook()

    ws = wb.active
    ws.title = sheet_title[:31]

    # Заголовки
    _style_header(
        ws=ws,
        columns=columns,
    )

    # Закрепляем заголовок
    ws.freeze_panes = "A2"

    # Фильтр
    if columns:
        last_column = get_column_letter(len(columns))

        ws.auto_filter.ref = (
            f"A1:{last_column}{max(len(rows) + 1, 1)}"
        )

    # Данные
    for row_idx, row in enumerate(rows, start=2):
        data = row.model_dump()

        for col_idx, (_, field, _) in enumerate(
            columns,
            start=1,
        ):
            value = data.get(field)

            cell = ws.cell(
                row=row_idx,
                column=col_idx,
            )

            _set_cell_value(
                cell=cell,
                field=field,
                value=value,
            )

        _style_body_row(
            ws=ws,
            row_idx=row_idx,
            column_count=len(columns),
        )

    # Итого
    if rows:
        _add_total_row(
            ws=ws,
            rows=rows,
            columns=columns,
        )

    # Сохраняем в память
    buffer = BytesIO()

    wb.save(buffer)

    buffer.seek(0)

    return buffer