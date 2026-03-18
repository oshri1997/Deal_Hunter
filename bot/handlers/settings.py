import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_regions, _escape_md, is_subscriber
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
    sub_active = await is_subscriber(user.id)

    region_names = []
    for code in regions:
        info = config.REGIONS.get(code, {})
        region_names.append(f"{info.get('flag', '')} {info.get('name', code)}")
    regions_str = ", ".join(region_names) if region_names else "None"

    sub_status = "✅ Active" if sub_active else "❌ Inactive"

    lines = [
        "\u2699\ufe0f *Your Settings*\n",
        f"*Subscription:* {_escape_md(sub_status)}",
        f"*Regions:* {_escape_md(regions_str)}",
        f"*Watchlist:* {wishlist_count} games",
        "",
        "*Quick actions:*",
        "/regions \\- Change regions",
        "/watchlist \\- View watchlist",
        "/subscribe \\- Get premium alerts",
        "/status \\- Check subscription",
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


settings_handler = CommandHandler("settings", _settings)
