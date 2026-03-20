import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_user_language
from bot.i18n import t

logger = logging.getLogger(__name__)


async def _donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /donate and /support - show donation options."""
    lang = await get_user_language(update.effective_user.id)
    await update.message.reply_text(t(lang, "donate_msg"))


donate_handler = CommandHandler("donate", _donate)
support_handler = CommandHandler("support", _donate)
