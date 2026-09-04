import uuid
from decimal import Decimal
from app.core.exceptions.conflict import BothBalancesSetError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.customer import Customer
from app.repositories.customer import CustomerBalanceAdjustmentsRepository



class CustomerBalanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.adjustments_repo = CustomerBalanceAdjustmentsRepository(session)

    async def set_balance(
        self,
        customer: Customer,
        new_debt: Decimal,
        new_prepayment: Decimal,
        user_id: uuid.UUID,
        reason: str,
    ) -> None:
        if new_debt > 0 and new_prepayment > 0:
            raise BothBalancesSetError()

        debt_before, prepayment_before = customer.debt, customer.prepayment
        customer.debt = new_debt
        customer.prepayment = new_prepayment
        await self._flush_and_log(customer, debt_before, prepayment_before, user_id, reason)

    async def apply_delta(
        self,
        customer: Customer,
        delta: Decimal,
        user_id: uuid.UUID,
        reason: str,
    ) -> None:
        debt_before, prepayment_before = customer.debt, customer.prepayment
        net = prepayment_before - debt_before + delta

        if net >= 0:
            customer.prepayment, customer.debt = net, Decimal("0.00")
        else:
            customer.prepayment, customer.debt = Decimal("0.00"), -net

        await self._flush_and_log(customer, debt_before, prepayment_before, user_id, reason)

    async def _flush_and_log(
        self,
        customer: Customer,
        debt_before: Decimal,
        prepayment_before: Decimal,
        user_id: uuid.UUID,
        reason: str,
    ) -> None:
        await self.session.flush()
        if customer.debt != debt_before or customer.prepayment != prepayment_before:
            await self.adjustments_repo.create(
                customer_id=customer.id,
                user_id=user_id,
                debt_before=debt_before,
                debt_after=customer.debt,
                prepayment_before=prepayment_before,
                prepayment_after=customer.prepayment,
                reason=reason,
            )