import logging
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from scraper.manager import ScraperManager
from amazon_checker import AmazonChecker, AMAZON_URL_2
from offgamers_checker import check_offgamers_stock

logger = logging.getLogger(__name__)
scraper_manager = ScraperManager()
amazon_checker = AmazonChecker()
amazon_checker2 = AmazonChecker()
amazon_checker2.URL = AMAZON_URL_2

ADMIN_IDS = [680723948]  # Oshri Moaelm


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def _get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    await update.message.reply_text("🔄 Starting FULL scrape...\nThis will take 30-60 minutes.")
    try:
        new_deals = await scraper_manager.scrape_all_regions(full_scrape=True)
        await update.message.reply_text(f"✅ Full scrape complete! Found {len(new_deals)} new/updated deals")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Full scrape error: {e}", exc_info=True)


async def _scrape_psp(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def _giftcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all 3 gift card links with live availability."""
    await update.message.reply_text("🔍 Checking all gift card sources...")
    try:
        avail1, msg1 = await amazon_checker.check_availability()
        avail2, msg2 = await amazon_checker2.check_availability()
        try:
            in_stock, _ = await check_offgamers_stock()
            og_available = bool(in_stock)
            og_status = ", ".join(in_stock) if in_stock else "Out of stock"
        except Exception:
            og_available = False
            og_status = "Could not check"

        offgamers_url = "https://www.offgamers.com/product/playstation-store-gift-cards?region_id=492c3ca6-c4e6-47fc-b274-c2c35031b271"

        def icon(ok): return "✅" if ok else "❌"

        text = (
            f"🎮 <b>PlayStation Gift Cards (India)</b>\n\n"
            f"{icon(avail1)} <b>Amazon (Cashback)</b>\n"
            f"   {msg1}\n"
            f"   🔗 <a href=\"{amazon_checker.URL}\">Buy on Amazon</a>\n\n"
            f"{icon(avail2)} <b>Amazon ₹1000</b>\n"
            f"   {msg2}\n"
            f"   🔗 <a href=\"{AMAZON_URL_2}\">Buy on Amazon</a>\n\n"
            f"{icon(og_available)} <b>OffGamers</b>\n"
            f"   {og_status}\n"
            f"   🔗 <a href=\"{offgamers_url}\">Buy on OffGamers</a>"
        )
        await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Giftcard check error: {e}", exc_info=True)


async def _check_amazon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Amazon India PlayStation gift card availability."""
    await update.message.reply_text("🔍 Checking Amazon gift card...")
    try:
        is_available, message = await amazon_checker.check_availability()
        if is_available:
            await update.message.reply_text(
                f"✅ <b>Amazon Gift Card Available!</b>\n\nStatus: {message}\n\n🛒 Buy now: {amazon_checker.URL}",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"❌ <b>Not Available</b>\n\nStatus: {message}\n\n🔗 {amazon_checker.URL}",
                parse_mode="HTML"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Amazon check error: {e}", exc_info=True)


async def _check_offgamers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin only: check OffGamers INR gift card stock."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    await update.message.reply_text("🔍 Checking OffGamers stock...")
    try:
        in_stock, out_of_stock = await check_offgamers_stock()
        url = "https://www.offgamers.com/product/playstation-store-gift-cards?region_id=492c3ca6-c4e6-47fc-b274-c2c35031b271"
        lines = [f"🛒 <b>OffGamers PlayStation Gift Cards (INR)</b>\n🔗 <a href=\"{url}\">View on OffGamers</a>\n"]
        if in_stock:
            lines.append("✅ <b>In Stock:</b>")
            lines.extend(f"  • {d}" for d in in_stock)
        if out_of_stock:
            lines.append("\n❌ <b>Out of Stock:</b>")
            lines.extend(f"  • {d}" for d in out_of_stock)
        if not in_stock and not out_of_stock:
            lines.append("⚠️ Could not parse denominations.")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        logger.error(f"OffGamers check error: {e}", exc_info=True)


async def _next_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    from datetime import datetime, timedelta
    now = datetime.now()
    next_scrape = now.replace(hour=2, minute=0, second=0, microsecond=0)
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
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only command")
        return
    await update.message.reply_text("⚠️ Clearing database... This will delete all deals and prices!")
    try:
        from database.engine import get_session
        from database.models import ActiveDeal, Price
        from sqlalchemy import delete
        async with get_session() as session:
            await session.execute(delete(ActiveDeal))
            await session.execute(delete(Price))
            await session.commit()
        await update.message.reply_text(
            "✅ <b>Database Cleared!</b>\n\nAll deals and price history deleted.\n\nUse /scrape_full to repopulate database.",
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
giftcard_handler = CommandHandler("giftcard", _giftcard)
check_amazon_handler = CommandHandler("check_amazon", _check_amazon)
offgamers_handler = CommandHandler("offgamers", _check_offgamers)
next_scrape_handler = CommandHandler("next_scrape", _next_scrape)
clear_db_handler = CommandHandler("cleardb", _clear_db)
