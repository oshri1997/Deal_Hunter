import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from scraper.manager import ScraperManager
from notification import NotificationEngine
from amazon_checker import AmazonChecker
from config import config

logger = logging.getLogger(__name__)


class DealScheduler:
    """Manages periodic scraping and notifications"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scraper_manager = ScraperManager()
        self.notification_engine = NotificationEngine(bot)
        self.amazon_checker = AmazonChecker()
        self.admin_chat_id = None  # Set via /check_amazon command
    
    def start(self, run_initial_scrape: bool = True):
        """Start all scheduled jobs"""
        # Daily scrape at 02:00 (5 pages per region)
        self.scheduler.add_job(
            self._scrape_and_notify,
            trigger=CronTrigger(hour=2, minute=0),
            id="scrape_deals",
            name="Daily scrape at 02:00 (5 pages)",
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
        
        # Check Amazon gift card every 3 hours
        self.scheduler.add_job(
            self._check_amazon,
            trigger=IntervalTrigger(hours=3),
            id="amazon_check",
            name="Check Amazon gift card",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started - Daily scrape at 02:00 (2 pages), Amazon check every 3 hours")
        
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
    
    async def _scrape_and_notify(self):
        """Daily scrape (2 pages) and notifications"""
        logger.info("Starting daily scraping job (2 pages per region)")
        try:
            new_deals = await self.scraper_manager.scrape_all_regions(full_scrape=False)
            logger.info(f"Found {len(new_deals)} new/updated deals")
            
            if new_deals:
                await self.notification_engine.notify_new_deals(new_deals)

            # Check price alerts after scraping
            await self.notification_engine.check_price_alerts()
        except Exception as e:
            logger.error(f"Error in scraping job: {e}", exc_info=True)
    
    async def _cleanup_expired_deals(self):
        """Remove expired deals from database"""
        logger.info("Starting cleanup job")
        try:
            await self.scraper_manager.cleanup_expired_deals()
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}", exc_info=True)
    
    async def _check_amazon(self):
        """Check Amazon PlayStation gift card availability"""
        logger.info("Checking Amazon gift card...")
        try:
            is_available, message = await self.amazon_checker.check_availability()
            
            # Notify admin if status changed to available
            if is_available and self.amazon_checker.last_status != True:
                logger.info(f"🎮 Amazon gift card NOW AVAILABLE!")
                if config.ADMIN_USER_ID:
                    try:
                        await self.bot.send_message(
                            chat_id=config.ADMIN_USER_ID,
                            text=f"🎮 <b>Amazon Gift Card Alert!</b>\n\n{message}\n\n🔗 https://www.amazon.in/Playstation-Gift-Redeemable-Flat-Cashback/dp/B0C1H473H8",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send Amazon alert to admin: {e}")
            else:
                logger.info(f"Amazon status: {message}")
            
            self.amazon_checker.last_status = is_available
            
        except Exception as e:
            logger.error(f"Error in Amazon check: {e}", exc_info=True)
