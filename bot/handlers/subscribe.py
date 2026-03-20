import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import format_username, get_user_language
from bot.i18n import t
from config import config
from database.engine import get_session
from database.models import Subscriber, User

logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = config.ADMIN_CHAT_ID
BMC_URL = config.BMC_URL


async def _subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe — explain the subscription and show payment link."""
    lang = await get_user_language(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "subscribe_msg", url=BMC_URL),
        parse_mode="HTML",
    )


async def _paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /paid — record payment request and notify admin."""
    user = update.effective_user
    lang = await get_user_language(user.id)

    async with get_session() as session:
        existing = await session.get(Subscriber, user.id)
        if not existing:
            subscriber = Subscriber(
                telegram_user_id=user.id,
                username=user.username,
                full_name=user.full_name,
            )
            session.add(subscriber)
        elif existing.active:
            await update.message.reply_text(t(lang, "subscribe_already_active"))
            return
        else:
            await update.message.reply_text(t(lang, "subscribe_pending"))
            return

    await update.message.reply_text(t(lang, "subscribe_got_it"))

    admin_text = (
        "New payment request:\n"
        f"Name: {user.full_name or 'No name'}\n"
        f"Username: {format_username(user)}\n"
        f"User ID: {user.id}\n"
        f"Run: /approve {user.id} to activate"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)


async def _approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve <user_id> — admin approves a subscriber."""
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID")
        return

    async with get_session() as session:
        subscriber = await session.get(Subscriber, target_id)
        if not subscriber:
            await update.message.reply_text("❌ User not found")
            return
        subscriber.active = True
        subscriber.approved_at = datetime.utcnow()

        user = await session.get(User, target_id)
        if user:
            user.is_following = True
            user.is_premium = True
            user.premium_expires_at = None

    # Notify in the target user's language
    target_lang = await get_user_language(target_id)
    await context.bot.send_message(
        chat_id=target_id,
        text=t(target_lang, "subscribe_approved_msg"),
    )
    await update.message.reply_text(f"✅ Approved {target_id}")


async def _revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /revoke <user_id> — admin revokes a subscriber."""
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /revoke <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID")
        return

    async with get_session() as session:
        subscriber = await session.get(Subscriber, target_id)
        if not subscriber:
            await update.message.reply_text("❌ User not found")
            return
        subscriber.active = False

        user = await session.get(User, target_id)
        if user:
            user.is_premium = False
            user.is_following = False

    target_lang = await get_user_language(target_id)
    await context.bot.send_message(
        chat_id=target_id,
        text=t(target_lang, "subscribe_revoked_msg"),
    )
    await update.message.reply_text(f"✅ Revoked {target_id}")


async def _subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribers — admin lists active subscribers."""
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    from sqlalchemy import select

    async with get_session() as session:
        result = await session.execute(
            select(Subscriber).where(Subscriber.active == True)
        )
        active = result.scalars().all()

    if not active:
        await update.message.reply_text("No active subscribers.")
        return

    lines = [f"Active subscribers ({len(active)}):"]
    for sub in active:
        since = sub.approved_at.strftime("%Y-%m-%d") if sub.approved_at else "N/A"
        name = f"@{sub.username}" if sub.username else sub.full_name or str(sub.telegram_user_id)
        lines.append(f"- {name} | {sub.telegram_user_id} | since {since}")

    await update.message.reply_text("\n".join(lines))


async def _status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status — check own subscription status."""
    user_id = update.effective_user.id
    lang = await get_user_language(user_id)

    async with get_session() as session:
        subscriber = await session.get(Subscriber, user_id)

    if subscriber and subscriber.active:
        await update.message.reply_text(t(lang, "subscribe_active"))
    else:
        await update.message.reply_text(t(lang, "subscribe_not_active"))


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe — user cancels their own subscription."""
    user_id = update.effective_user.id
    lang = await get_user_language(user_id)

    async with get_session() as session:
        subscriber = await session.get(Subscriber, user_id)
        if not subscriber or not subscriber.active:
            await update.message.reply_text(t(lang, "subscribe_not_active_cancel"))
            return

        # Mark subscription as cancelled but keep premium active for 30 days
        subscriber.active = False

        user = await session.get(User, user_id)
        if user:
            user.premium_expires_at = datetime.utcnow() + timedelta(days=30)

    await update.message.reply_text(t(lang, "subscribe_cancelled", url=BMC_URL))

    tg_user = update.effective_user
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "⚠️ Subscription cancelled:\n"
            f"Name: {tg_user.full_name or 'No name'}\n"
            f"Username: {format_username(tg_user)}\n"
            f"User ID: {user_id}"
        ),
    )


subscribe_handler = CommandHandler("subscribe", _subscribe)
paid_handler = CommandHandler("paid", _paid)
approve_handler = CommandHandler("approve", _approve)
revoke_handler = CommandHandler("revoke", _revoke)
subscribers_handler = CommandHandler("subscribers", _subscribers)
status_handler = CommandHandler("status", _status)
cancel_handler = CommandHandler("unsubscribe", _cancel)
