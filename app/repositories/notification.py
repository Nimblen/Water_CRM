from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import AdminNotification


class NotificationRepository:
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