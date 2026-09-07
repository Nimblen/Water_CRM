from sqlalchemy import select
from app.db.session import async_session
from app.db.models.user import User
from app.core.security import hash_password
from app.core.config import get_settings

settings = get_settings()

async def main():
    async with async_session() as session:
        exists = await session.scalar(
            select(User).where(User.phone == settings.DEFAULT_ADMIN_PHONE)
        )

        if exists:
            print("Admin already exists")
            return

        admin = User(
            phone=settings.DEFAULT_ADMIN_PHONE,
            hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )

        session.add(admin)
        await session.commit()

        print("Admin created")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())