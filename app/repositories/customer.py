from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.customer import Customer
from app.schemas.customer import CustomerFilters
from app.schemas.common import PaginationParams


class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _apply_filters(self, stmt, filters: CustomerFilters):
        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(pattern),
                    Customer.phone.ilike(pattern),
                    Customer.address.ilike(pattern),
                )
            )
        if filters.is_active is not None:
            stmt = stmt.where(Customer.is_active == filters.is_active)
        if filters.has_debt is not None:
            stmt = stmt.where(Customer.debt > 0) if filters.has_debt else stmt.where(Customer.debt == 0)
        if filters.has_cooler is not None:
            stmt = stmt.where(Customer.has_cooler == filters.has_cooler)
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
        stmt = select(Customer).where(Customer.phone == phone)
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
