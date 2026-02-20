import asyncio
import logging
from datetime import datetime

from sqlalchemy import delete, select, func
from sqlalchemy.orm import contains_eager

from config import config
from database.engine import get_session
from database.models import ActiveDeal, Game, Price
from scraper.psprices_new import PSPricesScraper, ScrapedDeal

logger = logging.getLogger(__name__)


class ScraperManager:
    """Coordinates scraping across regions and persists results to the database."""

    def __init__(self):
        self.scraper = PSPricesScraper()

    async def scrape_all_regions(self, full_scrape: bool = False) -> list[ActiveDeal]:
        """Scrape deals from all supported regions using PSPrices.

        Args:
            full_scrape: If True, scrape 50 pages. If False, scrape 2 pages per region.
        """
        all_new_deals: list[tuple[str, any]] = []

        # Scrape one region at a time to avoid Cloudflare blocks
        semaphore = asyncio.Semaphore(1)

        async def _scrape_region(region_code: str):
            async with semaphore:
                try:
                    if region_code not in ["IL", "IN", "US"]:
                        return
                    deals = await self.scraper.scrape_region(region_code, full_scrape=full_scrape)
                    if deals:
                        new_deals = await self._persist_deals(region_code, deals)
                        if new_deals:
                            for deal in new_deals:
                                all_new_deals.append((region_code, deal))
                except Exception as e:
                    logger.error(f"Error scraping {region_code}: {e}")

        tasks = [_scrape_region(rc) for rc in config.REGIONS]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Scrape complete: {len(all_new_deals)} new/updated deals")

        # Convert ScrapedDeal to ActiveDeal objects for notification
        active_deals = []
        async with get_session() as session:
            for region_code, deal in all_new_deals:
                result = await session.execute(
                    select(ActiveDeal).where(
                        ActiveDeal.game_id == deal.game_id,
                        ActiveDeal.region_code == region_code
                    )
                )
                active_deal = result.scalar_one_or_none()
                if active_deal:
                    active_deals.append(active_deal)

        return active_deals

    async def scrape_region(self, region_code: str) -> list:
        """Scrape a single region using PSPrices."""
        deals = await self.scraper.scrape_region(region_code, max_pages=10)
        if deals:
            return await self._persist_deals(region_code, deals)
        return []

    async def _persist_deals(self, region_code: str, deals: list) -> list:
        """Store scraped deals in database using batch operations for speed."""
        new_deals = []
        logger.info(f"Persisting {len(deals)} deals for {region_code}...")

        async with get_session() as session:
            # Batch fetch all existing games and deals
            game_ids = [d.game_id for d in deals]
            
            existing_games_result = await session.execute(
                select(Game).where(Game.id.in_(game_ids))
            )
            existing_games = {g.id: g for g in existing_games_result.scalars().all()}
            
            existing_deals_result = await session.execute(
                select(ActiveDeal).where(
                    ActiveDeal.game_id.in_(game_ids),
                    ActiveDeal.region_code == region_code
                )
            )
            existing_deals = {d.game_id: d for d in existing_deals_result.scalars().all()}
            
            # Process all deals
            for deal in deals:
                # Add game if new
                if deal.game_id not in existing_games:
                    game = Game(
                        id=deal.game_id,
                        title=deal.title,
                        cover_url=deal.cover_url,
                        genre=deal.genre,
                        platform=deal.platform,
                    )
                    session.add(game)
                    existing_games[deal.game_id] = game
                elif deal.cover_url and not existing_games[deal.game_id].cover_url:
                    existing_games[deal.game_id].cover_url = deal.cover_url
                
                # Add or update deal
                existing_deal = existing_deals.get(deal.game_id)
                is_new = False
                
                if not existing_deal:
                    is_new = True
                    active_deal = ActiveDeal(
                        game_id=deal.game_id,
                        region_code=region_code,
                        price=deal.price,
                        original_price=deal.original_price,
                        discount_percent=deal.discount_percent,
                        currency=deal.currency,
                        sale_end_date=deal.sale_end_date,
                        price_tag=deal.price_tag,
                        page_number=deal.page_number,
                        position_on_page=deal.position_on_page,
                    )
                    session.add(active_deal)
                else:
                    # Check if price or discount changed (real changes)
                    if (float(existing_deal.price) != float(deal.price) or 
                        existing_deal.discount_percent != deal.discount_percent):
                        is_new = True
                    
                    # Always update all fields
                    existing_deal.price = deal.price
                    existing_deal.original_price = deal.original_price
                    existing_deal.discount_percent = deal.discount_percent
                    existing_deal.sale_end_date = deal.sale_end_date
                    existing_deal.price_tag = deal.price_tag
                    existing_deal.page_number = deal.page_number
                    existing_deal.position_on_page = deal.position_on_page
                
                # Add price history
                price_record = Price(
                    game_id=deal.game_id,
                    region_code=region_code,
                    price=deal.price,
                    original_price=deal.original_price,
                    discount_percent=deal.discount_percent,
                    currency=deal.currency,
                    sale_end_date=deal.sale_end_date,
                )
                session.add(price_record)
                
                if is_new:
                    new_deals.append(deal)

            # Remove stale deals: if we scraped pages 1-5, any deal in the DB
            # that claims to be on pages 1-5 but wasn't found in this scrape
            # is no longer on the website and should be removed.
            scraped_pages = {d.page_number for d in deals}
            scraped_game_ids = set(game_ids)
            if scraped_pages:
                stale_result = await session.execute(
                    select(ActiveDeal).where(
                        ActiveDeal.region_code == region_code,
                        ActiveDeal.page_number.in_(scraped_pages),
                        ActiveDeal.game_id.notin_(scraped_game_ids)
                    )
                )
                stale_deals = stale_result.scalars().all()
                if stale_deals:
                    stale_ids = [d.game_id for d in stale_deals]
                    await session.execute(
                        delete(ActiveDeal).where(
                            ActiveDeal.region_code == region_code,
                            ActiveDeal.game_id.in_(stale_ids)
                        )
                    )
                    logger.info(f"Removed {len(stale_deals)} stale deals for {region_code} (no longer on scraped pages {sorted(scraped_pages)})")

            # Commit all at once
            await session.commit()
        
        logger.info(f"Persisted {len(new_deals)} new/updated deals for {region_code}")
        return new_deals

    async def cleanup_expired_deals(self):
        """Remove deals that have passed their sale end date."""
        async with get_session() as session:
            now = datetime.utcnow()
            await session.execute(
                delete(ActiveDeal).where(ActiveDeal.sale_end_date < now)
            )
            logger.info("Cleaned up expired deals")

    async def get_active_deals(self, region_code: str, limit: int = 20) -> list[ActiveDeal]:
        """Get deals from all pages, ordered by page number and position on page."""
        async with get_session() as session:
            result = await session.execute(
                select(ActiveDeal)
                .join(Game)
                .where(ActiveDeal.region_code == region_code)
                .order_by(ActiveDeal.page_number.asc(), ActiveDeal.position_on_page.asc())
                .limit(limit)
                .options(contains_eager(ActiveDeal.game))
            )
            deals = result.scalars().all()
            return deals

    async def get_deals_paginated(self, region_codes: list[str], offset: int = 0, limit: int = 20) -> tuple[list[ActiveDeal], int]:
        """Get deals across multiple regions with pagination, sorted by highest ID first (most recently added)."""
        from sqlalchemy import func
        async with get_session() as session:
            # Get total count
            count_result = await session.execute(
                select(func.count(ActiveDeal.id)).where(ActiveDeal.region_code.in_(region_codes))
            )
            total = count_result.scalar()
            
            # Get paginated deals
            result = await session.execute(
                select(ActiveDeal)
                .where(ActiveDeal.region_code.in_(region_codes))
                .order_by(ActiveDeal.id.desc())
                .offset(offset)
                .limit(limit)
            )
            deals = result.scalars().all()
            
            # Eagerly load game data
            for deal in deals:
                await session.refresh(deal, ["game"])
            
            return deals, total
