import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config import config
from database.engine import get_session
from database.models import Subscriber, User

logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = config.ADMIN_CHAT_ID
BMC_URL = config.BMC_URL


async def _subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe — explain the subscription and show payment link."""
    await update.message.reply_text(
        "🎮 <b>PS Deal Hunter — Premium Alerts</b>\n\n"
        "Get real-time deal alerts, price drop notifications, "
        "and gift card stock alerts delivered straight to your chat.\n\n"
        f"☕ Subscribe here: {BMC_URL}\n\n"
        "After paying, run /paid to let us know!",
        parse_mode="HTML",
    )


async def _paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /paid — record payment request and notify admin."""
    user = update.effective_user

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
            await update.message.reply_text("✅ You already have an active subscription!")
            return

    await update.message.reply_text("Got it! You'll be approved shortly.")

    admin_text = (
        "New payment request:\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username}\n"
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
            await update.message.reply_text(f"❌ User not found")
            return
        subscriber.active = True
        subscriber.approved_at = datetime.utcnow()

        # Auto-enable gift card follow and premium
        user = await session.get(User, target_id)
        if user:
            user.is_following = True
            user.is_premium = True
            user.premium_expires_at = None

    await context.bot.send_message(
        chat_id=target_id,
        text="You're now a subscriber! Alerts are active. 🎉",
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
            await update.message.reply_text(f"❌ User not found")
            return
        subscriber.active = False

        # Remove premium and follow
        user = await session.get(User, target_id)
        if user:
            user.is_premium = False
            user.is_following = False

    await context.bot.send_message(
        chat_id=target_id,
        text="Your subscription has ended.",
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
        lines.append(f"- @{sub.username} | {sub.telegram_user_id} | since {since}")

    await update.message.reply_text("\n".join(lines))


async def _status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status — check own subscription status."""
    user_id = update.effective_user.id

    async with get_session() as session:
        subscriber = await session.get(Subscriber, user_id)

    if subscriber and subscriber.active:
        await update.message.reply_text("✅ Your subscription is active.")
    else:
        await update.message.reply_text(
            "❌ You don't have an active subscription. Use /subscribe to get started."
        )


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel — user cancels their own subscription."""
    user_id = update.effective_user.id

    async with get_session() as session:
        subscriber = await session.get(Subscriber, user_id)
        if not subscriber or not subscriber.active:
            await update.message.reply_text(
                "❌ You don't have an active subscription."
            )
            return

        subscriber.active = False

        # Remove premium and follow
        user = await session.get(User, user_id)
        if user:
            user.is_premium = False
            user.is_following = False

    await update.message.reply_text(
        "Your subscription has been cancelled.\n\n"
        "⚠️ To stop future payments, also cancel on Buy Me a Coffee:\n"
        f"{BMC_URL}\n"
        "Go to your account → Manage Memberships → Cancel\n\n"
        "Use /subscribe if you'd like to rejoin."
    )

    # Notify admin
    username = update.effective_user.username
    full_name = update.effective_user.full_name
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"⚠️ Subscription cancelled:\n"
             f"Name: {full_name}\n"
             f"Username: @{username}\n"
             f"User ID: {user_id}",
    )


subscribe_handler = CommandHandler("subscribe", _subscribe)
paid_handler = CommandHandler("paid", _paid)
approve_handler = CommandHandler("approve", _approve)
revoke_handler = CommandHandler("revoke", _revoke)
subscribers_handler = CommandHandler("subscribers", _subscribers)
status_handler = CommandHandler("status", _status)
cancel_handler = CommandHandler("cancel", _cancel)
