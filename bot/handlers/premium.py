from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def _premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium info - currently all features are free during beta."""
    await update.message.reply_text(
        "🎉 All Features Are Free!\n\n"
        "During our beta period, every feature is available to all users:\n"
        "• ✅ Unlimited regions\n"
        "• ✅ Real-time instant alerts\n"
        "• ✅ Unlimited wishlist\n"
        "• ✅ Cross-region price comparison\n"
        "• ✅ Price alerts for specific games\n\n"
        "Premium plans with exclusive features are coming soon!\n\n"
        "💝 Want to support the bot? Use /donate"
    )


premium_handler = CommandHandler("premium", _premium)
