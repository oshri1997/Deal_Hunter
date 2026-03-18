import asyncio
import logging
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from telegram import Bot
from scraper.manager import ScraperManager
from notification import NotificationEngine
from amazon_checker import AmazonChecker
from offgamers_checker import check_offgamers_stock
from engagement import send_engagement_message
from config import config
from database.engine import get_session
from database.models import User
from bot.helpers import is_subscriber

logger = logging.getLogger(__name__)


class DealScheduler:
    """Manages periodic scraping and notifications"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scraper_manager = ScraperManager()
        self.notification_engine = NotificationEngine(bot)
        self.amazon_checker = AmazonChecker()
        self._offgamers_last_status = False
    
    def start(self, run_initial_scrape: bool = True):
        """Start all scheduled jobs"""
        # Daily scan at 04:00 - scrape deals and mark pending
        self.scheduler.add_job(
            self._scrape_deals,
            trigger=CronTrigger(hour=4, minute=0),
            id="scrape_deals",
            name="Daily scrape at 04:00 (2 pages)",
            replace_existing=True
        )

        # Daily delivery at 09:00 - send pending notifications
        self.scheduler.add_job(
            self._deliver_deals,
            trigger=CronTrigger(hour=9, minute=0),
            id="deliver_deals",
            name="Daily delivery at 09:00",
            replace_existing=True
        )

        # Cleanup expired deals daily
        self.scheduler.add_job(
            self._cleanup_expired_deals,
            trigger=CronTrigger(hour=3, minute=0),
            id="cleanup_deals",
            name="Cleanup expired deals",
            replace_existing=True
        )

        # Check Amazon gift card every 30 minutes
        self.scheduler.add_job(
            self._check_amazon,
            trigger=IntervalTrigger(minutes=30),
            id="amazon_check",
            name="Check Amazon gift card",
            replace_existing=True
        )

        # Check OffGamers gift card every 30 minutes
        self.scheduler.add_job(
            self._check_offgamers,
            trigger=IntervalTrigger(minutes=30),
            id="offgamers_check",
            name="Check OffGamers gift card",
            replace_existing=True
        )

        # Engagement messages every 4-6 hours (random interval)
        self._schedule_next_engagement()

        self.scheduler.start()
        logger.info("Scheduler started - Scrape at 04:00, Deliver at 09:00, Amazon+OffGamers check every 30min, engagement every 4-6h")
        
        if run_initial_scrape:
            self.scheduler.add_job(
                self._initial_full_scrape,
                trigger='date',
                id="initial_scrape",
                name="Initial full scrape"
            )
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    async def _initial_full_scrape(self):
        """Run initial full scrape on startup (50 pages per region)"""
        logger.info("Starting initial full scrape (50 pages per region)")
        try:
            new_deals = await self.scraper_manager.scrape_all_regions(full_scrape=True)
            logger.info(f"Initial scrape complete: {len(new_deals)} new deals found")
        except Exception as e:
            logger.error(f"Error in initial scrape: {e}", exc_info=True)
    
    async def _scrape_deals(self):
        """04:00 job: scrape deals and mark them pending for later delivery"""
        logger.info("Starting daily scraping job (2 pages per region)")
        try:
            new_deals = await self.scraper_manager.scrape_all_regions(
                full_scrape=False, mark_pending=True
            )
            logger.info(f"Scrape complete: {len(new_deals)} new/updated deals marked pending for 09:00 delivery")
        except Exception as e:
            logger.error(f"Error in scraping job: {e}", exc_info=True)

    async def _deliver_deals(self):
        """09:00 job: deliver pending deal notifications and check price alerts"""
        logger.info("Starting deal delivery job")
        try:
            await self.notification_engine.deliver_pending_deals()
            await self.notification_engine.check_price_alerts()
        except Exception as e:
            logger.error(f"Error in delivery job: {e}", exc_info=True)

    async def scrape_and_notify_now(self):
        """Manual trigger: scrape and immediately notify (used by admin commands)"""
        logger.info("Starting manual scrape + notify")
        try:
            new_deals = await self.scraper_manager.scrape_all_regions(full_scrape=False)
            logger.info(f"Found {len(new_deals)} new/updated deals")
            if new_deals:
                await self.notification_engine.notify_new_deals(new_deals)
            await self.notification_engine.check_price_alerts()
        except Exception as e:
            logger.error(f"Error in manual scrape+notify: {e}", exc_info=True)
    
    async def _cleanup_expired_deals(self):
        """Remove expired deals from database"""
        logger.info("Starting cleanup job")
        try:
            await self.scraper_manager.cleanup_expired_deals()
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}", exc_info=True)
    
    def _schedule_next_engagement(self):
        """Schedule the next engagement message with a random 4-6 hour interval."""
        hours = random.uniform(4, 6)
        self.scheduler.add_job(
            self._send_engagement,
            trigger=IntervalTrigger(hours=hours),
            id="engagement_message",
            name=f"Engagement message (every {hours:.1f}h)",
            replace_existing=True,
        )

    async def _send_engagement(self):
        """Send an engagement message then reschedule with a new random interval."""
        try:
            await send_engagement_message(self.bot)
        except Exception as e:
            logger.error(f"Error sending engagement message: {e}", exc_info=True)
        # Reschedule with a fresh random interval for next time
        self._schedule_next_engagement()

    async def _check_amazon(self):
        """Check Amazon India PlayStation gift card availability."""
        logger.info("Checking Amazon gift card...")
        try:
            is_available, message = await self.amazon_checker.check_availability()
            if is_available and self.amazon_checker.last_status != True:
                alert_text = (
                    f"🎮 <b>Amazon Gift Card IN STOCK!</b>\n\n"
                    f"Status: {message}\n\n"
                    f"🛒 Buy now: {self.amazon_checker.URL}"
                )
                if config.ADMIN_USER_ID:
                    await self.bot.send_message(chat_id=config.ADMIN_USER_ID, text=alert_text, parse_mode="HTML")
                async with get_session() as session:
                    result = await session.execute(select(User).where(User.is_following == True))
                    followers = result.scalars().all()
                for follower in followers:
                    if follower.id == config.ADMIN_USER_ID:
                        continue
                    if not await is_subscriber(follower.id):
                        continue
                    try:
                        await self.bot.send_message(chat_id=follower.id, text=alert_text, parse_mode="HTML")
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        logger.error(f"Failed to send Amazon alert to {follower.id}: {e}")
            else:
                logger.info(f"Amazon status: {message}")
            self.amazon_checker.last_status = is_available
        except Exception as e:
            logger.error(f"Error in Amazon check: {e}", exc_info=True)

    async def _check_offgamers(self):
        """Check OffGamers stock and notify admin + followers if back in stock."""
        logger.info("Checking OffGamers gift card stock...")
        try:
            in_stock, _ = await check_offgamers_stock()
            is_available = bool(in_stock)

            if is_available and not self._offgamers_last_status:
                alert_text = (
                    f"🎮 <b>OffGamers Gift Card IN STOCK!</b>\n\n"
                    f"Available: {', '.join(in_stock)}\n\n"
                    f"🛒 Buy now: https://www.offgamers.com/product/playstation-store-gift-cards"
                    f"?region_id=492c3ca6-c4e6-47fc-b274-c2c35031b271"
                )
                if config.ADMIN_USER_ID:
                    await self.bot.send_message(chat_id=config.ADMIN_USER_ID, text=alert_text, parse_mode="HTML")
                    logger.info("OffGamers alert sent to admin")
            else:
                logger.info(f"OffGamers in_stock={in_stock}")

            self._offgamers_last_status = is_available
        except Exception as e:
            logger.error(f"Error in OffGamers check: {e}", exc_info=True)
