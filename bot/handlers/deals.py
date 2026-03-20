import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from bot.helpers import get_or_create_user, get_user_regions, get_user_language, format_price_ils
from bot.i18n import t
from scraper.manager import ScraperManager

logger = logging.getLogger(__name__)
scraper_manager = ScraperManager()


async def _deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /deals command — show top 20 deals for user's regions."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)
    regions = await get_user_regions(user.id)

    if not regions:
        await update.message.reply_text(t(lang, "deals_no_regions"))
        return

    await update.message.reply_text(t(lang, "deals_fetching"))
    context.user_data["deals_regions"] = regions
    context.user_data["deals_lang"] = lang
    await _show_deals_page(update, context, regions, offset=0, lang=lang)


async def _show_deals_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    regions: list,
    offset: int,
    lang: str = "en",
):
    """Show 10 deals per region, grouped by region with beautiful formatting."""
    from config import config
    from urllib.parse import quote

    message_lines = [t(lang, "deals_header")]
    has_more_deals = False

    for region_code in regions:
        deals = await scraper_manager.get_active_deals(region_code, limit=10 + offset + 1)
        current_deals = deals[offset:offset + 10]

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
                tag_badge = ""
                if deal.price_tag == "New lowest!":
                    tag_badge = t(lang, "deals_new_lowest")
                elif deal.price_tag == "Lowest":
                    tag_badge = t(lang, "deals_lowest")

                if deal.discount_percent >= 70:
                    discount_color = "🔴"
                elif deal.discount_percent >= 50:
                    discount_color = "🟠"
                else:
                    discount_color = "🟡"

                search_query = quote(deal.game.title)
                psn_link = f"{store_url}/search/{search_query}" if store_url else ""

                ils_suffix = await format_price_ils(float(deal.price), currency)
                orig_ils_suffix = await format_price_ils(float(deal.original_price), currency)
                ps_store_label = t(lang, "deals_ps_store")
                message_lines.append(
                    f"<b>{i}.</b> <code>{deal.game.title}</code>{tag_badge}\n"
                    f"    💰 <b>{deal.price} {currency}{ils_suffix}</b> <s>{deal.original_price} {currency}{orig_ils_suffix}</s>\n"
                    f"    {discount_color} <b>-{deal.discount_percent}%</b> OFF\n"
                    f"    🛒 <a href='{psn_link}'>{ps_store_label}</a>\n"
                )

    if len(message_lines) == 1:
        text = t(lang, "deals_none")
        if update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return

    message = "\n".join(message_lines)

    keyboard = None
    if has_more_deals:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                t(lang, "deals_show_more"),
                callback_data=f"deals_more_{offset + 10}",
            )
        ]])

    if update.callback_query:
        await update.callback_query.edit_message_text(message, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(message, parse_mode="HTML", reply_markup=keyboard)


async def _deals_more_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Show More' button."""
    query = update.callback_query
    lang = context.user_data.get("deals_lang", "en")
    await query.answer(t(lang, "deals_loading_more"))

    offset = int(query.data.split("_")[-1])
    regions = context.user_data.get("deals_regions", [])

    if not regions:
        await query.edit_message_text(t(lang, "deals_session_expired"))
        return

    await _show_deals_page(update, context, regions, offset, lang=lang)


deals_handler = CommandHandler("deals", _deals)
deals_more_handler = CallbackQueryHandler(_deals_more_callback, pattern="^deals_more_")
