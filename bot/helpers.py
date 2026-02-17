"""Shared helpers for bot handlers."""
import re
import unicodedata
from datetime import datetime

from sqlalchemy import select

from config import config
from database.engine import get_session
from database.models import Game, User, UserRegion
from services.exchange_rates import ExchangeRateService


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


# --- Smart Search ---

def _normalize_title(title: str) -> str:
    """Normalize a game title for matching: strip ™®©, normalize unicode, lowercase."""
    title = re.sub(r'[™®©]', '', title)
    title = unicodedata.normalize('NFKD', title)
    return title.lower().strip()


def _words_match(query: str, title: str) -> bool:
    """Check if ALL words in query appear in title (any order).

    >>> _words_match("FC 26", "EA SPORTS FC™ 26")
    True
    """
    normalized_title = _normalize_title(title)
    query_words = _normalize_title(query).split()
    return all(word in normalized_title for word in query_words)


async def smart_search_games(session, query: str, limit: int = 10) -> list[Game]:
    """Search games with word-based matching.

    1. Try ILIKE substring first (fast).
    2. If not enough results, fetch broader candidates and filter with word matching.
    """
    # Step 1: direct ILIKE
    result = await session.execute(
        select(Game).where(Game.title.ilike(f"%{query}%")).limit(limit)
    )
    games = list(result.scalars().all())

    if len(games) >= limit:
        return games

    # Step 2: word-based fallback
    query_words = _normalize_title(query).split()
    if not query_words:
        return games

    found_ids = {g.id for g in games}
    search_word = max(query_words, key=len)  # longest word = most selective

    result = await session.execute(
        select(Game).where(Game.title.ilike(f"%{search_word}%")).limit(100)
    )
    candidates = result.scalars().all()

    for game in candidates:
        if game.id not in found_ids and _words_match(query, game.title):
            games.append(game)
            found_ids.add(game.id)
            if len(games) >= limit:
                break

    return games[:limit]


# --- Dual-Currency (ILS) ---

async def format_price_ils(price: float, currency: str) -> str:
    """Return ILS equivalent suffix for non-ILS currencies.

    Returns "" for ILS, " (~185₪)" for other currencies.
    """
    if currency == "ILS":
        return ""
    ils = await ExchangeRateService.convert_to_ils(price, currency)
    return f" (~{ils:.0f}₪)"
