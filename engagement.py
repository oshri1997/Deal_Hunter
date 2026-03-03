import asyncio
import logging
import random
from datetime import datetime, time

from sqlalchemy import select
from telegram import Bot
from telegram.error import TelegramError

from database.engine import get_session
from database.models import User

logger = logging.getLogger(__name__)

ENGAGEMENT_MESSAGES = [
    {
        "key": "support",
        "text": (
            "\U0001f496 \u05e8\u05d5\u05e6\u05d9\u05dd \u05dc\u05e2\u05d6\u05d5\u05e8 \u05dc\u05d9 \u05dc\u05d4\u05de\u05e9\u05d9\u05da \u05dc\u05e4\u05ea\u05d7 \u05d0\u05ea \u05d4\u05d1\u05d5\u05d8?\n\n"
            "\u05e0\u05d9\u05ea\u05df \u05dc\u05ea\u05de\u05d5\u05da \u05d1\u05d9 \u05db\u05d0\u05df:\n"
            "\U0001f449 https://buymeacoffee.com/oshri1997\n\n"
            "\u05db\u05dc \u05ea\u05e8\u05d5\u05de\u05d4 \u05e2\u05d5\u05d6\u05e8\u05ea \u05dc\u05e9\u05e4\u05e8 \u05d5\u05dc\u05d4\u05d5\u05e1\u05d9\u05e3 \u05ea\u05db\u05d5\u05e0\u05d5\u05ea \u05d7\u05d3\u05e9\u05d5\u05ea! \U0001f64f"
        ),
    },
    {
        "key": "feedback",
        "text": (
            "\U0001f4ac \u05d9\u05e9 \u05dc\u05db\u05dd \u05d4\u05de\u05dc\u05e6\u05d5\u05ea? \u05d8\u05d9\u05e4\u05d9\u05dd?\n\n"
            "\u05e8\u05d5\u05e6\u05d9\u05dd \u05dc\u05e9\u05ea\u05e3 \u05e2\u05dc \u05de\u05e9\u05d7\u05e7\u05d9\u05dd \u05e9\u05d0\u05ea\u05dd \u05de\u05e9\u05d7\u05e7\u05d9\u05dd?\n\n"
            "\u05d4\u05e6\u05d8\u05e8\u05e4\u05d5 \u05dc\u05e2\u05e8\u05d5\u05e5 \u05d4\u05d8\u05dc\u05d2\u05e8\u05dd \u05e9\u05dc\u05e0\u05d5:\n"
            "\U0001f449 https://t.me/deal_hunter_il\n\n"
            "\u05e0\u05e9\u05de\u05d7 \u05dc\u05e9\u05de\u05d5\u05e2 \u05de\u05db\u05dd! \U0001f3ae"
        ),
    },
    {
        "key": "community",
        "text": (
            "\U0001f3ae \u05d4\u05e6\u05d8\u05e8\u05e4\u05d5 \u05dc\u05e7\u05d4\u05d9\u05dc\u05d4 \u05e9\u05dc\u05e0\u05d5!\n\n"
            "\u05e9\u05ea\u05e4\u05d5 \u05d4\u05de\u05dc\u05e6\u05d5\u05ea, \u05d8\u05d9\u05e4\u05d9\u05dd \u05d5\u05d3\u05e2\u05d5\u05ea \u05e2\u05dc \u05de\u05e9\u05d7\u05e7\u05d9\u05dd:\n"
            "\U0001f449 https://t.me/deal_hunter_il\n\n"
            "\u05d1\u05e0\u05d5\u05e1\u05e3, \u05d0\u05dd \u05d0\u05ea\u05dd \u05e0\u05d4\u05e0\u05d9\u05dd \u05de\u05d4\u05d1\u05d5\u05d8 \u05d5\u05e8\u05d5\u05e6\u05d9\u05dd \u05dc\u05ea\u05de\u05d5\u05da:\n"
            "\U0001f496 https://buymeacoffee.com/oshri1997"
        ),
    },
]

FEATURE_TIPS = [
    "\U0001f4a1 \u05d9\u05d3\u05e2\u05ea\u05dd? \u05d0\u05e4\u05e9\u05e8 \u05dc\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1 /compare \u05db\u05d3\u05d9 \u05dc\u05d4\u05e9\u05d5\u05d5\u05ea \u05de\u05d7\u05d9\u05e8\u05d9\u05dd \u05d1\u05d9\u05df \u05d0\u05d6\u05d5\u05e8\u05d9\u05dd!",
    "\U0001f4a1 \u05d9\u05d3\u05e2\u05ea\u05dd? \u05d0\u05e4\u05e9\u05e8 \u05dc\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1 /watch \u05db\u05d3\u05d9 \u05dc\u05e2\u05e7\u05d5\u05d1 \u05d0\u05d7\u05e8\u05d9 \u05de\u05e9\u05d7\u05e7\u05d9\u05dd \u05d5\u05dc\u05e7\u05d1\u05dc \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea!",
    "\U0001f4a1 \u05d9\u05d3\u05e2\u05ea\u05dd? \u05d0\u05e4\u05e9\u05e8 \u05dc\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1 /alert \u05db\u05d3\u05d9 \u05dc\u05e7\u05d1\u05dc \u05d4\u05ea\u05e8\u05d0\u05d4 \u05db\u05e9\u05de\u05e9\u05d7\u05e7 \u05d9\u05d5\u05e8\u05d3 \u05dc\u05de\u05d7\u05d9\u05e8 \u05de\u05e1\u05d5\u05d9\u05dd!",
    "\U0001f4a1 \u05d9\u05d3\u05e2\u05ea\u05dd? \u05d0\u05e4\u05e9\u05e8 \u05dc\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1 /deals \u05db\u05d3\u05d9 \u05dc\u05e8\u05d0\u05d5\u05ea \u05d0\u05ea \u05db\u05dc \u05d4\u05de\u05d1\u05e6\u05e2\u05d9\u05dd \u05d4\u05e0\u05d5\u05db\u05d7\u05d9\u05d9\u05dd!",
    "\U0001f4a1 \u05d9\u05d3\u05e2\u05ea\u05dd? \u05d0\u05e4\u05e9\u05e8 \u05dc\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1 /search \u05db\u05d3\u05d9 \u05dc\u05d7\u05e4\u05e9 \u05de\u05e9\u05d7\u05e7 \u05e1\u05e4\u05e6\u05d9\u05e4\u05d9 \u05d5\u05dc\u05e8\u05d0\u05d5\u05ea \u05d0\u05ea \u05d4\u05de\u05d7\u05d9\u05e8 \u05e9\u05dc\u05d5!",
    "\U0001f4a1 \u05d9\u05d3\u05e2\u05ea\u05dd? \u05d0\u05e4\u05e9\u05e8 \u05dc\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1 /regions \u05db\u05d3\u05d9 \u05dc\u05d1\u05d7\u05d5\u05e8 \u05d0\u05d6\u05d5\u05e8\u05d9\u05dd \u05d5\u05dc\u05e7\u05d1\u05dc \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea \u05e2\u05dc \u05de\u05d1\u05e6\u05e2\u05d9\u05dd!",
    "\U0001f4a1 \u05d9\u05d3\u05e2\u05ea\u05dd? \u05d0\u05e4\u05e9\u05e8 \u05dc\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1 /watchlist \u05db\u05d3\u05d9 \u05dc\u05e8\u05d0\u05d5\u05ea \u05d0\u05ea \u05db\u05dc \u05d4\u05de\u05e9\u05d7\u05e7\u05d9\u05dd \u05e9\u05d0\u05ea\u05dd \u05e2\u05d5\u05e7\u05d1\u05d9\u05dd \u05d0\u05d7\u05e8\u05d9\u05d4\u05dd!",
    "💡 Did you know? Use /follow to get notified when Amazon PlayStation giftcards are back in stock!",
]


async def send_engagement_message(bot: Bot) -> None:
    """Send a random engagement message or feature tip to all users.

    Messages are only sent between 08:00 and 20:00.  If called outside
    that window the function returns immediately.
    """
    now = datetime.now()
    if not (time(8, 0) <= now.time() <= time(20, 0)):
        logger.info("Outside engagement window (08:00-20:00), skipping")
        return

    # Pick a random message: 40% feature tip, 60% engagement
    if random.random() < 0.4:
        text = random.choice(FEATURE_TIPS)
    else:
        text = random.choice(ENGAGEMENT_MESSAGES)["text"]

    # Fetch all users
    async with get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    if not users:
        logger.info("No users to send engagement message to")
        return

    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(chat_id=user.id, text=text)
            sent += 1
        except TelegramError as e:
            logger.warning(f"Failed to send engagement message to {user.id}: {e}")
            failed += 1
        await asyncio.sleep(0.05)

    logger.info(f"Engagement message sent to {sent} users ({failed} failed)")
