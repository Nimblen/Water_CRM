from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
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
    cooler_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        server_default="0",
    )
    custom_water_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")




class CustomerBalanceAdjustments(AbstractBase):
    __tablename__ = "customer_balance_adjustments"
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    debt_before: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    debt_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    prepayment_before: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    prepayment_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )