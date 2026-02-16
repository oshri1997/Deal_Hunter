import pytest
from database.engine import init_db, _get_engine


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all database tables before integration tests run."""
    await init_db()
    yield
    await _get_engine().dispose()
