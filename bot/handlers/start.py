import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user

logger = logging.getLogger(__name__)

WELCOME_MSG = (
    # ── Hebrew ──────────────────────────────────────────────
    "🎮 <b>ברוכים הבאים ל-PS Deal Hunter!</b>\n\n"
    "הבוט עוקב אחרי מבצעים ב-PlayStation Store ממדינות שונות ושולח התראות בזמן אמת.\n\n"
    "<b>🚀 איך מתחילים:</b>\n"
    "1. בחר אזורים עם /regions\n"
    "2. צפה במבצעים עם /deals\n"
    "3. עקוב אחרי משחקים עם /watch\n"
    "💡 לא רוצה לקבל התראות על מבצעים? אין צורך לבחור אזור!\n\n"
    "<b>📋 פקודות:</b>\n"
    "/regions – בחר אזורי PSN\n"
    "/deals – מבצעים נוכחיים\n"
    "/watch &lt;משחק&gt; – הוסף לרשימת המשאלות\n"
    "/unwatch &lt;שם|מספר&gt; – הסר מהרשימה\n"
    "/watchlist – הרשימה שלך\n"
    "/compare &lt;משחק&gt; – השוואת מחירים בין אזורים\n"
    "/alert &lt;משחק&gt; &lt;מחיר|%&gt; – התראת מחיר\n"
    "/alerts – ההתראות הפעילות שלך\n"
    "/search &lt;משחק&gt; – חפש משחק\n"
    "/giftcard – זמינות גיפט קארד Amazon\n"
    "/follow – עדכונים על גיפט קארד\n"
    "/settings – הגדרות\n"
    "/donate – תמוך בפיתוח\n\n"
    "💝 <b>תמיכה בפיתוח:</b>\n"
    "הבוט חינמי! אם חסכת כסף, ניתן לתמוך בי:\n"
    "☕ <a href=\"https://buymeacoffee.com/oshri1997\">buymeacoffee.com/oshri1997</a>\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    # ── English ─────────────────────────────────────────────
    "🎮 <b>Welcome to PS Deal Hunter!</b>\n\n"
    "I track PlayStation Store deals across multiple regions and send real-time notifications.\n\n"
    "<b>🚀 Getting started:</b>\n"
    "1. Choose your regions with /regions\n"
    "2. Browse deals with /deals\n"
    "3. Track games with /watch\n"
    "💡 Don't want deal alerts? No need to select a region!\n\n"
    "<b>📋 Commands:</b>\n"
    "/regions – Select PSN regions\n"
    "/deals – Current deals\n"
    "/watch &lt;game&gt; – Add to wishlist\n"
    "/unwatch &lt;name|number&gt; – Remove from wishlist\n"
    "/watchlist – Your tracked games\n"
    "/compare &lt;game&gt; – Compare prices across regions\n"
    "/alert &lt;game&gt; &lt;price|%&gt; – Set price alert\n"
    "/alerts – Your active alerts\n"
    "/search &lt;game&gt; – Search for a game\n"
    "/giftcard – Check Amazon gift card availability\n"
    "/follow – Get gift card availability alerts\n"
    "/settings – Your preferences\n"
    "/donate – Support the bot\n\n"
    "💝 <b>Support development:</b>\n"
    "This bot is free for everyone. If it saved you money, consider supporting:\n"
    "☕ <a href=\"https://buymeacoffee.com/oshri1997\">buymeacoffee.com/oshri1997</a>\n\n"
    "🎉 <b>All features are free during beta!</b>"
)


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user = update.effective_user
    await get_or_create_user(user)
    logger.info(f"User {user.id} ({user.username}) started the bot")
    await update.message.reply_text(WELCOME_MSG, parse_mode="HTML")


async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    await update.message.reply_text(WELCOME_MSG, parse_mode="HTML")


start_handler = CommandHandler("start", _start)
help_handler = CommandHandler("help", _help)
