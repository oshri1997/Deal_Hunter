from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def _premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium/subscription info."""
    await update.message.reply_text(
        "🔔 <b>PS Deal Hunter — Premium</b>\n\n"
        "Subscribers get:\n"
        "• ✅ Real-time deal alerts\n"
        "• ✅ Price drop notifications\n"
        "• ✅ Gift card stock alerts (/follow)\n"
        "• ✅ Unlimited wishlist &amp; regions\n"
        "• ✅ Cross-region price comparison\n\n"
        "Free features (no subscription needed):\n"
        "• 🔍 Search, browse deals, compare prices\n"
        "• 📋 Wishlist &amp; price alerts setup\n\n"
        "Use /subscribe to get started!\n"
        "Use /status to check your subscription.",
        parse_mode="HTML",
    )


premium_handler = CommandHandler("premium", _premium)
