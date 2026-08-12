from sqlalchemy import Enum as SQLEnum
import uuid
from app.core.constants import PaymentMethod
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from app.db.base import AbstractBase


class Payment(AbstractBase):
    __tablename__ = "payments"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    route_customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("route_customers.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    payment_method: Mapped["PaymentMethod"] = mapped_column(
        SQLEnum(PaymentMethod, name="payment_method"),
        nullable=False,
    )
    customer = relationship("Customer", back_populates="payments")
    route_customer = relationship(
        "RouteCustomer",
        back_populates="payment",
        uselist=False,
    )