from uuid import UUID
from app.core.exceptions.validation import InvalidUpdateFieldsError
from sqlalchemy.ext.asyncio import AsyncSession
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



ALLOWED_DRIVER_UPDATE_FIELDS = {"full_name", "phone", "email"}


class DriverService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.driver_repo = DriverRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)

    async def create_driver(self, data: CreateDriver) -> DriverResponse:
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

        return self._to_response(driver, phone=data.phone)

    async def get_drivers(
        self, pagination: PaginationParams, filters: DriverFilters
    ) -> PaginatedResponse[DriverResponse]:
        drivers, total = await self.driver_repo.get_all(pagination, filters)
        items = [self._to_response(d, phone=d.user.phone) for d in drivers]
        return build_paginated_response(items=items, total=total, pagination=pagination)

    async def get_driver(self, driver_id: UUID) -> DriverResponse:
        driver = await self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError()
        return self._to_response(driver, phone=driver.user.phone)

    async def deactivate_driver(self, driver_id: UUID) -> None:
        driver = await self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError()
        if not driver.user.is_active:
            raise UserAlreadyInactiveError()
        driver.user.is_active = False
        await self.session.flush()

    async def update_driver(self, driver_id: UUID, update_data: UpdateDriver) -> DriverResponse:
        update_dict = update_data.model_dump(exclude_unset=True)

        disallowed = set(update_dict) - ALLOWED_DRIVER_UPDATE_FIELDS
        if disallowed:
            raise InvalidUpdateFieldsError(disallowed)

        driver = await self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError()

        if "phone" in update_dict:
            existing = await self.user_repo.get_by_phone(update_dict["phone"])
            if existing and existing.id != driver.user_id:
                raise PhoneAlreadyExistsError()
            driver.user.phone = update_dict.pop("phone")

        for key, value in update_dict.items():
            setattr(driver, key, value)

        await self.session.flush()
        await self.session.refresh(driver)
        return self._to_response(driver, phone=driver.user.phone)

    def _to_response(self, driver: Driver, phone: str) -> DriverResponse:
        return DriverResponse(
            id=driver.id,
            user_id=driver.user_id,
            phone=phone,
            email=driver.email,
            full_name=driver.full_name,
            trip_count=driver.trip_count,
            today_trip_count=driver.today_trip_count,
            created_at=driver.created_at,
            updated_at=driver.updated_at,
        )
