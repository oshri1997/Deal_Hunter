"""
/search command — search for games with online fallback.

Flow:
1. Search local DB (fast).
2. If results found → show numbered list + "send 0 to search online".
3. If no results → immediately search PSPrices online.
4. User picks a number → show details.
5. User sends 0 → scrape PSPrices, save new games to DB, show results.
"""

import logging
from urllib.parse import quote

from sqlalchemy import select
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.helpers import smart_search_games, format_price_ils, get_or_create_user, get_user_language
from bot.i18n import t
from config import config
from database.engine import get_session
from database.models import ActiveDeal, Game

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PICK = 0
WAITING_FOR_ONLINE_PICK = 1


# ------------------------------------------------------------------
# Entry point — /search <query>
# ------------------------------------------------------------------

async def _search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search DB first, offer online fallback."""
    user = update.effective_user
    lang = await get_user_language(user.id)
    context.user_data["search_lang"] = lang

    if not context.args:
        await update.message.reply_text(t(lang, "search_usage"))
        return ConversationHandler.END

    query = " ".join(context.args)
    context.user_data["search_query"] = query

    await update.message.reply_text(t(lang, "search_searching", query=query))

    _DLC_KEYWORDS = ("points", "dlc", "pack", "bundle", "currency", "coins")

    def _dlc_sort_key(g) -> int:
        return 1 if any(kw in g.title.lower() for kw in _DLC_KEYWORDS) else 0

    async with get_session() as session:
        games = await smart_search_games(session, query, limit=50)
        games = sorted(games, key=_dlc_sort_key)

        main_games = [g for g in games if _dlc_sort_key(g) == 0]
        if main_games:
            games = main_games

        if games:
            from bot.helpers import get_user_regions
            user_regions = await get_user_regions(user.id) or list(config.REGIONS.keys())
            message, flat_games = await _format_db_results(session, games, user_regions, lang)
            message += t(lang, "search_reply_num")
            context.user_data["search_db_games"] = flat_games
            await update.message.reply_text(message, parse_mode="HTML")
            return WAITING_FOR_PICK

    return await _do_online_search(update, context, query, lang)


# ------------------------------------------------------------------
# State: WAITING_FOR_PICK (DB results shown)
# ------------------------------------------------------------------

async def _handle_db_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user reply after DB results are shown."""
    lang = context.user_data.get("search_lang", "en")
    db_games = context.user_data.get("search_db_games")
    query = context.user_data.get("search_query", "")

    if not db_games:
        await update.message.reply_text(t(lang, "search_session_expired"))
        return ConversationHandler.END

    text = update.message.text.strip()

    try:
        pick = int(text)
    except ValueError:
        await update.message.reply_text(t(lang, "search_invalid_pick"))
        return WAITING_FOR_PICK

    if pick == 0:
        return await _do_online_search(update, context, query, lang)

    if pick < 1 or pick > len(db_games):
        await update.message.reply_text(t(lang, "search_pick_range", max=len(db_games)))
        return WAITING_FOR_PICK

    game_info = db_games[pick - 1]
    await _show_game_details(update, game_info["id"], game_info["title"], lang)
    _cleanup_context(context)
    return ConversationHandler.END


# ------------------------------------------------------------------
# State: WAITING_FOR_ONLINE_PICK (online results shown)
# ------------------------------------------------------------------

async def _handle_online_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user reply after online results are shown."""
    lang = context.user_data.get("search_lang", "en")
    title_list = context.user_data.get("search_online_results")

    if not title_list:
        await update.message.reply_text(t(lang, "search_session_expired"))
        return ConversationHandler.END

    text = update.message.text.strip()

    try:
        pick = int(text)
    except ValueError:
        await update.message.reply_text(t(lang, "search_invalid_pick"))
        return WAITING_FOR_ONLINE_PICK

    if pick < 1 or pick > len(title_list):
        await update.message.reply_text(t(lang, "search_pick_range_online", max=len(title_list)))
        return WAITING_FOR_ONLINE_PICK

    title, platform, region_results = title_list[pick - 1]
    message = await _format_multi_region_result(title, platform, region_results, lang)
    await update.message.reply_text(message, parse_mode="HTML")
    _cleanup_context(context)
    return ConversationHandler.END


# ------------------------------------------------------------------
# Online search logic
# ------------------------------------------------------------------

async def _do_online_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    lang: str = "en",
):
    """Scrape PSPrices, save to DB, show results grouped by title."""
    await update.message.reply_text(t(lang, "search_online"))

    try:
        from scraper.psprices_search import PSPricesOnlineSearch
        from bot.helpers import get_user_regions

        user_regions = await get_user_regions(update.effective_user.id)
        if not user_regions:
            user_regions = list(config.REGIONS.keys())

        shared_cookies: dict = {}
        scheduler = context.bot_data.get("scheduler")
        if scheduler:
            psp = scheduler.scraper_manager.scraper
            if psp._scraper is not None:
                shared_cookies = dict(psp._scraper.cookies)
                logger.debug(
                    f"[Search] Borrowed {len(shared_cookies)} CF cookies "
                    "from live PSPricesScraper session"
                )

        searcher = PSPricesOnlineSearch(shared_cookies=shared_cookies)
        results = await searcher.search(query, region_codes=user_regions)
    except Exception as e:
        logger.error(f"Online search failed: {e}", exc_info=True)
        await update.message.reply_text(t(lang, "search_online_failed"))
        _cleanup_context(context)
        return ConversationHandler.END

    if not results:
        await update.message.reply_text(t(lang, "search_no_results", query=query))
        _cleanup_context(context)
        return ConversationHandler.END

    saved_count = await _save_results_to_db(results)
    logger.info(f"Saved {saved_count} new games to DB from online search")

    grouped: dict[str, list] = {}
    order: list[str] = []
    for r in results:
        norm = r.title.lower().strip()
        if norm not in grouped:
            grouped[norm] = []
            order.append(norm)
        grouped[norm].append(r)

    title_list = [
        (grouped[n][0].title, grouped[n][0].platform or "", grouped[n])
        for n in order
    ]

    if len(title_list) == 1:
        title, platform, region_results = title_list[0]
        message = await _format_multi_region_result(title, platform, region_results, lang)
        await update.message.reply_text(message, parse_mode="HTML")
        _cleanup_context(context)
        return ConversationHandler.END

    lines = [t(lang, "search_online_found", n=len(title_list))]
    for i, (title, platform, region_results) in enumerate(title_list, 1):
        plat = f" [{platform}]" if platform else ""
        best_discount = max(
            (r.discount_percent for r in region_results if r.discount_percent),
            default=None,
        )
        deal_info = f" — 🔥 -{best_discount}%" if best_discount else ""
        lines.append(f"<b>{i}.</b> {title}{plat}{deal_info}")

    lines.append(t(lang, "search_online_pick"))

    context.user_data["search_online_results"] = title_list
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return WAITING_FOR_ONLINE_PICK


# ------------------------------------------------------------------
# Cancel
# ------------------------------------------------------------------

async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel during search."""
    lang = context.user_data.get("search_lang", "en")
    _cleanup_context(context)
    await update.message.reply_text(t(lang, "search_cancelled"))
    return ConversationHandler.END


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _cleanup_context(context: ContextTypes.DEFAULT_TYPE):
    """Remove search-related data from user_data."""
    for key in ("search_query", "search_db_games", "search_online_results", "search_lang"):
        context.user_data.pop(key, None)


async def _format_db_results(
    session, games: list[Game], user_regions: list[str] | None = None, lang: str = "en"
) -> tuple[str, list[dict]]:
    """Format games grouped by region with prices."""
    MAX_LEN = 3100

    regions: dict[str, list[tuple]] = {}
    no_price_games: list[Game] = []
    seen_no_price: set[str] = set()

    for game in games:
        deal_result = await session.execute(
            select(ActiveDeal).where(ActiveDeal.game_id == game.id)
        )
        deals = deal_result.scalars().all()

        if deals:
            for deal in deals:
                rc = deal.region_code
                if rc not in regions:
                    regions[rc] = []
                regions[rc].append((game, deal))
        else:
            if game.title not in seen_no_price:
                no_price_games.append(game)
                seen_no_price.add(game.title)

    flat_games: list[dict] = []
    lines: list[str] = []
    counter = 1
    truncated = False

    def _current_len() -> int:
        return sum(len(l) + 1 for l in lines)

    for region_code, game_deals in regions.items():
        if truncated:
            break
        if user_regions and region_code not in user_regions:
            continue

        region_info = config.REGIONS.get(region_code, {})
        flag = region_info.get("flag", "")
        region_name = region_info.get("name", region_code)
        store_url = region_info.get("store_url", "")

        game_deals.sort(
            key=lambda x: (0 if (x[1].discount_percent or 0) > 0 else 1,
                           x[0].title.lower())
        )

        region_header = f"\n{flag} <b>{region_name}</b>"
        region_lines: list[str] = [region_header]
        region_games: list[dict] = []

        for game, deal in game_deals[:10]:
            psn_link = f"{store_url}/search/{quote(game.title)}" if store_url else ""
            price = float(deal.price)
            currency = deal.currency or "USD"
            ils_suffix = await format_price_ils(price, currency)
            disc = deal.discount_percent or 0

            if disc > 0:
                price_line = (
                    f"💰 {deal.price} {currency}{ils_suffix} "
                    f"(was {deal.original_price}) -<b>{disc}%</b>"
                )
                label = f"<b>{counter}.</b> 🔥 {game.title}"
            elif price > 0:
                price_line = f"💰 {deal.price} {currency}{ils_suffix}"
                label = f"<b>{counter}.</b> {game.title}"
            else:
                price_line = t(lang, "search_no_price")
                label = f"<b>{counter}.</b> {game.title}"

            entry = f"{label}\n    {price_line}"
            if psn_link:
                entry += f"\n    🛒 <a href='{psn_link}'>PS Store</a>"

            candidate_len = _current_len() + sum(len(l) + 1 for l in region_lines) + len(entry)
            if candidate_len > MAX_LEN:
                truncated = True
                break

            region_lines.append(entry)
            region_games.append({"id": game.id, "title": game.title})
            counter += 1

        if region_games:
            lines.extend(region_lines)
            flat_games.extend(region_games)

    for game in no_price_games:
        if truncated:
            break
        entry = f"\n<b>{counter}.</b> ⚪ {game.title} — {t(lang, 'search_no_price')}"
        if _current_len() + len(entry) > MAX_LEN:
            truncated = True
            break
        lines.append(entry)
        flat_games.append({"id": game.id, "title": game.title})
        counter += 1

    if truncated:
        lines.append(t(lang, "search_more"))

    header = t(lang, "search_found", n=len(flat_games))
    message = header + "\n".join(lines)
    return message, flat_games


async def _show_game_details(update: Update, game_id: str, title: str, lang: str = "en"):
    """Show detailed info for a DB game."""
    async with get_session() as session:
        deal_result = await session.execute(
            select(ActiveDeal).where(ActiveDeal.game_id == game_id)
        )
        deals = deal_result.scalars().all()

        lines = [f"🎮 <b>{title}</b>\n"]

        if deals:
            for deal in deals:
                region_info = config.REGIONS.get(deal.region_code, {})
                flag = region_info.get("flag", "")
                region_name = region_info.get("name", deal.region_code)
                currency = deal.currency or region_info.get("currency", "USD")
                store_url = region_info.get("store_url", "")

                ils_suffix = await format_price_ils(float(deal.price), currency)
                psn_link = f"{store_url}/search/{quote(title)}" if store_url else ""
                disc = deal.discount_percent or 0

                if disc > 0:
                    price_line = (
                        f"💰 {deal.price} {currency}{ils_suffix} "
                        f"(was {deal.original_price}) — <b>{disc}% OFF</b>"
                    )
                else:
                    price_line = f"💰 {deal.price} {currency}{ils_suffix}"

                lines.append(
                    f"{flag} <b>{region_name}:</b>\n"
                    f"{price_line}\n"
                    f"🛒 <a href='{psn_link}'>PS Store</a>\n"
                )
        else:
            lines.append(t(lang, "search_no_price_available") + "\n")

        lines.append(t(lang, "search_watch_tip", title=title))

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def _format_multi_region_result(
    title: str, platform: str, region_results: list, lang: str = "en"
) -> str:
    """Format a game with prices for every region the user follows."""
    lines = [f"🎮 <b>{title}</b>"]
    if platform:
        lines.append(f"🕹 {platform}")
    lines.append("")

    for r in region_results:
        region_info = config.REGIONS.get(r.region_code, {})
        flag = region_info.get("flag", "")
        region_name = region_info.get("name", r.region_code)
        store_url = region_info.get("store_url", "")
        psn_link = f"{store_url}/search/{quote(title)}" if store_url else ""

        lines.append(f"{flag} <b>{region_name}</b>")

        if r.price is not None:
            if r.price == 0.0:
                lines.append(t(lang, "search_free"))
            else:
                ils_suffix = await format_price_ils(float(r.price), r.currency)
                price_line = f"💰 {r.price} {r.currency}{ils_suffix}"
                if r.original_price and r.discount_percent:
                    price_line += f" (was {r.original_price}) — <b>-{r.discount_percent}%</b>"
                lines.append(price_line)
        else:
            lines.append(t(lang, "search_no_active_deal"))

        if psn_link:
            lines.append(f"🛒 <a href='{psn_link}'>PS Store</a>")
        lines.append("")

    lines.append(t(lang, "search_watch_tip", title=title))
    return "\n".join(lines)


async def _save_results_to_db(results) -> int:
    """Save online search results to DB. Returns count of new games."""
    saved = 0
    async with get_session() as session:
        for r in results:
            existing = await session.get(Game, r.game_id)
            if not existing:
                game = Game(
                    id=r.game_id,
                    title=r.title,
                    cover_url=r.cover_url,
                    platform=r.platform,
                )
                session.add(game)
                saved += 1
            elif r.cover_url and not existing.cover_url:
                existing.cover_url = r.cover_url

            if r.price is not None:
                existing_deal_result = await session.execute(
                    select(ActiveDeal).where(
                        ActiveDeal.game_id == r.game_id,
                        ActiveDeal.region_code == r.region_code,
                    )
                )
                existing_deal = existing_deal_result.scalar_one_or_none()

                if not existing_deal:
                    deal = ActiveDeal(
                        game_id=r.game_id,
                        region_code=r.region_code,
                        price=r.price,
                        original_price=r.original_price or r.price,
                        discount_percent=r.discount_percent or 0,
                        currency=r.currency,
                        page_number=0,
                        position_on_page=0,
                    )
                    session.add(deal)
                else:
                    existing_deal.price = r.price
                    existing_deal.original_price = r.original_price or r.price
                    existing_deal.discount_percent = r.discount_percent or 0
                    existing_deal.currency = r.currency

        await session.commit()
    return saved


# ------------------------------------------------------------------
# Handler registration
# ------------------------------------------------------------------

search_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("search", _search)],
    states={
        WAITING_FOR_PICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_db_pick),
            CommandHandler("cancel", _cancel),
        ],
        WAITING_FOR_ONLINE_PICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_online_pick),
            CommandHandler("cancel", _cancel),
        ],
    },
    fallbacks=[CommandHandler("cancel", _cancel)],
    allow_reentry=True,
)

search_handler = search_conv_handler
