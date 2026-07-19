from typing import Annotated
from fastapi import Depends

from app.services.price import PriceService
from app.repositories.price_settings import PriceSettingsRepository
from app.dependencies.session import SessionDep

def get_price_service(session: SessionDep) -> PriceService:
    return PriceService(PriceSettingsRepository(session))


PriceServiceDep = Annotated[PriceService, Depends(get_price_service)]