from decimal import Decimal
import uuid
from datetime import date as date_type
from sqlalchemy import ForeignKey, Date, Integer, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import AbstractBase
from app.core.constants import RouteStatus, ExpenseCategory


class Route(AbstractBase):
    __tablename__ = "routes"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    date: Mapped[date_type] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[RouteStatus] = mapped_column(
        Enum(RouteStatus, name="route_status"),
        nullable=False,
        default=RouteStatus.CREATED,
    )

    completed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    driver = relationship("Driver", back_populates="routes")

    orders = relationship(
        "Order",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="Order.created_at",
        foreign_keys="[Order.route_id]",
    )



class RouteExpenses(AbstractBase):
    __tablename__ = "route_expenses"

    route_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory, name="expense_category"),
        nullable=False,
        default=ExpenseCategory.OTHER,
        server_default="OTHER",
    )
    comment: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
