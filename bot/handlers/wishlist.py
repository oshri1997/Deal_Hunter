import logging

from sqlalchemy import delete, select
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_language, _escape_md, smart_search_games, _words_match
from bot.i18n import t
from database.engine import get_session
from database.models import Game, UserWishlist

logger = logging.getLogger(__name__)


async def _watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watch <game> — add a game to the user's wishlist."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "watch_usage"), parse_mode="MarkdownV2")
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        games = await smart_search_games(session, game_query, limit=5)
        game = games[0] if games else None

        if not game:
            game_id = f"search_{game_query.lower().replace(' ', '_')[:50]}"
            game = Game(id=game_id, title=game_query, platform="PS5")
            session.add(game)
            await session.flush()

        result = await session.execute(
            select(UserWishlist).where(
                UserWishlist.user_id == user.id,
                UserWishlist.game_id == game.id,
            )
        )
        if result.scalar_one_or_none():
            await update.message.reply_text(
                t(lang, "watch_already", title=_escape_md(game.title)),
                parse_mode="MarkdownV2",
            )
            return

        session.add(UserWishlist(user_id=user.id, game_id=game.id))
        await session.commit()

    await update.message.reply_text(
        t(lang, "watch_added", title=_escape_md(game.title)),
        parse_mode="MarkdownV2",
    )


async def _unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unwatch <game> — remove a game from the wishlist."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "unwatch_usage"), parse_mode="MarkdownV2")
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        if game_query.isdigit():
            index = int(game_query) - 1
            result = await session.execute(
                select(UserWishlist)
                .where(UserWishlist.user_id == user.id)
                .order_by(UserWishlist.added_at.desc())
            )
            entries = result.scalars().all()

            if index < 0 or index >= len(entries):
                await update.message.reply_text(
                    t(lang, "unwatch_invalid_num"),
                    parse_mode="MarkdownV2",
                )
                return

            entry = entries[index]
            game = await session.get(Game, entry.game_id)
            title = game.title if game else entry.game_id
            await session.delete(entry)
            await session.commit()

            await update.message.reply_text(
                t(lang, "unwatch_removed", title=_escape_md(title)),
                parse_mode="MarkdownV2",
            )
            return

        result = await session.execute(
            select(UserWishlist, Game)
            .join(Game, UserWishlist.game_id == Game.id)
            .where(UserWishlist.user_id == user.id)
        )
        entries = result.all()

        matched_entry = None
        matched_game = None
        for wishlist_entry, game in entries:
            if _words_match(game_query, game.title) or game_query.lower() in game.id.lower():
                matched_entry = wishlist_entry
                matched_game = game
                break

        if not matched_entry:
            await update.message.reply_text(
                t(lang, "unwatch_not_found", title=_escape_md(game_query)),
                parse_mode="MarkdownV2",
            )
            return

        await session.delete(matched_entry)
        await session.commit()

    await update.message.reply_text(
        t(lang, "unwatch_removed", title=_escape_md(matched_game.title)),
        parse_mode="MarkdownV2",
    )


async def _watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watchlist — show all tracked games."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

    async with get_session() as session:
        result = await session.execute(
            select(UserWishlist)
            .where(UserWishlist.user_id == user.id)
            .order_by(UserWishlist.added_at.desc())
        )
        entries = result.scalars().all()

        if not entries:
            await update.message.reply_text(
                t(lang, "watchlist_empty"),
                parse_mode="MarkdownV2",
            )
            return

        lines = [t(lang, "watchlist_header")]
        for i, entry in enumerate(entries, 1):
            game = await session.get(Game, entry.game_id)
            title = game.title if game else entry.game_id
            lines.append(f"{i}\\. \U0001f3ae {_escape_md(title)}")

        lines.append(f"\n{t(lang, 'watchlist_count', n=len(entries))}")
        lines.append(f"\n{t(lang, 'watchlist_tip')}")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


watch_handler = CommandHandler("watch", _watch)
unwatch_handler = CommandHandler("unwatch", _unwatch)
watchlist_handler = CommandHandler("watchlist", _watchlist)
