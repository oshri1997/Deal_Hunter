import logging

from sqlalchemy import select
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from urllib.parse import quote

from bot.helpers import get_or_create_user, get_user_language, _escape_md, smart_search_games, format_price_ils, require_subscriber
from bot.i18n import t
from config import config
from database.engine import get_session
from database.models import ActiveDeal, Game

logger = logging.getLogger(__name__)


async def _compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compare <game> — compare a game's price across all regions."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

    if not await require_subscriber(update):
        return

    if not context.args:
        await update.message.reply_text(t(lang, "compare_usage"))
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        games = await smart_search_games(session, game_query, limit=10)

        if not games:
            await update.message.reply_text(t(lang, "compare_no_games", query=game_query))
            return

        all_lines = []
        seen_game_titles = set()

        for game in games:
            if game.title in seen_game_titles:
                continue
            seen_game_titles.add(game.title)

            result = await session.execute(
                select(ActiveDeal)
                .join(Game)
                .where(Game.title == game.title)
            )
            deals = result.scalars().all()

            if not deals:
                continue

            from services.exchange_rates import ExchangeRateService
            deals_with_ils = []
            for deal in deals:
                price_in_ils = await ExchangeRateService.convert_to_ils(float(deal.price), deal.currency)
                deals_with_ils.append((deal, price_in_ils))

            deals_with_ils.sort(key=lambda x: x[1])

            game_lines = [f"\n📊 <b>{game.title}</b>"]

            cheapest = deals_with_ils[0][0]
            regions_with_deals = {deal.region_code for deal, _ in deals_with_ils}

            for deal, price_ils in deals_with_ils:
                region_info = config.REGIONS.get(deal.region_code, {})
                flag = region_info.get("flag", "")
                name = region_info.get("name", deal.region_code)
                currency = region_info.get("currency", "USD")

                ils_suffix = f" (~{price_ils:.0f}₪)" if currency != "ILS" else ""
                marker = t(lang, "compare_cheapest") if deal == cheapest else ""
                game_lines.append(
                    f"{flag} <b>{name}:</b> {deal.price} {currency}{ils_suffix} "
                    f"(-{deal.discount_percent}%){marker}"
                )

            for region_code, region_info in config.REGIONS.items():
                if region_code not in regions_with_deals:
                    flag = region_info.get("flag", "")
                    name = region_info.get("name", region_code)
                    game_lines.append(
                        f"{flag} <b>{name}:</b> {t(lang, 'compare_no_deal')}"
                    )

            cheapest_info = config.REGIONS.get(cheapest.region_code, {})
            game_lines.append(
                t(lang, "compare_best",
                  flag=cheapest_info.get("flag", ""),
                  name=cheapest_info.get("name", ""))
            )

            best_store_url = cheapest_info.get("store_url", "")
            if best_store_url:
                store_link = f"{best_store_url}/search/{quote(game.title)}"
                game_lines.append(t(lang, "compare_buy", url=store_link))

            all_lines.extend(game_lines)

        if not all_lines:
            await update.message.reply_text(t(lang, "compare_no_deals", query=game_query))
            return

        header = t(lang, "compare_header", query=game_query)
        all_lines.insert(0, header)

    await update.message.reply_text("\n".join(all_lines), parse_mode="HTML")


compare_handler = CommandHandler("compare", _compare)
