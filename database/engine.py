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
        # Increase timeout for migration statements
        await conn.execute(text("SET statement_timeout = '30s'"))

        await conn.run_sync(Base.metadata.create_all)
        # Add is_following column to existing databases that predate it
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_following BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        # Add pending_notification column for decoupled scan/delivery
        await conn.execute(text(
            "ALTER TABLE active_deals ADD COLUMN IF NOT EXISTS pending_notification BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        # Create subscribers table for paywall system
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS subscribers ("
            "  telegram_user_id BIGINT PRIMARY KEY,"
            "  username TEXT,"
            "  full_name TEXT,"
            "  requested_at TIMESTAMP DEFAULT NOW(),"
            "  approved_at TIMESTAMP,"
            "  active BOOLEAN DEFAULT FALSE"
            ")"
        ))

        # Reset timeout back to default
        await conn.execute(text("SET statement_timeout = DEFAULT"))
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
