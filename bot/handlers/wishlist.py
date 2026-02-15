import logging

from sqlalchemy import delete, select
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, _escape_md
from database.engine import get_session
from database.models import Game, UserWishlist

logger = logging.getLogger(__name__)


async def _watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watch <game> — add a game to the user's wishlist."""
    user = update.effective_user
    db_user = await get_or_create_user(user)

    if not context.args:
        await update.message.reply_text(
            "\u2139\ufe0f *Usage:* `/watch Game Title`\n"
            "Example: `/watch God of War Ragnarok`",
            parse_mode="MarkdownV2",
        )
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        # Search for the game in our database
        result = await session.execute(
            select(Game).where(Game.title.ilike(f"%{game_query}%")).limit(1)
        )
        game = result.scalar_one_or_none()

        if not game:
            # Create a placeholder game entry
            game_id = f"search_{game_query.lower().replace(' ', '_')[:50]}"
            game = Game(id=game_id, title=game_query, platform="PS5")
            session.add(game)
            await session.flush()

        # Check if already watching
        result = await session.execute(
            select(UserWishlist).where(
                UserWishlist.user_id == user.id,
                UserWishlist.game_id == game.id,
            )
        )
        if result.scalar_one_or_none():
            await update.message.reply_text(
                f"\u2139\ufe0f *{_escape_md(game.title)}* is already on your watchlist\\!",
                parse_mode="MarkdownV2",
            )
            return

        session.add(UserWishlist(user_id=user.id, game_id=game.id))

    await update.message.reply_text(
        f"\u2705 Added *{_escape_md(game.title)}* to your watchlist\\!\n"
        "You'll be notified when it goes on sale\\.",
        parse_mode="MarkdownV2",
    )


async def _unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unwatch <game> — remove a game from the wishlist."""
    user = update.effective_user
    await get_or_create_user(user)

    if not context.args:
        await update.message.reply_text(
            "\u2139\ufe0f *Usage:* `/unwatch Game Title`",
            parse_mode="MarkdownV2",
        )
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        # Find matching wishlist entries
        result = await session.execute(
            select(UserWishlist)
            .join(Game)
            .where(
                UserWishlist.user_id == user.id,
                Game.title.ilike(f"%{game_query}%"),
            )
        )
        entry = result.scalar_one_or_none()

        if not entry:
            await update.message.reply_text(
                f"\u26a0\ufe0f *{_escape_md(game_query)}* is not on your watchlist\\.",
                parse_mode="MarkdownV2",
            )
            return

        # Get title before deleting
        game = await session.get(Game, entry.game_id)
        title = game.title if game else game_query
        await session.delete(entry)

    await update.message.reply_text(
        f"\u274c Removed *{_escape_md(title)}* from your watchlist\\.",
        parse_mode="MarkdownV2",
    )


async def _watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watchlist — show all tracked games."""
    user = update.effective_user
    await get_or_create_user(user)

    async with get_session() as session:
        result = await session.execute(
            select(UserWishlist)
            .where(UserWishlist.user_id == user.id)
            .order_by(UserWishlist.added_at.desc())
        )
        entries = result.scalars().all()

        if not entries:
            await update.message.reply_text(
                "\U0001f4cb *Your watchlist is empty\\.*\n"
                "Use `/watch Game Title` to start tracking games\\!",
                parse_mode="MarkdownV2",
            )
            return

        lines = ["\U0001f4cb *Your Watchlist:*\n"]
        for i, entry in enumerate(entries, 1):
            game = await session.get(Game, entry.game_id)
            title = game.title if game else entry.game_id
            lines.append(f"{i}\\. \U0001f3ae {_escape_md(title)}")

        lines.append(f"\n\U0001f4e6 {len(entries)} game\\(s\\) tracked")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


watch_handler = CommandHandler("watch", _watch)
unwatch_handler = CommandHandler("unwatch", _unwatch)
watchlist_handler = CommandHandler("watchlist", _watchlist)
