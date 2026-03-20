from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_user_language
from bot.i18n import t


async def _premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium/subscription info."""
    lang = await get_user_language(update.effective_user.id)
    await update.message.reply_text(t(lang, "premium_msg"), parse_mode="HTML")


premium_handler = CommandHandler("premium", _premium)
