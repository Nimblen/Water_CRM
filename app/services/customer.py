from uuid import UUID
from app.db.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import (
    CreateCustomer,
    UpdateCustomer,
    CustomerResponse,
    CustomerFilters,
)
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.core.exceptions.not_found import CustomerNotFoundError
from app.core.exceptions.conflict import CustomerPhoneAlreadyExistsError, CustomerAlreadyActiveError, CustomerAlreadyInactiveError
from sqlalchemy.ext.asyncio import AsyncSession



class CustomerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CustomerRepository(session)

    async def create_customer(self, data: CreateCustomer) -> CustomerResponse:
        existing = await self.repo.get_by_phone(data.phone)
        if existing:
            raise CustomerPhoneAlreadyExistsError()

        customer = Customer(
            full_name=data.full_name,
            phone=data.phone,
            address=data.address,
            comment=data.comment,
        )
        customer = await self.repo.create(customer)
        await self.session.flush()
        await self.session.refresh(customer)
        return CustomerResponse.model_validate(customer)

    async def get_customer(self, customer_id: UUID) -> CustomerResponse:
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError()
        return CustomerResponse.model_validate(customer)

    async def get_customers(
        self, pagination: PaginationParams, filters: CustomerFilters
    ) -> PaginatedResponse[CustomerResponse]:
        customers, total = await self.repo.get_list(pagination, filters)
        return build_paginated_response(
            items=[CustomerResponse.model_validate(c) for c in customers],
            total=total,
            pagination=pagination,
        )

    async def update_customer(self, customer_id: UUID, data: UpdateCustomer) -> CustomerResponse:
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError()

        if data.phone and data.phone != customer.phone:
            existing = await self.repo.get_by_phone(data.phone)
            if existing:
                raise CustomerPhoneAlreadyExistsError()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        await self.session.flush()
        await self.session.refresh(customer)
        return CustomerResponse.model_validate(customer)

    async def deactivate_customer(self, customer_id: UUID) -> None:
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError()
        if not customer.is_active:
            raise CustomerAlreadyInactiveError()
        customer.is_active = False
        await self.session.flush()

    async def reactivate_customer(self, customer_id: UUID) -> None:
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError()
        if customer.is_active:
            raise CustomerAlreadyActiveError()
        customer.is_active = True
        await self.session.flush()
