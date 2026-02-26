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

from bot.helpers import smart_search_games, format_price_ils, get_or_create_user
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
    if not context.args:
        await update.message.reply_text(
            "Usage: /search <game name>\nExample: /search Spider-Man"
        )
        return ConversationHandler.END

    query = " ".join(context.args)
    context.user_data["search_query"] = query

    await update.message.reply_text(f"🔍 Searching for '{query}'...")

    # --- DB search ---
    _DLC_KEYWORDS = ("points", "dlc", "pack", "bundle", "currency", "coins")

    def _dlc_sort_key(g) -> int:
        return 1 if any(kw in g.title.lower() for kw in _DLC_KEYWORDS) else 0

    async with get_session() as session:
        games = await smart_search_games(session, query, limit=50)
        games = sorted(games, key=_dlc_sort_key)  # main games first

        # Filter out DLC / Points packs — show only main game editions by default
        main_games = [g for g in games if _dlc_sort_key(g) == 0]
        if main_games:
            games = main_games

        if games:
            message = await _format_db_results(session, games)
            message += (
                "\n\n📝 Reply with a <b>number</b> to see details.\n"
                "🌐 Didn't find your game? Send <b>0</b> to search online."
            )
            context.user_data["search_db_games"] = [
                {"id": g.id, "title": g.title} for g in games
            ]
            await update.message.reply_text(message, parse_mode="HTML")
            return WAITING_FOR_PICK

    # --- No DB results → go online immediately ---
    return await _do_online_search(update, context, query)


# ------------------------------------------------------------------
# State: WAITING_FOR_PICK (DB results shown)
# ------------------------------------------------------------------

async def _handle_db_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user reply after DB results are shown."""
    db_games = context.user_data.get("search_db_games")
    query = context.user_data.get("search_query", "")

    if not db_games:
        await update.message.reply_text("⚠️ Session expired. Use /search again.")
        return ConversationHandler.END

    text = update.message.text.strip()

    try:
        pick = int(text)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please reply with a number, or /cancel to stop."
        )
        return WAITING_FOR_PICK

    # User sends 0 → online search
    if pick == 0:
        return await _do_online_search(update, context, query)

    if pick < 1 or pick > len(db_games):
        await update.message.reply_text(
            f"⚠️ Pick a number between 1 and {len(db_games)}, or 0 for online search."
        )
        return WAITING_FOR_PICK

    # Show details for the picked game
    game_info = db_games[pick - 1]
    await _show_game_details(update, game_info["id"], game_info["title"])
    _cleanup_context(context)
    return ConversationHandler.END


# ------------------------------------------------------------------
# State: WAITING_FOR_ONLINE_PICK (online results shown)
# ------------------------------------------------------------------

async def _handle_online_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user reply after online results are shown."""
    title_list = context.user_data.get("search_online_results")

    if not title_list:
        await update.message.reply_text("⚠️ Session expired. Use /search again.")
        return ConversationHandler.END

    text = update.message.text.strip()

    try:
        pick = int(text)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please reply with a number, or /cancel to stop."
        )
        return WAITING_FOR_ONLINE_PICK

    if pick < 1 or pick > len(title_list):
        await update.message.reply_text(
            f"⚠️ Pick a number between 1 and {len(title_list)}."
        )
        return WAITING_FOR_ONLINE_PICK

    title, platform, region_results = title_list[pick - 1]
    message = await _format_multi_region_result(title, platform, region_results)
    await update.message.reply_text(message, parse_mode="HTML")
    _cleanup_context(context)
    return ConversationHandler.END


# ------------------------------------------------------------------
# Online search logic
# ------------------------------------------------------------------

async def _do_online_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Scrape PSPrices, save to DB, show results grouped by title."""
    await update.message.reply_text("🌐 Searching online...")

    try:
        from scraper.psprices_search import PSPricesOnlineSearch
        from bot.helpers import get_user_regions

        user_regions = await get_user_regions(update.effective_user.id)
        if not user_regions:
            user_regions = list(config.REGIONS.keys())

        searcher = PSPricesOnlineSearch()
        # Get all results across all user regions (no dedup)
        results = await searcher.search(query, region_codes=user_regions)
    except Exception as e:
        logger.error(f"Online search failed: {e}", exc_info=True)
        await update.message.reply_text("❌ Online search failed. Try again later.")
        _cleanup_context(context)
        return ConversationHandler.END

    if not results:
        await update.message.reply_text(
            f"❌ No games found matching '{query}' on PSPrices either."
        )
        _cleanup_context(context)
        return ConversationHandler.END

    # Save all results to DB
    saved_count = await _save_results_to_db(results)
    logger.info(f"Saved {saved_count} new games to DB from online search")

    # Group by normalized title: {norm_title: [SearchResult, ...]}
    grouped: dict[str, list] = {}
    order: list[str] = []
    for r in results:
        norm = r.title.lower().strip()
        if norm not in grouped:
            grouped[norm] = []
            order.append(norm)
        grouped[norm].append(r)

    # Build indexed list: [(display_title, platform, [SearchResult, ...])]
    title_list = [
        (grouped[n][0].title, grouped[n][0].platform or "", grouped[n])
        for n in order
    ]

    # Single unique title → show directly
    if len(title_list) == 1:
        title, platform, region_results = title_list[0]
        message = await _format_multi_region_result(title, platform, region_results)
        await update.message.reply_text(message, parse_mode="HTML")
        _cleanup_context(context)
        return ConversationHandler.END

    # Multiple titles → show numbered list with best deal indicator
    lines = [f"🌐 Found {len(title_list)} games on PSPrices:\n"]
    for i, (title, platform, region_results) in enumerate(title_list, 1):
        plat = f" [{platform}]" if platform else ""
        best_discount = max(
            (r.discount_percent for r in region_results if r.discount_percent),
            default=None,
        )
        deal_info = f" — 🔥 -{best_discount}%" if best_discount else ""
        lines.append(f"<b>{i}.</b> {title}{plat}{deal_info}")

    lines.append("\n📝 Reply with a <b>number</b> to see details, or /cancel to stop.")

    context.user_data["search_online_results"] = title_list
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return WAITING_FOR_ONLINE_PICK


# ------------------------------------------------------------------
# Cancel
# ------------------------------------------------------------------

async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel during search."""
    _cleanup_context(context)
    await update.message.reply_text("🔍 Search cancelled.")
    return ConversationHandler.END


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _cleanup_context(context: ContextTypes.DEFAULT_TYPE):
    """Remove search-related data from user_data."""
    for key in ("search_query", "search_db_games", "search_online_results"):
        context.user_data.pop(key, None)


async def _format_db_results(session, games: list[Game]) -> str:
    """Format games found in the local DB with deal info."""
    lines = [f"🎮 Found {len(games)} game(s):\n"]

    for i, game in enumerate(games, 1):
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
                lines.append(
                    f"<b>{i}.</b> 🔥 {flag} {game.title}\n"
                    f"    💰 {deal.price} {currency}{ils_suffix} "
                    f"(was {deal.original_price}) -{deal.discount_percent}%\n"
                    f"    🛒 <a href='{psn_link}'>PS Store</a>\n"
                )
        else:
            lines.append(f"<b>{i}.</b> ⚪ {game.title} — No active deals\n")

    message = "\n".join(lines)
    if len(message) > 3800:
        message = message[:3790] + "\n..."
    return message


async def _show_game_details(update: Update, game_id: str, title: str):
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
                currency = region_info.get("currency", "USD")
                store_url = region_info.get("store_url", "")

                ils_suffix = await format_price_ils(float(deal.price), currency)
                psn_link = f"{store_url}/search/{quote(title)}" if store_url else ""

                lines.append(
                    f"{flag} <b>{region_name}:</b>\n"
                    f"💰 {deal.price} {currency}{ils_suffix} "
                    f"(was {deal.original_price}) — <b>{deal.discount_percent}% OFF</b>\n"
                    f"🛒 <a href='{psn_link}'>PS Store</a>\n"
                )
        else:
            lines.append("💰 No active deals at the moment.\n")

        lines.append(f"💡 Use <code>/watch {title}</code> to track this game!")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def _format_multi_region_result(title: str, platform: str, region_results: list) -> str:
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
                lines.append("💰 Free")
            else:
                ils_suffix = await format_price_ils(float(r.price), r.currency)
                price_line = f"💰 {r.price} {r.currency}{ils_suffix}"
                if r.original_price and r.discount_percent:
                    price_line += f" (was {r.original_price}) — <b>-{r.discount_percent}%</b>"
                lines.append(price_line)
        else:
            lines.append("💰 No active deal")

        if psn_link:
            lines.append(f"🛒 <a href='{psn_link}'>PS Store</a>")
        lines.append("")

    lines.append(f"💡 Use <code>/watch {title}</code> to track this game!")
    return "\n".join(lines)


async def _save_results_to_db(results) -> int:
    """Save online search results to DB. Returns count of new games."""
    saved = 0
    async with get_session() as session:
        for r in results:
            # Check if game already exists (no duplicates)
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

            # Save deal if exists (no duplicates)
            if r.price is not None and r.discount_percent and r.discount_percent > 0:
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
                        page_number=0,       # 0 = from search, not from scrape
                        position_on_page=0,
                    )
                    session.add(deal)

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

# Backward-compatible alias — drop-in replacement in main.py
search_handler = search_conv_handler
