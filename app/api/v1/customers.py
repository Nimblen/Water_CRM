from uuid import UUID
from fastapi import APIRouter

from app.dependencies.user import CurrentUserDep
from app.dependencies.customer import CustomerServiceDep, CustomerFiltersForDriverDep
from app.dependencies.common import PaginationDep
from app.schemas.customer import CustomerResponseForDriver
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/driver/customers", tags=["driver:customers"])



@router.get("", response_model=PaginatedResponse[CustomerResponseForDriver])
async def get_customers(
    _: CurrentUserDep,
    pagination: PaginationDep,
    filters: CustomerFiltersForDriverDep,
    service: CustomerServiceDep,
):
    return await service.get_customers_for_driver(pagination, filters)

