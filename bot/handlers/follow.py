import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_language, require_subscriber
from bot.i18n import t
from database.engine import get_session
from database.models import User

logger = logging.getLogger(__name__)


async def _follow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /follow - toggle gift card availability notifications."""
    tg_user = update.effective_user
    await get_or_create_user(tg_user)
    lang = await get_user_language(tg_user.id)

    if not await require_subscriber(update):
        return

    async with get_session() as session:
        user = await session.get(User, tg_user.id)
        user.is_following = not user.is_following
        is_now_following = user.is_following

    if is_now_following:
        await update.message.reply_text(t(lang, "follow_on"), parse_mode="HTML")
    else:
        await update.message.reply_text(t(lang, "follow_off"), parse_mode="HTML")


follow_handler = CommandHandler("follow", _follow)
