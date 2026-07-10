import uuid
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import AbstractBase


class Driver(AbstractBase):
    __tablename__ = "drivers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    trip_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    today_trip_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="driver",
        uselist=False,
    )


