import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_regions, get_user_language, _escape_md, is_subscriber
from bot.i18n import t
from config import config
from database.engine import get_session
from database.models import UserWishlist
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def _settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings — show user's current preferences."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

    async with get_session() as session:
        regions = await get_user_regions(user.id)

        result = await session.execute(
            select(UserWishlist).where(UserWishlist.user_id == user.id)
        )
        wishlist_count = len(result.scalars().all())

    sub_active = await is_subscriber(user.id)

    region_names = []
    for code in regions:
        info = config.REGIONS.get(code, {})
        region_names.append(f"{info.get('flag', '')} {info.get('name', code)}")
    regions_str = ", ".join(region_names) if region_names else t(lang, "settings_regions_none")

    sub_status = t(lang, "settings_active") if sub_active else t(lang, "settings_inactive")

    lines = [
        t(lang, "settings_header"),
        t(lang, "settings_subscription", status=_escape_md(sub_status)),
        t(lang, "settings_regions", regions=_escape_md(regions_str)),
        t(lang, "settings_watchlist", n=wishlist_count),
        "",
        t(lang, "settings_actions"),
        t(lang, "settings_change_regions"),
        t(lang, "settings_view_watchlist"),
        t(lang, "settings_subscribe"),
        t(lang, "settings_status"),
        t(lang, "settings_language"),
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


settings_handler = CommandHandler("settings", _settings)
