import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user

logger = logging.getLogger(__name__)

WELCOME_MSG = (
    "🎮 *Welcome to PS5 Deal Hunter\\!*\n\n"
    "I track PlayStation Store deals across multiple regions "
    "and send you instant notifications when games go on sale\\.\n\n"
    "*Getting started:*\n"
    "1\\. Use /regions to choose your PSN store regions\n"
    "2\\. Use /deals to see current top deals\n"
    "3\\. Use /watch to track specific games\n\n"
    "*Commands:*\n"
    "/regions \\- Select your regions\n"
    "/deals \\- View current deals\n"
    "/watch \\<game\\> \\- Add game to wishlist\n"
    "/unwatch \\<game\\|number\\> \\- Remove from wishlist\n"
    "/watchlist \\- View your tracked games\n"
    "/compare \\<game\\> \\- Compare prices across regions\n"
    "/alert \\<game\\> \\<price\\|discount%\\> \\- Set price alert\n"
    "/alerts \\- View your active alerts\n"
    "/search \\<game\\> \\- Search for a game\n"
    "/check\\_amazon \\- Check PS gift card availability\n"
    "/settings \\- Your preferences\n"
    "/donate \\- Support the bot\n"
    "/help \\- Show this message\n\n"
    "🎉 *All features are free during beta\\!*\n"
    "Enjoy unlimited regions, real\\-time alerts, and price comparison\\."
)


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user = update.effective_user
    await get_or_create_user(user)
    logger.info(f"User {user.id} ({user.username}) started the bot")
    await update.message.reply_text(WELCOME_MSG, parse_mode="MarkdownV2")


async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    await update.message.reply_text(WELCOME_MSG, parse_mode="MarkdownV2")


start_handler = CommandHandler("start", _start)
help_handler = CommandHandler("help", _help)
