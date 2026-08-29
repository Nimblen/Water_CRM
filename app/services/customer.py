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
from sqlalchemy.ext.asyncio import AsyncSession



class CustomerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CustomerRepository(session)
        self.adjustments_repo = CustomerBalanceAdjustmentsRepository(session)
        self.idempotency_repo = IdempotencyRepository(session)


        
    async def create_customer(self, data: CreateCustomer, current_user_id: UUID) -> CustomerResponse:
        existing = await self.repo.get_by_phone(data.phone)
        if existing:
            raise CustomerPhoneAlreadyExistsError()
        if data.debt > 0 and data.prepayment > 0:
            raise BothBalancesSetError()

        customer = Customer(
            full_name=data.full_name,
            phone=data.phone,
            address=data.address,
            comment=data.comment,
            cooler_count=data.cooler_count,
            custom_water_price=data.custom_water_price,
            debt=data.debt,
            prepayment=data.prepayment,
        )
        customer = await self.repo.create(customer)
        await self.session.flush()
        await self.session.refresh(customer)
        if data.debt > 0 or data.prepayment > 0:
            await self.adjustments_repo.create(
                CustomerBalanceAdjustments(
                    customer_id=customer.id,
                    user_id=current_user_id,
                    debt_before=Decimal("0"),
                    debt_after=customer.debt,
                    prepayment_before=Decimal("0"),
                    prepayment_after=customer.prepayment,
                    reason="initial_balance_on_create",
                )
            )
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
        new_debt = update_data.get("debt", customer.debt)
        new_prepayment = update_data.get("prepayment", customer.prepayment)
        if new_debt > 0 and new_prepayment > 0:
            raise BothBalancesSetError()

        balance_changed = "debt" in update_data or "prepayment" in update_data
        debt_before, prepayment_before = customer.debt, customer.prepayment

        for field, value in update_data.items():
            setattr(customer, field, value)

        await self.session.flush()
        await self.session.refresh(customer)

        if balance_changed and (
            customer.debt != debt_before or customer.prepayment != prepayment_before
        ):
            await self.adjustments_repo.create(
                CustomerBalanceAdjustments(
                    customer_id=customer.id,
                    user_id=current_user_id,
                    debt_before=debt_before,
                    debt_after=customer.debt,
                    prepayment_before=prepayment_before,
                    prepayment_after=customer.prepayment,
                    reason="balance_adjustment_via_patch",
                )
            )

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

