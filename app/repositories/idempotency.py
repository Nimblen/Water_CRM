from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.idempotency_key import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str, endpoint: str) -> IdempotencyKey | None:
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.key == key,
            IdempotencyKey.endpoint == endpoint,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, key: str, endpoint: str, status_code: int, response_body: dict) -> None:
        record = IdempotencyKey(
            key=key, endpoint=endpoint, status_code=status_code, response_body=response_body,
        )
        self.session.add(record)
        await self.session.flush()