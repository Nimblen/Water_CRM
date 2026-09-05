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

    async def create(self, water_price, deposit_price, damaged_bottle_fine) -> PriceSettings:
        # POST /admin/prices принимает подмножество полей, а установленные сборки
        # админки шлют только water_price и deposit_price. Записывать при этом
        # None в NOT NULL damaged_bottle_fine нельзя (IntegrityError), обнулять —
        # тоже: непереданное поле обязано сохранить действующее значение.
        # Поэтому берём текущий прайс и накладываем сверху только то, что пришло.
        stmt = (
            select(PriceSettings)
            .order_by(PriceSettings.created_at.desc())
            .limit(1)
        )
        # Намеренно не через get_current(): тот при пустой таблице создаёт нулевую
        # строку, и она осела бы лишней записью в /admin/prices/history.
        current = (await self.session.execute(stmt)).scalar_one_or_none()

        def inherit(new_value, field: str):
            if new_value is not None:
                return new_value
            return getattr(current, field) if current is not None else 0

        price = PriceSettings(
            water_price=inherit(water_price, "water_price"),
            deposit_price=inherit(deposit_price, "deposit_price"),
            damaged_bottle_fine=inherit(damaged_bottle_fine, "damaged_bottle_fine"),
        )
        self.session.add(price)
        await self.session.flush()
        return price