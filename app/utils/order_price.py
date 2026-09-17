from decimal import Decimal

from app.core.constants import OrderPurpose
from app.db.models.order import Order
from app.db.models.price_settings import PriceSettings




async def calculate_order_cost(
    order: Order,
    purpose: OrderPurpose,
    price_settings: PriceSettings,
) -> tuple[Decimal, Decimal, Decimal]:

    price = (
        order.customer.custom_water_price
        or price_settings.water_price
    )
    fine = price_settings.damaged_bottle_fine

    water_sum = (
        (
            (order.delivered_bottles or 0)
            - (order.returned_full_bottles or 0)
        ) * price
        if purpose == OrderPurpose.DELIVERY_19L
        else Decimal("0.00")
    )

    damage_sum = (order.damaged_bottles or 0) * fine

    bulk_sum = (
        (order.bulk_5l_count or 0) * (order.bulk_5l_price or 0)
        + (order.bulk_10l_count or 0) * (order.bulk_10l_price or 0)
    )

    calculated_cost = water_sum + damage_sum + bulk_sum
    order_cost = order.custom_price or calculated_cost

    return order_cost, price, fine