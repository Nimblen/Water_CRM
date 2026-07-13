from sqlalchemy.ext.asyncio import AsyncSession
import math
from app.repositories.user import UserRepository
from app.repositories.driver import DriverRepository
from app.schemas.user import CreateDriver, DriverResponse, DriverFilters
from app.schemas.common import PaginationParams, PaginatedResponse
from app.core.security import hash_password
from app.core.exceptions.conflict import PhoneAlreadyExistsError
from app.core.constants import UserRole
from app.db.models.driver import Driver
from app.db.models.user import User


class DriverService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.user_repo = UserRepository(session)
        self.driver_repo = DriverRepository(session)

    async def create_driver(
        self,
        data: CreateDriver,
    ) -> DriverResponse:

        if await self.user_repo.get_by_phone(data.phone):
            raise PhoneAlreadyExistsError()

        async with self.session.begin():

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

        await self.session.refresh(driver)

        return DriverResponse(
            id=driver.id,
            user_id=user.id,
            phone=user.phone,
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

        pages = math.ceil(total / pagination.page_size)

        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )
