from uuid import UUID
from fastapi import APIRouter

from app.dependencies.user import CurrentAdminDep
from app.dependencies.customer import CustomerServiceDep, CustomerFiltersDep
from app.dependencies.driver import PaginationDep
from app.schemas.customer import CreateCustomer, UpdateCustomer, CustomerResponse
from app.schemas.common import PaginatedResponse
from app.dependencies.idempotency import IdempotencyKeyDep
router = APIRouter(prefix="/admin/customers", tags=["admin:customers"])


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    data: CreateCustomer,
    _: CurrentAdminDep,
    service: CustomerServiceDep,
    idempotency_key: IdempotencyKeyDep,
):
    customer = await service.create_customer(data)
    if idempotency_key:
        await service.idempotency_repo.save(idempotency_key, endpoint="/admin/customers", status_code=201, response_body=customer.model_dump(mode="json"))
    return customer

@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def get_customers(
    _: CurrentAdminDep,
    pagination: PaginationDep,
    filters: CustomerFiltersDep,
    service: CustomerServiceDep,
):
    return await service.get_customers(pagination, filters)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    _: CurrentAdminDep,
    service: CustomerServiceDep,
):
    return await service.get_customer(customer_id)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    data: UpdateCustomer,
    _: CurrentAdminDep,
    service: CustomerServiceDep,
):
    return await service.update_customer(customer_id, data)


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: UUID,
    _: CurrentAdminDep,
    service: CustomerServiceDep,
):
    await service.deactivate_customer(customer_id)