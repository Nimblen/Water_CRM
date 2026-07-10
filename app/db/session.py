from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={"command_timeout": 60},
)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session
