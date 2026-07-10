from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    Index,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import AbstractBase


class Customer(AbstractBase):
    __tablename__ = "customers"

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    bottle_balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    prepayment: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )

    debt: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )

    last_order_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    __table_args__ = (
        Index("ix_customer_phone", "phone"),
        Index("ix_customer_full_name", "full_name"),
    )