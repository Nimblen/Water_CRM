import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, Numeric, Enum, DateTime, BigInteger, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import AbstractBase
from app.core.constants import DeliveryStatus, PaymentMethod, OrderPurpose


class Order(AbstractBase):
    __tablename__ = "orders"
    number: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        nullable=False,
        unique=True,
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        nullable=False,
        default=DeliveryStatus.PENDING,
    )

    delivered_bottles: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    returned_bottles: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="0",
    )
    damaged_bottles: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="0",
    )
    bottle_balance_after: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    bulk_5l_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="0",
    )
    bulk_5l_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        default=0,
        server_default="0.00",
    )
    bulk_10l_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="0",
    )
    bulk_10l_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        default=0,
        server_default="0.00",
    )
    picked_coolers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="0",
    )
    picked_bottles: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="0",
    )
    water_price_applied: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        default=0,
        server_default="0.00",
    )
    damaged_fine_applied: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        default=0,
        server_default="0.00",
    )
    order_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        default=0,
        server_default="0.00",
    )
    payment_method: Mapped["PaymentMethod | None"] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=True,
    )
    purpose: Mapped["OrderPurpose | None"] = mapped_column(
        Enum(OrderPurpose, name="order_purpose"),
        nullable=True,
        default=OrderPurpose.DELIVERY_19L,
        server_default="DELIVERY_19L",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
    )
    moved_from_route_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    moved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    route = relationship("Route", back_populates="orders", foreign_keys=[route_id],)
    customer = relationship("Customer", back_populates="orders")
    payment = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
    )
