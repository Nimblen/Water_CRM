from decimal import Decimal
from uuid import UUID
from app.db.models.customer import Customer, CustomerBalanceAdjustments
from app.repositories.customer import CustomerRepository, CustomerBalanceAdjustmentsRepository
from app.repositories.idempotency import IdempotencyRepository
from app.schemas.customer import (
    CreateCustomer,
    UpdateCustomer,
    CustomerResponse,
    CustomerFilters,
)
from app.schemas.common import PaginationParams, PaginatedResponse, build_paginated_response
from app.core.exceptions.not_found import CustomerNotFoundError
from app.core.exceptions.conflict import BothBalancesSetError, CustomerPhoneAlreadyExistsError, CustomerAlreadyActiveError, CustomerAlreadyInactiveError
from app.services.customer_balance import CustomerBalanceService
from sqlalchemy.ext.asyncio import AsyncSession



class CustomerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CustomerRepository(session)
        self.adjustments_repo = CustomerBalanceAdjustmentsRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)
        self.balance_service = CustomerBalanceService(session)


        
    async def create_customer(self, data: CreateCustomer, current_user_id: UUID) -> CustomerResponse:
        existing = await self.repo.get_by_phone(data.phone)
        if existing:
            raise CustomerPhoneAlreadyExistsError()

        customer = Customer(
            full_name=data.full_name,
            phone=data.phone,
            address=data.address,
            comment=data.comment,
            cooler_count=data.cooler_count,
            custom_water_price=data.custom_water_price,
            debt=Decimal("0.00"),
            prepayment=Decimal("0.00"),
        )
        customer = await self.repo.create(customer)
        await self.session.flush()
        await self.session.refresh(customer)

        if data.debt > 0 or data.prepayment > 0:
            await self.balance_service.set_balance(
                customer,
                new_debt=data.debt,
                new_prepayment=data.prepayment,
                user_id=current_user_id,
                reason="initial_balance_on_create",
            )
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

    async def update_customer(
        self, customer_id: UUID, data: UpdateCustomer, current_user_id: UUID
    ) -> CustomerResponse:
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError()

        if data.phone and data.phone != customer.phone:
            existing = await self.repo.get_by_phone(data.phone)
            if existing:
                raise CustomerPhoneAlreadyExistsError()

        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("cooler_count") is None:
            update_data.pop("cooler_count", None)

        new_debt = update_data.pop("debt", None)
        new_prepayment = update_data.pop("prepayment", None)

        for field, value in update_data.items():
            setattr(customer, field, value)

        if new_debt is not None or new_prepayment is not None:
            await self.balance_service.set_balance(
                customer,
                new_debt=new_debt if new_debt is not None else customer.debt,
                new_prepayment=new_prepayment if new_prepayment is not None else customer.prepayment,
                user_id=current_user_id,
                reason="balance_adjustment_via_patch",
            )

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

