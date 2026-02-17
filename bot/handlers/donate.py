import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


async def _donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /donate and /support - show donation options."""
    await update.message.reply_text(
        "💝 Support PS5 Deal Hunter!\n\n"
        "This bot is free for everyone. If it helped you\n"
        "find a great deal, consider supporting development:\n\n"
        "☕ Buy me a coffee:\n"
        "   https://buymeacoffee.com/oshri1997\n\n"
        "💳 PayPal:\n"
        "   https://paypal.me/<YOUR_PAYPAL_USERNAME>\n\n"
        "Every contribution helps keep the bot running\n"
        "and fund new features! 🙏"
    )


donate_handler = CommandHandler("donate", _donate)
support_handler = CommandHandler("support", _donate)
