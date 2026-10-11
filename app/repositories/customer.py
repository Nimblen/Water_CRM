from decimal import Decimal
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from app.db.models.customer import Customer, CustomerBalanceAdjustments
from app.schemas.customer import CustomerFilters, CustomerFiltersForDriver
from app.schemas.common import PaginationParams


class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _apply_search_filter(self, stmt, search: str | None):
        if search:
            pattern = f"%{search}%"

            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(pattern),
                    Customer.phone.ilike(pattern),
                    Customer.phone_secondary.ilike(pattern),
                    Customer.address.ilike(pattern),
                )
            )
        return stmt
    
    def _apply_filters(
        self,
        stmt,
        filters: CustomerFilters,
        ):
        stmt = self._apply_search_filter(
            stmt,
            filters.search,
        )

        if filters.is_active is not None:
            stmt = stmt.where(
                Customer.is_active == filters.is_active
            )

        if filters.has_debt is not None:
            if filters.has_debt:
                stmt = stmt.where(Customer.debt > 0)
            else:
                stmt = stmt.where(Customer.debt == 0)

        return stmt

    async def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        await self.session.flush()
        return customer

    async def get_by_id(self, customer_id: UUID) -> Customer | None:
        stmt = select(Customer).where(Customer.id == customer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Customer | None:
        stmt = select(Customer).where(
            or_(
                Customer.phone == phone,
                Customer.phone_secondary == phone,
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self, pagination: PaginationParams, filters: CustomerFilters
    ) -> tuple[list[Customer], int]:
        base_stmt = self._apply_filters(select(Customer), filters)

        count_stmt = self._apply_filters(select(func.count(Customer.id)), filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            base_stmt
            .order_by(Customer.created_at.desc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def delete(self, customer: Customer) -> None:
        await self.session.delete(customer)

    async def get_list_for_driver(
        self,
        pagination: PaginationParams,
        filters: CustomerFiltersForDriver,
    ) -> tuple[list[Customer], int]:

        base_stmt = self._apply_search_filter(
            select(Customer).options(
                load_only(
                    Customer.id,
                    Customer.full_name,
                    Customer.phone,
                    Customer.phone_secondary,
                    Customer.address,
                    Customer.comment,
                )
            ),
            filters.search,
        ).where(
            Customer.is_active.is_(True)
        )

        count_stmt = self._apply_search_filter(
            select(func.count(Customer.id)),
            filters.search,
        ).where(
            Customer.is_active.is_(True)
        )

        total = (
            await self.session.execute(count_stmt)
        ).scalar_one()

        stmt = (
            base_stmt
            .order_by(Customer.created_at.desc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )

        result = await self.session.execute(stmt)

        return result.scalars().all(), total



class CustomerBalanceAdjustmentsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self,
            *,
            customer_id: UUID,
            user_id: UUID,
            debt_before: Decimal,
            debt_after: Decimal,
            prepayment_before: Decimal,
            prepayment_after: Decimal,
            reason: str | None,
        ) -> CustomerBalanceAdjustments:

            adjustment = CustomerBalanceAdjustments(
                customer_id=customer_id,
                user_id=user_id,
                debt_before=debt_before,
                debt_after=debt_after,
                prepayment_before=prepayment_before,
                prepayment_after=prepayment_after,
                reason=reason,
            )

            self.session.add(adjustment)
            return adjustment