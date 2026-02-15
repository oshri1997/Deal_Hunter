import logging
import asyncio
from telegram.ext import Application
from database.engine import init_db
from scheduler import DealScheduler
from config import config
from bot.handlers import (
    start_handler,
    help_handler,
    regions_handler,
    region_callback_handler,
    deals_handler,
    deals_more_handler,
    watch_handler,
    unwatch_handler,
    watchlist_handler,
    compare_handler,
    settings_handler,
    premium_handler,
    get_id_handler,
    scrape_now_handler,
    scrape_full_handler,
    scrape_psp_handler,
    check_amazon_handler,
    next_scrape_handler,
    clear_db_handler,
    search_handler,
    donate_handler,
    support_handler,
    alert_handler,
    alerts_handler,
    delalert_handler,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """Initialize database and scheduler after bot starts"""
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Starting scheduler...")
    scheduler = DealScheduler(application.bot)
    scheduler.start(run_initial_scrape=False)
    
    application.bot_data["scheduler"] = scheduler


async def post_shutdown(application: Application):
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    scheduler = application.bot_data.get("scheduler")
    if scheduler:
        scheduler.stop()


def main():
    """Start the bot"""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment!")
        return
    
    logger.info("Building application...")
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    # Register handlers
    logger.info("Registering handlers...")
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(regions_handler)
    application.add_handler(region_callback_handler)
    application.add_handler(deals_handler)
    application.add_handler(deals_more_handler)
    application.add_handler(watch_handler)
    application.add_handler(unwatch_handler)
    application.add_handler(watchlist_handler)
    application.add_handler(compare_handler)
    application.add_handler(settings_handler)
    application.add_handler(premium_handler)
    application.add_handler(get_id_handler)
    application.add_handler(scrape_now_handler)
    application.add_handler(scrape_full_handler)
    application.add_handler(scrape_psp_handler)
    application.add_handler(check_amazon_handler)
    application.add_handler(next_scrape_handler)
    application.add_handler(clear_db_handler)
    application.add_handler(search_handler)
    application.add_handler(donate_handler)
    application.add_handler(support_handler)
    application.add_handler(alert_handler)
    application.add_handler(alerts_handler)
    application.add_handler(delalert_handler)

    logger.info("🚀 PS5 Deal Hunter Bot starting...")
    logger.info(f"Daily scrape scheduled at 02:00")
    logger.info(f"Amazon check every 3 hours")
    logger.info(f"Use /getid to get your Telegram ID for admin access")
    logger.info(f"Supported regions: {', '.join(config.REGIONS.keys())}")
    
    # Start the bot
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
