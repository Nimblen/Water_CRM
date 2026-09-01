from uuid import UUID
from app.core.constants import PaymentMethod
from fastapi import APIRouter, UploadFile, Request, Form, File, Depends
from decimal import Decimal


from app.dependencies.user import CurrentAdminDep
from app.dependencies.common import PaginationDep
from app.dependencies.order import AdminOrderFiltersDep, OrderServiceDep
from app.schemas.order import AdminPaymentUpdate, OrderResponse, MoveOrder
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/admin/orders", tags=["admin:orders"])


@router.get("", response_model=PaginatedResponse[OrderResponse])
async def get_orders(
    _: CurrentAdminDep,
    pagination: PaginationDep,
    filters: AdminOrderFiltersDep,
    service: OrderServiceDep,
):
    return await service.get_admin_orders(pagination, filters)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    _: CurrentAdminDep,
    service: OrderServiceDep,
):
    return await service.get_admin_order(order_id)




@router.post("/{order_id}/move", status_code=204)
async def move_order(order_id: UUID, payload: MoveOrder, _: CurrentAdminDep, service: OrderServiceDep):
    await service.move_order(order_id, payload)


#TODO: перенести в отдельный модуль
async def parse_payment_update(
    request: Request,
    amount: Decimal | None = Form(None),
    payment_method: PaymentMethod | None = Form(None),
    note: str | None = Form(None),
    payment_photo: UploadFile | None = File(None),
) -> tuple[AdminPaymentUpdate, UploadFile | None]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await request.json()
        return AdminPaymentUpdate(**body), None
    return (
        AdminPaymentUpdate(amount=amount, payment_method=payment_method, note=note),
        payment_photo,
    )


@router.patch("/{order_id}/payment", status_code=204)
async def update_order_payment(
    order_id: UUID,
    admin: CurrentAdminDep,
    service: OrderServiceDep,
    parsed: tuple[AdminPaymentUpdate, UploadFile | None] = Depends(parse_payment_update),
):
    payload, photo = parsed
    await service.update_order_payment(order_id, payload, photo, admin_id=admin.id)