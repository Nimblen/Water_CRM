from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.price import PriceServiceDep
from app.schemas.price import PriceSettingsResponse, CreatePriceSettings
from app.dependencies.idempotency import IdempotencyKeyDep
router = APIRouter(prefix="/admin/prices", tags=["admin:prices"])


@router.get("/current", response_model=PriceSettingsResponse)
async def get_current_price(
    _: CurrentAdminDep,
    service: PriceServiceDep,
):
    return await service.get_current()


@router.get("/history", response_model=list[PriceSettingsResponse])
async def get_price_history(
    _: CurrentAdminDep,
    service: PriceServiceDep,
):
    return await service.get_history()


@router.post("", response_model=PriceSettingsResponse, status_code=201)
async def set_price(
    data: CreatePriceSettings,
    _: CurrentAdminDep,
    service: PriceServiceDep,
    idempotency_key: IdempotencyKeyDep,
):
    price = await service.set_price(data)
    if idempotency_key:
        await service.idempotency_repo.save(idempotency_key, endpoint="/admin/prices", status_code=201, response_body=price.model_dump(mode="json"))
    return price