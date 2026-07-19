from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.price_settings import PriceSettings


class PriceSettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_current(self) -> PriceSettings:
        stmt = (
            select(PriceSettings)
            .order_by(PriceSettings.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        price = result.scalar_one_or_none()
        if price is None:
            # первый запуск системы — записи ещё нет
            price = PriceSettings(water_price=0, deposit_price=0)
            self.session.add(price)
            await self.session.flush()
        return price

    async def get_history(self, limit: int = 50) -> list[PriceSettings]:
        stmt = (
            select(PriceSettings)
            .order_by(PriceSettings.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, water_price, deposit_price) -> PriceSettings:
        price = PriceSettings(water_price=water_price, deposit_price=deposit_price)
        self.session.add(price)
        await self.session.flush()
        return price