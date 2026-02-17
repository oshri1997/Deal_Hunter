import logging

from sqlalchemy import select, delete
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_regions, _escape_md, smart_search_games
from config import config
from database.engine import get_session
from database.models import Game, PriceAlert

logger = logging.getLogger(__name__)


async def _alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alert <game> <price|discount%> — set a price alert."""
    user = update.effective_user
    await get_or_create_user(user)

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "ℹ️ *Usage:*\n"
            "`/alert Game Title 100` \\- Alert when price drops below 100\n"
            "`/alert Game Title 50%` \\- Alert when discount reaches 50%\n\n"
            "Example:\n"
            "`/alert God of War Ragnarok 100`\n"
            "`/alert Elden Ring 50%`",
            parse_mode="MarkdownV2",
        )
        return

    # Last arg is the target (price or discount%), rest is game name
    target_str = context.args[-1]
    game_query = " ".join(context.args[:-1]).strip()

    # Parse target
    target_price = None
    target_discount = None

    if target_str.endswith("%"):
        try:
            target_discount = int(target_str[:-1])
            if target_discount < 1 or target_discount > 99:
                await update.message.reply_text("⚠️ Discount must be between 1% and 99%.")
                return
        except ValueError:
            await update.message.reply_text("⚠️ Invalid discount format. Use e.g. `50%`", parse_mode="MarkdownV2")
            return
    else:
        try:
            target_price = float(target_str)
            if target_price <= 0:
                await update.message.reply_text("⚠️ Price must be greater than 0.")
                return
        except ValueError:
            await update.message.reply_text(
                "⚠️ Invalid target\\. Use a price \\(e\\.g\\. `100`\\) or discount \\(e\\.g\\. `50%`\\)",
                parse_mode="MarkdownV2",
            )
            return

    # Get user's regions
    user_regions = await get_user_regions(user.id)
    if not user_regions:
        await update.message.reply_text(
            "⚠️ You haven't selected any regions yet.\n"
            "Use /regions to choose your PSN store regions first!"
        )
        return

    async with get_session() as session:
        games = await smart_search_games(session, game_query, limit=1)
        game = games[0] if games else None

        if not game:
            await update.message.reply_text(
                f"⚠️ No game found matching *{_escape_md(game_query)}*\\.\n"
                "Try a different search term or use /search first\\.",
                parse_mode="MarkdownV2",
            )
            return

        # Create alerts for each of the user's regions
        created = []
        for region_code in user_regions:
            # Check if alert already exists
            existing = await session.execute(
                select(PriceAlert).where(
                    PriceAlert.user_id == user.id,
                    PriceAlert.game_id == game.id,
                    PriceAlert.region_code == region_code,
                    PriceAlert.is_active == True,
                )
            )
            if existing.scalar_one_or_none():
                continue

            alert = PriceAlert(
                user_id=user.id,
                game_id=game.id,
                target_price=target_price,
                target_discount=target_discount,
                region_code=region_code,
            )
            session.add(alert)
            region_info = config.REGIONS.get(region_code, {})
            created.append(f"{region_info.get('flag', '')} {region_info.get('name', region_code)}")

    if not created:
        await update.message.reply_text(
            f"ℹ️ You already have active alerts for *{_escape_md(game.title)}* in all your regions\\.",
            parse_mode="MarkdownV2",
        )
        return

    # Format the response
    target_text = f"{target_discount}% discount" if target_discount else f"price below {target_price}"
    regions_text = ", ".join(created)

    await update.message.reply_text(
        f"🔔 *Price alert set\\!*\n\n"
        f"🎮 {_escape_md(game.title)}\n"
        f"🎯 Target: {_escape_md(target_text)}\n"
        f"📍 Regions: {_escape_md(regions_text)}\n\n"
        f"You'll be notified when the conditions are met\\!",
        parse_mode="MarkdownV2",
    )


async def _alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alerts — list all active price alerts."""
    user = update.effective_user
    await get_or_create_user(user)

    async with get_session() as session:
        result = await session.execute(
            select(PriceAlert, Game)
            .join(Game, PriceAlert.game_id == Game.id)
            .where(
                PriceAlert.user_id == user.id,
                PriceAlert.is_active == True,
            )
            .order_by(PriceAlert.created_at.desc())
        )
        alerts = result.all()

    if not alerts:
        await update.message.reply_text(
            "🔔 *No active price alerts\\.*\n"
            "Use `/alert Game Title 100` to set one\\!",
            parse_mode="MarkdownV2",
        )
        return

    lines = ["🔔 *Your Price Alerts:*\n"]
    for i, (alert, game) in enumerate(alerts, 1):
        region_info = config.REGIONS.get(alert.region_code, {})
        flag = region_info.get("flag", "")

        if alert.target_price is not None:
            symbol = region_info.get("currency_symbol", "$")
            target = f"below {symbol}{alert.target_price:.2f}"
        else:
            target = f"{alert.target_discount}% discount"

        lines.append(
            f"{i}\\. 🎮 {_escape_md(game.title)}\n"
            f"    {flag} Target: {_escape_md(target)}"
        )

    lines.append(f"\n📊 {len(alerts)} active alert\\(s\\)")
    lines.append("Use `/delalert <number>` to remove an alert\\.")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


async def _delalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delalert <number> — delete a price alert by its list number."""
    user = update.effective_user
    await get_or_create_user(user)

    if not context.args:
        await update.message.reply_text(
            "ℹ️ *Usage:* `/delalert 1`\n"
            "Use /alerts to see your alert numbers\\.",
            parse_mode="MarkdownV2",
        )
        return

    try:
        alert_num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a valid number\\.", parse_mode="MarkdownV2")
        return

    async with get_session() as session:
        result = await session.execute(
            select(PriceAlert, Game)
            .join(Game, PriceAlert.game_id == Game.id)
            .where(
                PriceAlert.user_id == user.id,
                PriceAlert.is_active == True,
            )
            .order_by(PriceAlert.created_at.desc())
        )
        alerts = result.all()

        if alert_num < 1 or alert_num > len(alerts):
            await update.message.reply_text(
                f"⚠️ Invalid alert number\\. You have {len(alerts)} active alerts\\.\n"
                "Use /alerts to see the list\\.",
                parse_mode="MarkdownV2",
            )
            return

        alert, game = alerts[alert_num - 1]
        alert.is_active = False

    await update.message.reply_text(
        f"❌ Removed alert for *{_escape_md(game.title)}*\\.",
        parse_mode="MarkdownV2",
    )


alert_handler = CommandHandler("alert", _alert)
alerts_handler = CommandHandler("alerts", _alerts)
delalert_handler = CommandHandler("delalert", _delalert)
