from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine.url import make_url
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def normalize_asyncpg_url(raw_url: str) -> str:
    """Remove psycopg-style params (sslmode/channel_binding) and set ssl=true for asyncpg."""
    try:
        url_obj = make_url(raw_url)
        if url_obj.drivername.endswith("asyncpg"):
            q = dict(url_obj.query)
            q.pop("sslmode", None)
            q.pop("channel_binding", None)
            if "ssl" not in q:
                q["ssl"] = "true"
            url_obj = url_obj.set(query=q)
        cleaned = str(url_obj)
        logger.info(f"Using DATABASE_URL: {cleaned}")
        return cleaned
    except Exception as e:
        logger.warning(f"Failed to normalize DATABASE_URL, using raw: {e}")
        return raw_url


DATABASE_URL = normalize_asyncpg_url(settings.DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
