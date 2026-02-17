from urllib.parse import quote

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sqlalchemy import select

from bot.helpers import smart_search_games, format_price_ils
from config import config
from database.engine import get_session
from database.models import ActiveDeal


async def _search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for a game in the database"""
    if not context.args:
        await update.message.reply_text("Usage: /search <game name>\nExample: /search Spider-Man")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching for '{query}'...")

    async with get_session() as session:
        games = await smart_search_games(session, query)

        if not games:
            await update.message.reply_text(f"❌ No games found matching '{query}'")
            return

        message_lines = [f"🎮 Found {len(games)} game(s):\n"]

        for game in games:
            deal_stmt = select(ActiveDeal).where(ActiveDeal.game_id == game.id)
            deal_result = await session.execute(deal_stmt)
            deals = deal_result.scalars().all()

            if deals:
                for deal in deals:
                    region_info = config.REGIONS.get(deal.region_code, {})
                    flag = region_info.get("flag", "")
                    currency = region_info.get("currency", "USD")
                    store_url = region_info.get("store_url", "")
                    search_query = quote(game.title)
                    psn_link = f"{store_url}/search/{search_query}" if store_url else ""

                    ils_suffix = await format_price_ils(float(deal.price), currency)
                    message_lines.append(
                        f"🔥 {flag} {game.title}\n"
                        f"💰 {deal.price} {currency}{ils_suffix} (was {deal.original_price}) -{deal.discount_percent}%\n"
                        f"🛒 PS Store: {psn_link}\n"
                    )
            else:
                message_lines.append(f"⚪ {game.title}\n   No active deals\n")

        message = "\n".join(message_lines)

        if len(message) > 4000:
            message = message[:3990] + "\n..."

        await update.message.reply_text(message)


search_handler = CommandHandler("search", _search)
