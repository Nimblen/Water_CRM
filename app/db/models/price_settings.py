import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import AbstractBase


class PriceSettings(AbstractBase):
    __tablename__ = "price_settings"

    water_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    deposit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )
    damaged_bottle_fine: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
        server_default="0.00",
    )