import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/ps5deals"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Scraping
    SCRAPE_INTERVAL_HOURS: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "3"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )
    REQUEST_TIMEOUT: int = 30

    # Notification
    MAX_DEALS_PER_NOTIFICATION: int = 10

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Supported regions - Only IL, US, IN
    REGIONS: dict[str, dict] = {
        "IL": {"name": "Israel", "flag": "🇮🇱", "currency": "ILS", "currency_symbol": "₪", "store_url": "https://store.playstation.com/en-il"},
        "US": {"name": "USA", "flag": "🇺🇸", "currency": "USD", "currency_symbol": "$", "store_url": "https://store.playstation.com/en-us"},
        "IN": {"name": "India", "flag": "🇮🇳", "currency": "INR", "currency_symbol": "₹", "store_url": "https://store.playstation.com/en-in"},
    }


config = Config()
