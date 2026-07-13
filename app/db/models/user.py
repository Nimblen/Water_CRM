
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum
from app.db.base import AbstractBase
from app.core.constants import UserRole


class User(AbstractBase):
    __tablename__ = "users"
    phone: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.DRIVER)
    driver = relationship(
        "Driver",
        back_populates="user",
        uselist=False,
    )