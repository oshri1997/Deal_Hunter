from bot.handlers.start import start_handler, help_handler
from bot.handlers.regions import regions_handler, region_callback_handler
from bot.handlers.deals import deals_handler, deals_more_handler
from bot.handlers.wishlist import watch_handler, unwatch_handler, watchlist_handler
from bot.handlers.compare import compare_handler
from bot.handlers.settings import settings_handler
from bot.handlers.premium import premium_handler
from bot.handlers.admin import get_id_handler, scrape_now_handler, scrape_full_handler, scrape_psp_handler, check_amazon_handler, next_scrape_handler, clear_db_handler
from bot.handlers.search import search_handler
from bot.handlers.donate import donate_handler, support_handler
from bot.handlers.alert import alert_handler, alerts_handler, delalert_handler

__all__ = [
    "start_handler",
    "help_handler",
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
    "check_amazon_handler",
    "next_scrape_handler",
    "clear_db_handler",
    "search_handler",
    "donate_handler",
    "support_handler",
    "alert_handler",
    "alerts_handler",
    "delalert_handler",
]
