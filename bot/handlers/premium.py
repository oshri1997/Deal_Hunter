from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def _premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium/subscription info."""
    await update.message.reply_text(
        "🔔 <b>PS Deal Hunter — Premium</b>\n\n"
        "<b>Subscribers get:</b>\n"
        "• ⭐ Daily deal alerts to your chat\n"
        "• ⭐ Price drop notifications\n"
        "• ⭐ Gift card stock alerts (/follow)\n"
        "• ⭐ Cross-region price comparison (/compare)\n"
        "• ⭐ Price alerts (/alert)\n\n"
        "<b>Free for everyone:</b>\n"
        "• 🔍 Search &amp; browse deals\n"
        "• 📋 Wishlist\n"
        "• 🎮 Check gift card availability\n\n"
        "Use /subscribe to get started!\n"
        "Use /status to check your subscription.",
        parse_mode="HTML",
    )


premium_handler = CommandHandler("premium", _premium)
