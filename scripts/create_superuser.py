from sqlalchemy import select
from app.db.session import async_session
from app.db.models.user import User
from app.core.security import hash_password


async def main():
    async with async_session() as session:
        exists = await session.scalar(
            select(User).where(User.phone == "998901234567")
        )

        if exists:
            print("Admin already exists")
            return

        admin = User(
            phone="998901234567",
            hashed_password=hash_password("Admin123!"),
            role="admin",
            is_active=True,
        )

        session.add(admin)
        await session.commit()

        print("Admin created")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())