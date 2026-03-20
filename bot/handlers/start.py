import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_language, set_user_language
from bot.i18n import t

logger = logging.getLogger(__name__)


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
        InlineKeyboardButton("🇮🇱 עברית", callback_data="lang:he"),
    ]])


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — show language picker for new users, welcome for returning ones."""
    user = update.effective_user
    db_user = await get_or_create_user(user)
    logger.info(f"User {user.id} ({user.username}) started the bot")

    if db_user.language:
        # Returning user — show welcome in their language directly
        await update.message.reply_text(t(db_user.language, "welcome"), parse_mode="HTML")
    else:
        # New user — ask for language
        await update.message.reply_text(
            t("en", "choose_language"),
            parse_mode="HTML",
            reply_markup=_lang_keyboard(),
        )


async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help — show welcome message in user's language."""
    lang = await get_user_language(update.effective_user.id)
    await update.message.reply_text(t(lang, "welcome"), parse_mode="HTML")


async def _language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language — show language picker to change language."""
    lang = await get_user_language(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "choose_language"),
        parse_mode="HTML",
        reply_markup=_lang_keyboard(),
    )


async def _language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection inline button."""
    query = update.callback_query
    await query.answer()

    data = query.data  # "lang:en" or "lang:he"
    if not data.startswith("lang:"):
        return

    lang = data.split(":", 1)[1]
    if lang not in ("en", "he"):
        return

    user_id = query.from_user.id
    await set_user_language(user_id, lang)

    # Replace the picker with the full welcome message
    await query.edit_message_text(t(lang, "welcome"), parse_mode="HTML")


start_handler = CommandHandler("start", _start)
help_handler = CommandHandler("help", _help)
language_handler = CommandHandler("language", _language)
language_callback_handler = CallbackQueryHandler(_language_callback, pattern=r"^lang:")
