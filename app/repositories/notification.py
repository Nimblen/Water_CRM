import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import AdminNotification, DriverNotification


class AdminNotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, event_type: str, payload: dict) -> AdminNotification:
        row = AdminNotification(event_type=event_type, payload=payload)
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_since(self, last_id: int, limit: int = 500) -> list[AdminNotification]:
        rows = await self.session.scalars(
            select(AdminNotification)
            .where(AdminNotification.id > last_id)
            .order_by(AdminNotification.id.asc())
            .limit(limit)
        )
        return list(rows)
    

class DriverNotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, driver_id: uuid.UUID, event_type: str, payload: dict) -> DriverNotification:
        row = DriverNotification(driver_id=driver_id, event_type=event_type, payload=payload)
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_since(
        self, driver_id: uuid.UUID, last_id: int, limit: int = 200
    ) -> list[DriverNotification]:
        rows = await self.session.scalars(
            select(DriverNotification)
            .where(
                DriverNotification.driver_id == driver_id,
                DriverNotification.id > last_id,
            )
            .order_by(DriverNotification.id.asc())
            .limit(limit)
        )
        return list(rows)