from app.repositories.price_settings import PriceSettingsRepository
from app.schemas.price import PriceSettingsResponse, CreatePriceSettings


class PriceService:
    def __init__(self, repo: PriceSettingsRepository):
        self.repo = repo

    async def get_current(self) -> PriceSettingsResponse:
        price = await self.repo.get_current()
        return PriceSettingsResponse.model_validate(price)

    async def get_history(self) -> list[PriceSettingsResponse]:
        prices = await self.repo.get_history()
        return [PriceSettingsResponse.model_validate(p) for p in prices]

    async def set_price(self, data: CreatePriceSettings) -> PriceSettingsResponse:
        price = await self.repo.create(data.water_price, data.deposit_price, data.damaged_bottle_fine)
        return PriceSettingsResponse.model_validate(price)