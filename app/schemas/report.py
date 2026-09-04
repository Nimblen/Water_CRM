from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel

from app.core.constants import PaymentMethod, OrderPurpose


class ReportDateFilter(BaseModel):
    date_from: date
    date_to: date
    driver_id: UUID | None = None   # доп. фильтр, не в спеке явно, но полезен


class DriverReportRow(BaseModel):
    route_id: UUID
    route_date: date
    driver_id: UUID
    driver_full_name: str
    customer_name_or_address: str
    delivered_bottles: int
    returned_bottles: int
    bottle_balance_after: int | None
    order_amount: Decimal
    payment_method: PaymentMethod | None
    purpose: OrderPurpose
    bulk_liters_sold_count: int      # bulk_5l_count + bulk_10l_count
    bulk_sale_amount: Decimal        # bulk_5l_count*price + bulk_10l_count*price
    route_expenses_total: Decimal    # ASSUMPTION: повторяется на каждой строке маршрута — см. ниже


class CustomerReportRow(BaseModel):
    customer_id: UUID
    full_name: str
    address: str
    phone: str
    bulk_liters_purchased: int
    damaged_bottles_count: int
    bottles_purchased_in_period: int
    current_bottle_balance: int
    current_cooler_count: int
    prepayment: Decimal
    debt: Decimal
    total_realization: Decimal       # сумма order_amount за период


class GeneralReportRow(BaseModel):
    date: date
    driver_full_name: str
    customer_name_or_address: str
    delivered_bottles: int
    returned_bottles: int
    order_amount: Decimal
    damaged_bottles: int
    cooler_count: int