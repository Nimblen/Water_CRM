from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID
from app.db.models.payment import Payment
from sqlalchemy import select, func, or_
from sqlalchemy.orm import contains_eager, joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.db.models.route import Route
from app.db.models.customer import Customer
from app.schemas.common import PaginationParams
from app.core.constants import DeliveryStatus, OrderPurpose, PaymentMethod


@dataclass(frozen=True)
class OrderListFilters:
    date_from: date | None = None
    date_to: date | None = None
    customer_id: UUID | None = None
    driver_id: UUID | None = None
    route_id: UUID | None = None
    status: DeliveryStatus | None = None
    purpose: OrderPurpose | None = None
    payment_method: PaymentMethod | None = None
    search: str | None = None





class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    def _base_stmt(
        self,
        filters: OrderListFilters,
    ):
        stmt = (
            select(Order)
            .join(Order.route)
            .join(Order.customer)
            .options(
                joinedload(Order.route)
                    .joinedload(Route.driver),

                joinedload(Order.customer),

                selectinload(Order.payments),
            )
        )

        if filters.date_from:
            stmt = stmt.where(
                Route.date >= filters.date_from
            )

        if filters.date_to:
            stmt = stmt.where(
                Route.date <= filters.date_to
            )

        if filters.customer_id:
            stmt = stmt.where(
                Order.customer_id == filters.customer_id
            )

        if filters.driver_id:
            stmt = stmt.where(
                Route.driver_id == filters.driver_id
            )

        if filters.route_id:
            stmt = stmt.where(
                Order.route_id == filters.route_id
            )

        if filters.status:
            stmt = stmt.where(
                Order.status == filters.status
            )

        if filters.purpose:
            stmt = stmt.where(
                Order.purpose == filters.purpose
            )

        if filters.payment_method:
            stmt = stmt.where(
                Order.payment_method == filters.payment_method
            )

        if filters.search:
            search = f"%{filters.search}%"

            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(search),
                    Customer.phone.ilike(search),
                    Customer.address.ilike(search),
                )
            )

        return stmt
    async def get_list(
        self,
        pagination: PaginationParams,
        filters: OrderListFilters,
    ) -> tuple[list[Order], int]:
        stmt = self._base_stmt(filters)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(Route.date.desc(), Order.sequence.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        result = await self.session.execute(stmt)
        orders = result.unique().scalars().all()
        return orders, total

    async def get_by_id(self, order_id: UUID) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .join(Order.route)
            .join(Order.customer)
            .options(
                contains_eager(Order.route),
                contains_eager(Order.customer),
            )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
    

    async def get_max_sequence(self, route_id: UUID) -> int | None:
        result = await self.session.execute(
            select(func.max(Order.sequence)).where(Order.route_id == route_id)
        )
        return result.scalar_one_or_none()
    #TODO: убрать в другое место 
    async def count_by_route(self, route_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Order).where(Order.route_id == route_id)
        )
        return result.scalar_one()
    


    async def get_total_paid(self, order_id: UUID) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
        )
        return result.scalar_one()

    async def add_payment(
        self,
        order_id: UUID,
        customer_id: UUID,
        amount: Decimal,
        payment_method: PaymentMethod,
        note: str | None,
        photo_url: str | None,
        recorded_by_user_id: UUID,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            note=note,
            photo_url=photo_url,
            recorded_by_user_id=recorded_by_user_id,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment