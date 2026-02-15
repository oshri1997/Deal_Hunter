"""
Sanity tests - End-to-end integration tests
Run with: python -m pytest tests/test_sanity.py -v
"""
import pytest
import asyncio
from config import config
from database.engine import get_session
from database.models import Game, ActiveDeal, User
from scraper.psprices_new import PSPricesScraper, ScrapedDeal
from datetime import datetime


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection works"""
    from sqlalchemy import text
    async with get_session() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_create_game_in_db():
    """Test creating a game in database"""
    async with get_session() as session:
        game = Game(
            id="test_game_123",
            title="Test Game",
            platform="PS5"
        )
        session.add(game)
        await session.commit()
        
        # Verify it was created
        from sqlalchemy import select
        result = await session.execute(
            select(Game).where(Game.id == "test_game_123")
        )
        found_game = result.scalar_one_or_none()
        assert found_game is not None
        assert found_game.title == "Test Game"
        
        # Cleanup
        await session.delete(found_game)
        await session.commit()


@pytest.mark.asyncio
async def test_create_deal_in_db():
    """Test creating a deal in database"""
    async with get_session() as session:
        # Create game first
        game = Game(
            id="test_game_deal_123",
            title="Test Deal Game",
            platform="PS5"
        )
        session.add(game)
        await session.flush()
        
        # Create deal
        deal = ActiveDeal(
            game_id="test_game_deal_123",
            region_code="IL",
            price=199.0,
            original_price=299.0,
            discount_percent=33,
            currency="ILS",
            page_number=1,
            position_on_page=0
        )
        session.add(deal)
        await session.commit()
        
        # Verify
        from sqlalchemy import select
        result = await session.execute(
            select(ActiveDeal).where(ActiveDeal.game_id == "test_game_deal_123")
        )
        found_deal = result.scalar_one_or_none()
        assert found_deal is not None
        assert found_deal.price == 199.0
        assert found_deal.discount_percent == 33
        
        # Cleanup
        await session.delete(found_deal)
        await session.delete(game)
        await session.commit()


@pytest.mark.asyncio
async def test_scraper_initialization():
    """Test scraper can be initialized"""
    await asyncio.sleep(0)  # Ensure async context
    scraper = PSPricesScraper()
    assert scraper is not None
    assert scraper.base_url == "https://psprices.com"
    assert "IL" in scraper.REGION_MAP
    assert "US" in scraper.REGION_MAP
    assert "IN" in scraper.REGION_MAP


def test_config_loaded():
    """Test configuration is loaded correctly"""
    assert config.TELEGRAM_BOT_TOKEN is not None
    assert config.DATABASE_URL is not None
    assert len(config.REGIONS) >= 3
    assert "IL" in config.REGIONS
    assert "US" in config.REGIONS
    assert "IN" in config.REGIONS


def test_regions_have_required_data():
    """Test all regions have required configuration"""
    required_fields = ["name", "flag", "currency", "currency_symbol", "store_url"]
    
    for region_code, region_info in config.REGIONS.items():
        for field in required_fields:
            assert field in region_info, f"Region {region_code} missing {field}"
            assert region_info[field], f"Region {region_code} has empty {field}"


@pytest.mark.asyncio
async def test_user_creation():
    """Test user can be created in database"""
    async with get_session() as session:
        user = User(
            id=999999999,
            username="test_user",
            first_name="Test",
            is_premium=False
        )
        session.add(user)
        await session.commit()
        
        # Verify
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.id == 999999999)
        )
        found_user = result.scalar_one_or_none()
        assert found_user is not None
        assert found_user.username == "test_user"
        
        # Cleanup
        await session.delete(found_user)
        await session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
