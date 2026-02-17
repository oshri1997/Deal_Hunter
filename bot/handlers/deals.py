import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from bot.helpers import get_or_create_user, get_user_regions, format_price_ils
from scraper.manager import ScraperManager

logger = logging.getLogger(__name__)
scraper_manager = ScraperManager()


async def _deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /deals command — show top 20 deals for user's regions."""
    user = update.effective_user
    await get_or_create_user(user)
    regions = await get_user_regions(user.id)

    if not regions:
        await update.message.reply_text(
            "⚠️ You haven't selected any regions yet.\n"
            "Use /regions to choose your PSN store regions first!"
        )
        return

    await update.message.reply_text("🔍 Fetching latest deals...")
    context.user_data['deals_regions'] = regions
    await _show_deals_page(update, context, regions, offset=0)


async def _show_deals_page(update: Update, context: ContextTypes.DEFAULT_TYPE, regions: list, offset: int):
    """Show 10 deals per region, grouped by region with beautiful formatting"""
    from config import config
    from urllib.parse import quote

    message_lines = ["<b>🎮 PLAYSTATION DEALS 🎮</b>\n"]
    has_more_deals = False

    for region_code in regions:
        # Get 11 deals to check if there are more
        deals = await scraper_manager.get_active_deals(region_code, limit=10 + offset + 1)
        
        # Take only the deals for current page
        current_deals = deals[offset:offset + 10]
        
        # Check if there are more deals
        if len(deals) > offset + 10:
            has_more_deals = True

        if current_deals:
            region_info = config.REGIONS.get(region_code, {})
            flag = region_info.get("flag", "")
            region_name = region_info.get("name", region_code)
            currency = region_info.get("currency", "USD")
            store_url = region_info.get("store_url", "")

            message_lines.append(f"\n{'═' * 35}")
            message_lines.append(f"<b>{flag} {region_name.upper()}</b>")
            message_lines.append(f"{'═' * 35}\n")

            for i, deal in enumerate(current_deals, offset + 1):
                # Price tag badge
                tag_badge = ""
                if deal.price_tag == "New lowest!":
                    tag_badge = " 🔥 <b>NEW LOWEST!</b>"
                elif deal.price_tag == "Lowest":
                    tag_badge = " ⭐ <b>LOWEST</b>"

                # Discount color
                if deal.discount_percent >= 70:
                    discount_color = "🔴"  # Red - amazing deal
                elif deal.discount_percent >= 50:
                    discount_color = "🟠"  # Orange - great deal
                else:
                    discount_color = "🟡"  # Yellow - good deal

                # Store link
                search_query = quote(deal.game.title)
                psn_link = f"{store_url}/search/{search_query}" if store_url else ""

                ils_suffix = await format_price_ils(float(deal.price), currency)
                orig_ils_suffix = await format_price_ils(float(deal.original_price), currency)
                message_lines.append(
                    f"<b>{i}.</b> <code>{deal.game.title}</code>{tag_badge}\n"
                    f"    💰 <b>{deal.price} {currency}{ils_suffix}</b> <s>{deal.original_price} {currency}{orig_ils_suffix}</s>\n"
                    f"    {discount_color} <b>-{deal.discount_percent}%</b> OFF\n"
                    f"    🛒 <a href='{psn_link}'>PS Store</a>\n"
                )
    
    if len(message_lines) == 1:
        text = "❌ No deals found right now. Check back later!"
        if update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return
    
    message = "\n".join(message_lines)
    
    # Add "Show More" button if there are more deals
    keyboard = None
    if has_more_deals:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📄 Show More", callback_data=f"deals_more_{offset + 10}")
        ]])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
    else:
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)


async def _deals_more_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Show More' button"""
    query = update.callback_query
    await query.answer("Loading more deals...")
    
    offset = int(query.data.split('_')[-1])
    regions = context.user_data.get('deals_regions', [])
    
    if not regions:
        await query.edit_message_text("⚠️ Session expired. Use /deals again.")
        return
    
    await _show_deals_page(update, context, regions, offset)


deals_handler = CommandHandler("deals", _deals)
deals_more_handler = CallbackQueryHandler(_deals_more_callback, pattern="^deals_more_")
