from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Debug log to confirm DATABASE_URL at runtime (helps diagnose SSL params)
logger.info(f"Using DATABASE_URL: {settings.DATABASE_URL}")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
