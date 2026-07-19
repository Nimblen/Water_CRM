from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import math
from app.repositories.user import UserRepository
from app.repositories.driver import DriverRepository
from app.schemas.user import CreateDriver, DriverResponse, DriverFilters, UpdateDriver
from app.schemas.common import (
    PaginationParams,
    PaginatedResponse,
    build_paginated_response,
)
from app.core.security import hash_password
from app.core.exceptions.conflict import (
    PhoneAlreadyExistsError,
    UserAlreadyInactiveError,
)
from app.core.exceptions.not_found import DriverNotFoundError
from app.core.constants import UserRole
from app.db.models.driver import Driver
from app.db.models.user import User
from app.repositories.idempotency import IdempotencyRepository


class DriverService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.user_repo = UserRepository(session)
        self.driver_repo = DriverRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)

    async def create_driver(
        self,
        data: CreateDriver,
    ) -> DriverResponse:

        if await self.user_repo.get_by_phone(data.phone):
            raise PhoneAlreadyExistsError()

        user = User(
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role=UserRole.DRIVER,
        )

        await self.user_repo.create(user)

        await self.session.flush()

        driver = Driver(
            user_id=user.id,
            full_name=data.full_name,
            email=data.email,
        )

        await self.driver_repo.create(driver)

        await self.session.flush()

        await self.session.refresh(driver)

        return DriverResponse(
            id=driver.id,
            user_id=user.id,
            phone=data.phone,
            email=driver.email,
            full_name=driver.full_name,
            trip_count=driver.trip_count,
            today_trip_count=driver.today_trip_count,
            created_at=driver.created_at,
            updated_at=driver.updated_at,
        )

    async def get_drivers(
        self,
        pagination: PaginationParams,
        filters: DriverFilters,
    ) -> PaginatedResponse[DriverResponse]:
        drivers, total = await self.driver_repo.get_all(
            pagination,
            filters,
        )

        items = [
            DriverResponse(
                id=driver.id,
                user_id=driver.user_id,
                phone=driver.user.phone,
                email=driver.email,
                full_name=driver.full_name,
                trip_count=driver.trip_count,
                today_trip_count=driver.today_trip_count,
                created_at=driver.created_at,
                updated_at=driver.updated_at,
            )
            for driver in drivers
        ]

        return build_paginated_response(
            items=items,
            total=total,
            pagination=pagination,
        )

    async def get_driver(self, driver_id: UUID) -> DriverResponse:
        driver = await self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError()
        return DriverResponse(
            id=driver.id,
            user_id=driver.user_id,
            phone=driver.user.phone,
            email=driver.email,
            full_name=driver.full_name,
            trip_count=driver.trip_count,
            today_trip_count=driver.today_trip_count,
            created_at=driver.created_at,
            updated_at=driver.updated_at,
        )

    async def deactivate_driver(self, driver_id: UUID) -> None:
        driver = await self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError()
        if not driver.user.is_active:
            raise UserAlreadyInactiveError()
        driver.user.is_active = False

    async def update_driver(self, update_data: UpdateDriver):
        update_dict = update_data.model_dump(exclude_unset=True, exclude={"id"})
        driver = await self.driver_repo.get_by_id(update_data.id)
        if not driver:
            raise DriverNotFoundError()
        if update_data.phone:
            existing = await self.user_repo.get_by_phone(update_data.phone)
            if existing and existing.id != driver.user_id:
                raise PhoneAlreadyExistsError()
        for key, value in update_dict.items():
            if hasattr(driver, key):
                setattr(driver, key, value)
            if driver.user and hasattr(driver.user, key):
                setattr(driver.user, key, value)
        await self.session.flush()
        await self.session.refresh(driver)
        return DriverResponse(
            id=driver.id,
            user_id=driver.user_id,
            phone=driver.user.phone,
            email=driver.email,
            full_name=driver.full_name,
            trip_count=driver.trip_count,
            today_trip_count=driver.today_trip_count,
            created_at=driver.created_at,
            updated_at=driver.updated_at,
        )
