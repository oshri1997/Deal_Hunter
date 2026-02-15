import logging

from sqlalchemy import select
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, _escape_md
from config import config
from database.engine import get_session
from database.models import ActiveDeal, Game

logger = logging.getLogger(__name__)


async def _compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compare <game> — compare a game's price across all regions."""
    user = update.effective_user
    await get_or_create_user(user)

    if not context.args:
        await update.message.reply_text(
            "\u2139\ufe0f *Usage:* `/compare Game Title`\n"
            "Example: `/compare God of War Ragnarok`",
            parse_mode="MarkdownV2",
        )
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        # Find matching games
        result = await session.execute(
            select(Game).where(Game.title.ilike(f"%{game_query}%")).limit(1)
        )
        game = result.scalar_one_or_none()

        if not game:
            await update.message.reply_text(
                f"\u26a0\ufe0f No game found matching *{_escape_md(game_query)}*\\.\n"
                "Try a different search term\\.",
                parse_mode="MarkdownV2",
            )
            return

        # Get active deals for this game across all regions
        result = await session.execute(
            select(ActiveDeal)
            .where(ActiveDeal.game_id == game.id)
            .order_by(ActiveDeal.price.asc())
        )
        deals = result.scalars().all()

        if not deals:
            await update.message.reply_text(
                f"\u26a0\ufe0f *{_escape_md(game.title)}* has no active deals right now\\.",
                parse_mode="MarkdownV2",
            )
            return

        lines = [f"\U0001f4ca *Price Comparison: {_escape_md(game.title)}*\n"]

        cheapest = deals[0]
        for deal in deals:
            region_info = config.REGIONS.get(deal.region_code, {})
            flag = region_info.get("flag", "")
            name = region_info.get("name", deal.region_code)
            symbol = region_info.get("currency_symbol", "$")

            marker = " \U0001f44d CHEAPEST" if deal == cheapest else ""
            lines.append(
                f"{flag} *{_escape_md(name)}:* {symbol}{deal.price:.2f} "
                f"\\(\\-{deal.discount_percent}%\\){_escape_md(marker)}"
            )

        lines.append(
            f"\n\U0001f4a1 Best deal: {config.REGIONS.get(cheapest.region_code, {}).get('flag', '')} "
            f"{_escape_md(config.REGIONS.get(cheapest.region_code, {}).get('name', ''))}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


compare_handler = CommandHandler("compare", _compare)
