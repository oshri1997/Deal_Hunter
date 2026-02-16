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
        await session.commit()

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
            "\u2139\ufe0f *Usage:* `/unwatch Game Title` or `/unwatch <number>`\n"
            "Example: `/unwatch God of War` or `/unwatch 1`",
            parse_mode="MarkdownV2",
        )
        return

    game_query = " ".join(context.args).strip()

    async with get_session() as session:
        # Check if it's a number (index)
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
                    f"\u26a0\ufe0f Invalid number\\. Use `/watchlist` to see your games\\.",
                    parse_mode="MarkdownV2",
                )
                return
            
            entry = entries[index]
            game = await session.get(Game, entry.game_id)
            title = game.title if game else entry.game_id
            await session.delete(entry)
            await session.commit()
            
            await update.message.reply_text(
                f"\u274c Removed *{_escape_md(title)}* from your watchlist\\.",
                parse_mode="MarkdownV2",
            )
            return
        
        # Search by game title or game_id
        result = await session.execute(
            select(UserWishlist, Game)
            .join(Game, UserWishlist.game_id == Game.id)
            .where(
                UserWishlist.user_id == user.id,
            )
        )
        entries = result.all()
        
        # Find matching entry
        matched_entry = None
        for wishlist_entry, game in entries:
            if (game_query.lower() in game.title.lower() or 
                game_query.lower() in game.id.lower()):
                matched_entry = wishlist_entry
                matched_game = game
                break
        
        if not matched_entry:
            await update.message.reply_text(
                f"\u26a0\ufe0f *{_escape_md(game_query)}* is not on your watchlist\\.",
                parse_mode="MarkdownV2",
            )
            return

        await session.delete(matched_entry)
        await session.commit()

    await update.message.reply_text(
        f"\u274c Removed *{_escape_md(matched_game.title)}* from your watchlist\\.",
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
            # Show index number for easy removal
            lines.append(f"{i}\\. \U0001f3ae {_escape_md(title)}")

        lines.append(f"\n\U0001f4e6 {len(entries)} game\\(s\\) tracked")
        lines.append(f"\n\u2139\ufe0f Use `/unwatch <number>` or `/unwatch <game name>` to remove")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


watch_handler = CommandHandler("watch", _watch)
unwatch_handler = CommandHandler("unwatch", _unwatch)
watchlist_handler = CommandHandler("watchlist", _watchlist)
