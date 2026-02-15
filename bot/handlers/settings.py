import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_regions, _escape_md
from config import config
from database.engine import get_session
from database.models import UserWishlist
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def _settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings — show user's current preferences."""
    user = update.effective_user
    await get_or_create_user(user)

    async with get_session() as session:
        regions = await get_user_regions(user.id)

        result = await session.execute(
            select(UserWishlist).where(UserWishlist.user_id == user.id)
        )
        wishlist_entries = result.scalars().all()
        wishlist_count = len(wishlist_entries)

    # Build settings display
    region_names = []
    for code in regions:
        info = config.REGIONS.get(code, {})
        region_names.append(f"{info.get('flag', '')} {info.get('name', code)}")
    regions_str = ", ".join(region_names) if region_names else "None"

    lines = [
        "\u2699\ufe0f *Your Settings*\n",
        f"*Account:* \U0001f389 All Features \\(Beta\\)",
        f"*Regions:* {_escape_md(regions_str)}",
        f"*Watchlist:* {wishlist_count} games",
        "",
        "*Quick actions:*",
        "/regions \\- Change regions",
        "/watchlist \\- View watchlist",
        "/donate \\- Support the bot",
        "",
        "\U0001f389 All features are free during beta\\!",
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


settings_handler = CommandHandler("settings", _settings)
