import uuid
from datetime import date as date_type
from sqlalchemy import ForeignKey, Date, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import AbstractBase
from app.core.constants import RouteStatus


class Route(AbstractBase):
    __tablename__ = "routes"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        nullable=False,
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

    route_customers = relationship(
        "RouteCustomer",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteCustomer.created_at",
    )