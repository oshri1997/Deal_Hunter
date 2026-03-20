from bot.handlers.start import start_handler, help_handler, language_handler, language_callback_handler
from bot.handlers.regions import regions_handler, region_callback_handler
from bot.handlers.deals import deals_handler, deals_more_handler
from bot.handlers.wishlist import watch_handler, unwatch_handler, watchlist_handler
from bot.handlers.compare import compare_handler
from bot.handlers.settings import settings_handler
from bot.handlers.premium import premium_handler
from bot.handlers.admin import get_id_handler, scrape_now_handler, scrape_full_handler, scrape_psp_handler, check_amazon_handler, giftcard_handler, offgamers_handler, next_scrape_handler, clear_db_handler
from bot.handlers.search import search_handler
from bot.handlers.alert import alert_handler, alerts_handler, delalert_handler
from bot.handlers.follow import follow_handler
from bot.handlers.subscribe import (
    subscribe_handler,
    paid_handler,
    approve_handler,
    revoke_handler,
    subscribers_handler,
    status_handler,
    cancel_handler,
)

__all__ = [
    "start_handler",
    "help_handler",
    "language_handler",
    "language_callback_handler",
    "regions_handler",
    "region_callback_handler",
    "deals_handler",
    "deals_more_handler",
    "watch_handler",
    "unwatch_handler",
    "watchlist_handler",
    "compare_handler",
    "settings_handler",
    "premium_handler",
    "get_id_handler",
    "scrape_now_handler",
    "scrape_full_handler",
    "scrape_psp_handler",
    "giftcard_handler",
    "check_amazon_handler",
    "offgamers_handler",
    "next_scrape_handler",
    "clear_db_handler",
    "search_handler",
    "alert_handler",
    "alerts_handler",
    "delalert_handler",
    "follow_handler",
    "subscribe_handler",
    "paid_handler",
    "approve_handler",
    "revoke_handler",
    "subscribers_handler",
    "status_handler",
    "cancel_handler",
]
