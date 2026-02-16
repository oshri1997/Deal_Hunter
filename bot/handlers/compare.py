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
        # Search for games by title
        games_result = await session.execute(
            select(Game)
            .where(Game.title.ilike(f"%{game_query}%"))
            .limit(10)
        )
        games = games_result.scalars().all()
        
        if not games:
            await update.message.reply_text(
                f"⚠️ No games found for '{game_query}'.\n"
                "Try a different search term."
            )
            return
        
        # Currency conversion rates to ILS
        conversion_to_ils = {
            "ILS": 1.0,
            "USD": 3.7,
            "INR": 0.0341,
        }
        
        # Process each game separately
        all_lines = []
        seen_game_titles = set()  # Track by title instead of ID
        
        for game in games:
            if game.title in seen_game_titles:
                continue
            seen_game_titles.add(game.title)
            
            # Get all deals for games with this title (may have different IDs)
            result = await session.execute(
                select(ActiveDeal)
                .join(Game)
                .where(Game.title == game.title)
            )
            deals = result.scalars().all()
            
            if not deals:
                continue
            
            # Convert prices to ILS and sort
            deals_with_ils = []
            for deal in deals:
                rate = conversion_to_ils.get(deal.currency, 1.0)
                price_in_ils = float(deal.price) * rate
                deals_with_ils.append((deal, price_in_ils))
            
            deals_with_ils.sort(key=lambda x: x[1])
            
            # Build output for this game
            game_lines = [f"\n📊 <b>{game.title}</b>"]
            
            cheapest = deals_with_ils[0][0]
            regions_with_deals = {deal.region_code for deal, _ in deals_with_ils}
            
            # Show regions with deals
            for deal, price_ils in deals_with_ils:
                region_info = config.REGIONS.get(deal.region_code, {})
                flag = region_info.get("flag", "")
                name = region_info.get("name", deal.region_code)
                currency = region_info.get("currency", "USD")
                
                marker = " 👍 <b>CHEAPEST</b>" if deal == cheapest else ""
                game_lines.append(
                    f"{flag} <b>{name}:</b> {deal.price} {currency} "
                    f"(~{price_ils:.0f} ₪) "
                    f"(-{deal.discount_percent}%){marker}"
                )
            
            # Show regions without deals
            for region_code, region_info in config.REGIONS.items():
                if region_code not in regions_with_deals:
                    flag = region_info.get("flag", "")
                    name = region_info.get("name", region_code)
                    game_lines.append(
                        f"{flag} <b>{name}:</b> <i>No deal available</i>"
                    )
            
            game_lines.append(
                f"💡 Best: {config.REGIONS.get(cheapest.region_code, {}).get('flag', '')} "
                f"{config.REGIONS.get(cheapest.region_code, {}).get('name', '')}"
            )
            
            # Add PS Store link
            from urllib.parse import quote
            best_store_url = config.REGIONS.get(cheapest.region_code, {}).get('store_url', '')
            if best_store_url:
                store_link = f"{best_store_url}/search/{quote(game.title)}"
                game_lines.append(f"🛒 <a href='{store_link}'>Buy on PS Store</a>")
            
            all_lines.extend(game_lines)
        
        if not all_lines:
            await update.message.reply_text(
                f"⚠️ No deals found for '{game_query}'.\n"
                "These games are not currently on sale."
            )
            return
        
        # Add header
        header = f"🎮 <b>Price Comparison for '{game_query}'</b>\n"
        all_lines.insert(0, header)
        
    await update.message.reply_text("\n".join(all_lines), parse_mode="HTML")


compare_handler = CommandHandler("compare", _compare)
