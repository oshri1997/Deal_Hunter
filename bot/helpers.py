"""Shared helpers for bot handlers."""
from datetime import datetime

from sqlalchemy import select

from config import config
from database.engine import get_session
from database.models import User, UserRegion


async def get_or_create_user(telegram_user) -> User:
    """Get existing user or create a new one from a Telegram user object."""
    async with get_session() as session:
        user = await session.get(User, telegram_user.id)
        if not user:
            user = User(
                id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
            )
            session.add(user)
        else:
            # Update info
            user.username = telegram_user.username
            user.first_name = telegram_user.first_name
        return user


async def get_user_regions(user_id: int) -> list[str]:
    """Get list of region codes a user is subscribed to."""
    async with get_session() as session:
        result = await session.execute(
            select(UserRegion.region_code).where(UserRegion.user_id == user_id)
        )
        return [row[0] for row in result.all()]


def is_premium(user: User) -> bool:
    """Check if a user has an active premium subscription."""
    if not user.is_premium:
        return False
    if user.premium_expires_at and user.premium_expires_at < datetime.utcnow():
        return False
    return True


def format_deal(deal, show_region: bool = True) -> str:
    """Format a deal for display in a Telegram message."""
    region_info = config.REGIONS.get(deal.region_code, {})
    flag = region_info.get("flag", "")
    symbol = region_info.get("currency_symbol", "$")
    region_name = region_info.get("name", deal.region_code)

    game_title = deal.game.title if deal.game else "Unknown Game"

    lines = [f"🎮 {game_title}"]

    if show_region:
        lines.append(
            f"{flag} {region_name}: {symbol}{deal.price:.2f} "
            f"(was {symbol}{deal.original_price:.2f}) — {deal.discount_percent}% OFF"
        )
    else:
        lines.append(
            f"{symbol}{deal.price:.2f} "
            f"(was {symbol}{deal.original_price:.2f}) — {deal.discount_percent}% OFF"
        )

    if deal.sale_end_date:
        end_str = deal.sale_end_date.strftime("%b %d, %Y")
        lines.append(f"⏰ Sale ends: {end_str}")

    return "\n".join(lines)


def _escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = r"_*[]()~`>#+-=|{}.!"
    escaped = ""
    for char in text:
        if char in special_chars:
            escaped += f"\\{char}"
        else:
            escaped += char
    return escaped
