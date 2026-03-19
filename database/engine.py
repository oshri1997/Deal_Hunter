import logging
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import config
from database.models import Base

logger = logging.getLogger(__name__)

_engine = None
_async_session = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            config.DATABASE_URL,
            echo=False,
            pool_size=10,
            max_overflow=20,
            connect_args={
                "prepared_statement_cache_size": 0,
            },
        )
    return _engine


def _get_session_factory():
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session


async def init_db():
    """Create all tables if they don't exist."""
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Run each migration individually — if it times out or the column
        # already exists, log and continue.  Supabase free-tier has a very
        # short statement_timeout that can't be overridden.
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_following BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE active_deals ADD COLUMN IF NOT EXISTS pending_notification BOOLEAN NOT NULL DEFAULT FALSE",
            (
                "CREATE TABLE IF NOT EXISTS subscribers ("
                "  telegram_user_id BIGINT PRIMARY KEY,"
                "  username TEXT,"
                "  full_name TEXT,"
                "  requested_at TIMESTAMP DEFAULT NOW(),"
                "  approved_at TIMESTAMP,"
                "  active BOOLEAN DEFAULT FALSE"
                ")"
            ),
        ]

        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                logger.warning(f"Migration skipped (probably already applied): {e}")

    logger.info("Database tables created successfully")


@asynccontextmanager
async def get_session():
    """Provide a transactional database session."""
    session = _get_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
