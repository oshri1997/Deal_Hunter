import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from scraper.manager import ScraperManager
from amazon_checker import AmazonChecker

logger = logging.getLogger(__name__)
scraper_manager = ScraperManager()
amazon_checker = AmazonChecker()

# Admin user IDs
ADMIN_IDS = [680723948]  # Oshri Moaelm


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


async def _get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get your Telegram user ID"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "No username"
    first_name = update.effective_user.first_name or "No name"
    
    await update.message.reply_text(
        f"👤 Your Telegram Info:\n\n"
        f"User ID: {user_id}\n"
        f"Username: @{username}\n"
        f"Name: {first_name}\n\n"
        f"To make yourself admin:\n"
        f"1. Copy your User ID: {user_id}\n"
        f"2. Edit bot/handlers/admin.py\n"
        f"3. Change ADMIN_IDS = [{user_id}]"
    )


async def _scrape_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger immediate scrape (2 pages)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    
    await update.message.reply_text("🔄 Starting scrape (2 pages per region)...")
    
    try:
        new_deals = await scraper_manager.scrape_all_regions(full_scrape=False)
        await update.message.reply_text(f"✅ Scrape complete! Found {len(new_deals)} new/updated deals")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Scrape error: {e}", exc_info=True)


async def _scrape_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger full scrape (50 pages)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    
    await update.message.reply_text("🔄 Starting FULL scrape (50 pages per region)...\nThis will take 30-60 minutes.")
    
    try:
        new_deals = await scraper_manager.scrape_all_regions(full_scrape=True)
        await update.message.reply_text(f"✅ Full scrape complete! Found {len(new_deals)} new/updated deals")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Full scrape error: {e}", exc_info=True)


async def _scrape_psp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger PSPrices scrape"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    
    await update.message.reply_text("🔄 Starting PSPrices scrape...")
    
    try:
        new_deals = await scraper_manager.scrape_all_regions(full_scrape=False)
        await update.message.reply_text(f"✅ PSPrices scrape complete! Found {len(new_deals)} deals")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"PSPrices scrape error: {e}", exc_info=True)


async def _check_amazon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Amazon PlayStation gift card availability"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    
    await update.message.reply_text("🔍 Checking Amazon gift card availability...")
    
    try:
        is_available, message = await amazon_checker.check_availability()
        
        if is_available:
            await update.message.reply_text(
                f"✅ PlayStation Gift Card Available!\n\n"
                f"Status: {message}\n\n"
                f"🔗 {amazon_checker.URL}"
            )
        else:
            await update.message.reply_text(
                f"❌ Not Available\n\n"
                f"Status: {message}\n\n"
                f"🔗 {amazon_checker.URL}"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking Amazon: {str(e)}")
        logger.error(f"Amazon check error: {e}", exc_info=True)


async def _next_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show next scheduled scraping time"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    
    from datetime import datetime, timedelta
    
    now = datetime.now()
    next_scrape = now.replace(hour=2, minute=0, second=0, microsecond=0)
    
    # If it's past 02:00 today, show tomorrow's time
    if now.hour >= 2:
        next_scrape += timedelta(days=1)
    
    time_until = next_scrape - now
    hours = int(time_until.total_seconds() // 3600)
    minutes = int((time_until.total_seconds() % 3600) // 60)
    
    await update.message.reply_text(
        f"⏰ <b>Next Scheduled Scrape</b>\n\n"
        f"📅 Date: {next_scrape.strftime('%Y-%m-%d')}\n"
        f"🕐 Time: <b>{next_scrape.strftime('%H:%M')}</b>\n\n"
        f"⏳ Time remaining: <b>{hours}h {minutes}m</b>",
        parse_mode='HTML'
    )


async def _clear_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all deals from database"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    
    await update.message.reply_text("⚠️ Clearing database... This will delete all deals and prices!")
    
    try:
        from database.engine import get_session
        from database.models import ActiveDeal, Price
        from sqlalchemy import delete
        
        async with get_session() as session:
            # Delete all active deals
            await session.execute(delete(ActiveDeal))
            # Delete all price history
            await session.execute(delete(Price))
            await session.commit()
        
        await update.message.reply_text(
            "✅ <b>Database Cleared!</b>\n\n"
            "All deals and price history deleted.\n\n"
            "Use /scrape_full to repopulate database.",
            parse_mode='HTML'
        )
        logger.info("Database cleared by admin")
    except Exception as e:
        await update.message.reply_text(f"❌ Error clearing database: {str(e)}")
        logger.error(f"Clear DB error: {e}", exc_info=True)


get_id_handler = CommandHandler("getid", _get_id)
scrape_now_handler = CommandHandler("scrape_now", _scrape_now)
scrape_full_handler = CommandHandler("scrape_full", _scrape_full)
scrape_psp_handler = CommandHandler("scrape_psp", _scrape_psp)
check_amazon_handler = CommandHandler("check_amazon", _check_amazon)
next_scrape_handler = CommandHandler("next_scrape", _next_scrape)
clear_db_handler = CommandHandler("cleardb", _clear_db)
