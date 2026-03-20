import logging

from sqlalchemy import select
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.helpers import get_or_create_user, get_user_regions, get_user_language, _escape_md, smart_search_games, require_subscriber
from bot.i18n import t
from config import config
from database.engine import get_session
from database.models import Game, PriceAlert

logger = logging.getLogger(__name__)


async def _alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alert <game> <price|discount%> — set a price alert."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

    if not await require_subscriber(update):
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(t(lang, "alert_usage"), parse_mode="MarkdownV2")
        return

    target_str = context.args[-1]
    game_query = " ".join(context.args[:-1]).strip()

    target_price = None
    target_discount = None

    if target_str.endswith("%"):
        try:
            target_discount = int(target_str[:-1])
            if target_discount < 1 or target_discount > 99:
                await update.message.reply_text(t(lang, "alert_invalid_discount"))
                return
        except ValueError:
            await update.message.reply_text(t(lang, "alert_invalid_discount_fmt"), parse_mode="MarkdownV2")
            return
    else:
        try:
            target_price = float(target_str)
            if target_price <= 0:
                await update.message.reply_text(t(lang, "alert_price_positive"))
                return
        except ValueError:
            await update.message.reply_text(t(lang, "alert_invalid_target"), parse_mode="MarkdownV2")
            return

    user_regions = await get_user_regions(user.id)
    if not user_regions:
        await update.message.reply_text(t(lang, "alert_no_regions"))
        return

    async with get_session() as session:
        games = await smart_search_games(session, game_query, limit=1)
        game = games[0] if games else None

        if not game:
            await update.message.reply_text(
                t(lang, "alert_no_game", game=_escape_md(game_query)),
                parse_mode="MarkdownV2",
            )
            return

        created = []
        for region_code in user_regions:
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
            t(lang, "alert_already_set", game=_escape_md(game.title)),
            parse_mode="MarkdownV2",
        )
        return

    if target_discount:
        target_text = t(lang, "alert_target_discount", pct=target_discount)
    else:
        target_text = t(lang, "alert_target_price", price=target_price)
    regions_text = ", ".join(created)

    await update.message.reply_text(
        t(lang, "alert_set",
          game=_escape_md(game.title),
          target=_escape_md(target_text),
          regions=_escape_md(regions_text)),
        parse_mode="MarkdownV2",
    )


async def _alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alerts — list all active price alerts."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

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
        await update.message.reply_text(t(lang, "alerts_none"), parse_mode="MarkdownV2")
        return

    lines = [t(lang, "alerts_header")]
    for i, (alert, game) in enumerate(alerts, 1):
        region_info = config.REGIONS.get(alert.region_code, {})
        flag = region_info.get("flag", "")

        if alert.target_price is not None:
            symbol = region_info.get("currency_symbol", "$")
            target = t(lang, "alerts_below", sym=symbol, price=f"{alert.target_price:.2f}")
        else:
            target = t(lang, "alerts_discount", pct=alert.target_discount)

        lines.append(
            f"{i}\\. 🎮 {_escape_md(game.title)}\n"
            f"    {flag} {_escape_md(target)}"
        )

    lines.append(f"\n{t(lang, 'alerts_count', n=len(alerts))}")
    lines.append(t(lang, "alerts_tip"))

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


async def _delalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delalert <number> — delete a price alert by its list number."""
    user = update.effective_user
    await get_or_create_user(user)
    lang = await get_user_language(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "delalert_usage"), parse_mode="MarkdownV2")
        return

    try:
        alert_num = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t(lang, "delalert_invalid"), parse_mode="MarkdownV2")
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
                t(lang, "delalert_out_of_range", n=len(alerts)),
                parse_mode="MarkdownV2",
            )
            return

        alert, game = alerts[alert_num - 1]
        alert.is_active = False

    await update.message.reply_text(
        t(lang, "delalert_removed", game=_escape_md(game.title)),
        parse_mode="MarkdownV2",
    )


alert_handler = CommandHandler("alert", _alert)
alerts_handler = CommandHandler("alerts", _alerts)
delalert_handler = CommandHandler("delalert", _delalert)
