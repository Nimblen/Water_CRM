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

    order_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        unique=False,
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
    note: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    # ДОЛГ: на боевой базе колонка осталась nullable. Миграция 6dd708b2e4f4
    # ставит NOT NULL только на пустой таблице payments — для исторических
    # платежей неизвестно, кто их провёл. Новые строки поле заполняют всегда
    # (см. DriverRouteService.complete_delivery), но до ручного бэкафилла и
    # отдельной ревизии с SET NOT NULL модель и боевая схема расходятся.
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer = relationship("Customer", back_populates="payments")
    order = relationship(
        "Order",
        back_populates="payment",
        uselist=False,
    )