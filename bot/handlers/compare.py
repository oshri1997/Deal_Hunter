import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
            "ℹ️ Usage: /compare Game Title\n"
            "Example: /compare God of War Ragnarok"
        )
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        # Search for deals by game title across all regions
        result = await session.execute(
            select(ActiveDeal)
            .join(Game)
            .where(Game.title.ilike(f"%{game_query}%"))
            .options(selectinload(ActiveDeal.game))
        )
        deals = result.scalars().all()
        
        if not deals:
            await update.message.reply_text(
                f"⚠️ No deals found for '{game_query}'.\n"
                "Try a different search term."
            )
            return
        
        # Get the game title (use first deal's game title)
        game_title = deals[0].game.title

        # Currency conversion rates to ILS
        conversion_to_ils = {
            "ILS": 1.0,
            "USD": 3.7,   # 1 USD = 3.7 ILS
            "INR": 0.0341, # 1 INR = 0.0341 ILS
        }

        # Convert all prices to ILS and sort
        deals_with_ils = []
        for deal in deals:
            rate = conversion_to_ils.get(deal.currency, 1.0)
            price_in_ils = float(deal.price) * rate
            deals_with_ils.append((deal, price_in_ils))
        
        # Sort by ILS price
        deals_with_ils.sort(key=lambda x: x[1])

        lines = [f"📊 <b>Price Comparison: {game_title}</b>\n"]

        if not deals_with_ils:
            await update.message.reply_text(
                f"⚠️ {game_title} has no active deals in any region right now."
            )
            return

        cheapest = deals_with_ils[0][0]
        
        # Show all regions (with and without deals)
        regions_with_deals = {deal.region_code for deal, _ in deals_with_ils}
        
        # First show regions with deals (sorted by price)
        for deal, price_ils in deals_with_ils:
            region_info = config.REGIONS.get(deal.region_code, {})
            flag = region_info.get("flag", "")
            name = region_info.get("name", deal.region_code)
            currency = region_info.get("currency", "USD")

            marker = " 👍 <b>CHEAPEST</b>" if deal == cheapest else ""
            lines.append(
                f"{flag} <b>{name}:</b> {deal.price} {currency} "
                f"(~{price_ils:.0f} ₪) "
                f"(-{deal.discount_percent}%){marker}"
            )
        
        # Then show regions without deals
        for region_code, region_info in config.REGIONS.items():
            if region_code not in regions_with_deals:
                flag = region_info.get("flag", "")
                name = region_info.get("name", region_code)
                lines.append(
                    f"{flag} <b>{name}:</b> <i>No deal available</i>"
                )

        lines.append(
            f"\n💡 Best deal: {config.REGIONS.get(cheapest.region_code, {}).get('flag', '')} "
            f"{config.REGIONS.get(cheapest.region_code, {}).get('name', '')}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


compare_handler = CommandHandler("compare", _compare)
