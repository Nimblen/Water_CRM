import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, Numeric, String, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import AbstractBase
from app.core.constants import DeliveryStatus, PaymentMethod


class RouteCustomer(AbstractBase):
    __tablename__ = "route_customers"

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
    payment_method: Mapped["PaymentMethod | None"] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    order: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
    )
    route = relationship("Route", back_populates="route_customers")
    customer = relationship("Customer", back_populates="route_customers")
    payment = relationship(
        "Payment",
        back_populates="route_customer",
        uselist=False,
    )