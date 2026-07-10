
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.user import User

#TODO: доделать репозитории
class UserRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_phone(
        self,
        phone: str,
    ) -> User | None:
        stmt = (
            select(User)
            .where(User.phone == phone)
        )

        result = await self.session.execute(
            stmt
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        user: User,
    ) -> User:
        self.session.add(user)
        await self.session.flush()
        return user