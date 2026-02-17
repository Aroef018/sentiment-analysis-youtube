from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

# Optimized for Neon serverless PostgreSQL
# Neon free tier has ~100-200 max connections across all clients
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Important for Neon: check connection before use
    pool_recycle=300,  # Recycle connections after 5 minutes (Neon recommendation)
    pool_size=3,  # Reduced from 5 - be conservative with Neon connections
    max_overflow=5,  # Reduced from 10 - max 8 total connections per worker
    pool_timeout=30,  # Wait max 30 seconds for connection from pool
    connect_args={
        "statement_timeout": 300000,  # 5 minutes (reduced from 10 for better responsiveness)
        "command_timeout": 300,  # 5 minutes
        "server_settings": {
            "application_name": "sentiment-analysis",
            "jit": "off",  # Disable JIT for faster cold starts on Neon
        },
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
