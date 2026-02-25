import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user

logger = logging.getLogger(__name__)

WELCOME_MSG = (
    "🎮 <b>ברוכים הבאים ל-PS Deal Hunter!</b>\n\n"
    "הבוט עוקב אחרי מבצעים ב-PlayStation Store ממדינות שונות "
    "ושולח לך התראות בזמן אמת כשמשחקים יורדים במחיר.\n\n"
    "<b>🚀 איך מתחילים:</b>\n"
    "1. בחר את אזורי ה-PSN שלך עם /regions\n"
    "2. צפה במבצעים הנוכחיים עם /deals\n"
    "3. עקוב אחרי משחקים ספציפיים עם /watch\n\n"
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
    "/giftcard – בדוק זמינות גיפט קארד של Amazon\n"
    "/follow – קבל עדכון כשהגיפט קארד זמין\n"
    "/settings – הגדרות אישיות\n"
    "/donate – תמוך בפיתוח\n"
    "/help – הצג הודעה זו\n\n"
    "💝 <b>תמיכה בפיתוח:</b>\n"
    "הבוט חינמי לחלוטין לכולם! אם הוא עזר לך לחסוך כסף, "
    "שקול לתמוך בפיתוח ולשמור על הבוט פעיל:\n"
    "☕ <a href=\"https://buymeacoffee.com/oshri1997\">buymeacoffee.com/oshri1997</a>\n\n"
    "🎉 <b>כל הפיצ'רים חינמיים בבטא!</b>"
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
