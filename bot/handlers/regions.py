import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config import config
from bot.helpers import get_or_create_user, get_user_regions, _escape_md
from database.engine import get_session
from database.models import User, UserRegion

logger = logging.getLogger(__name__)


def _build_region_keyboard(selected_regions: list[str]) -> InlineKeyboardMarkup:
    """Build inline keyboard with region toggle buttons."""
    buttons = []
    row = []
    for code, info in config.REGIONS.items():
        check = "✅ " if code in selected_regions else ""
        label = f"{check}{info['flag']} {info['name']}"
        row.append(InlineKeyboardButton(label, callback_data=f"region:{code}"))
    
    # All 3 regions in one row
    buttons.append(row)
    buttons.append([InlineKeyboardButton("✅ Done", callback_data="region:done")])
    return InlineKeyboardMarkup(buttons)


async def _regions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /regions command — show region selection keyboard."""
    user = update.effective_user
    await get_or_create_user(user)
    selected = await get_user_regions(user.id)
    keyboard = _build_region_keyboard(selected)

    count_text = f"Selected: {len(selected)} region(s)"
    await update.message.reply_text(
        f"\U0001f30d *Select your PSN store regions:*\n{_escape_md(count_text)}\n\n"
        "Tap a region to toggle it on/off\\.",
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )


async def _region_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle region selection button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("region:"):
        return

    action = data.split(":", 1)[1]
    user_id = query.from_user.id

    if action == "done":
        selected = await get_user_regions(user_id)
        if not selected:
            await query.edit_message_text(
                "\u26a0\ufe0f You haven't selected any regions\\. Use /regions to choose at least one\\.",
                parse_mode="MarkdownV2",
            )
        else:
            region_names = []
            for code in selected:
                info = config.REGIONS.get(code, {})
                region_names.append(f"{info.get('flag', '')} {info.get('name', code)}")
            regions_str = ", ".join(region_names)
            await query.edit_message_text(
                f"\u2705 *Subscribed to:* {_escape_md(regions_str)}\n\n"
                "You'll receive deal alerts for these regions\\.\n"
                "Use /deals to see current deals\\!",
                parse_mode="MarkdownV2",
            )
        return

    region_code = action

    async with get_session() as session:
        db_user = await session.get(User, user_id)
        if not db_user:
            await query.edit_message_text("Please use /start first.")
            return

        # Check if region is already selected
        current_regions = await get_user_regions(user_id)

        if region_code in current_regions:
            # Remove region
            from sqlalchemy import delete
            await session.execute(
                delete(UserRegion).where(
                    UserRegion.user_id == user_id,
                    UserRegion.region_code == region_code,
                )
            )
            current_regions.remove(region_code)
        else:
            # Add region
            session.add(UserRegion(user_id=user_id, region_code=region_code))
            current_regions.append(region_code)

    # Refresh keyboard
    keyboard = _build_region_keyboard(current_regions)
    count_text = f"Selected: {len(current_regions)} region(s)"
    await query.edit_message_text(
        f"\U0001f30d *Select your PSN store regions:*\n{_escape_md(count_text)}\n\n"
        "Tap a region to toggle it on/off\\.",
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )


regions_handler = CommandHandler("regions", _regions)
region_callback_handler = CallbackQueryHandler(_region_callback, pattern=r"^region:")
