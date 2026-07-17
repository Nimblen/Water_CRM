from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.price_settings import PriceSettings


class PriceSettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_current(self) -> PriceSettings:
        stmt = select(PriceSettings).order_by(PriceSettings.updated_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if settings is None:
            raise RuntimeError("PriceSettings не сконфигурированы")
        return settings