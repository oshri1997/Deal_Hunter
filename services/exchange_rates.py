import logging
import time

import aiohttp

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """Fetches and caches exchange rates to ILS."""

    API_URL = "https://open.er-api.com/v6/latest/ILS"

    _cache: dict[str, float] = {}
    _cache_timestamp: float = 0
    CACHE_TTL = 86400  # 24 hours

    FALLBACK_RATES = {
        "USD": 3.7,
        "INR": 0.044,
        "ILS": 1.0,
    }

    @classmethod
    async def get_rate_to_ils(cls, currency: str) -> float:
        """Get conversion rate: 1 unit of currency = X ILS."""
        if currency == "ILS":
            return 1.0

        if time.time() - cls._cache_timestamp > cls.CACHE_TTL or not cls._cache:
            await cls._refresh()

        return cls._cache.get(currency, cls.FALLBACK_RATES.get(currency, 1.0))

    @classmethod
    async def convert_to_ils(cls, amount: float, currency: str) -> float:
        """Convert an amount to ILS."""
        rate = await cls.get_rate_to_ils(currency)
        return amount * rate

    @classmethod
    async def _refresh(cls):
        """Fetch latest rates from API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(cls.API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # API returns rates FROM ILS (e.g., 1 ILS = 0.27 USD)
                        # We need TO ILS (e.g., 1 USD = 3.7 ILS)
                        rates = data.get("rates", {})
                        cls._cache = {"ILS": 1.0}
                        for code, rate_from_ils in rates.items():
                            if rate_from_ils > 0:
                                cls._cache[code] = 1.0 / rate_from_ils
                        cls._cache_timestamp = time.time()
                        logger.info(
                            f"Exchange rates refreshed: "
                            f"USD={cls._cache.get('USD', '?'):.3f}, "
                            f"INR={cls._cache.get('INR', '?'):.4f}"
                        )
                    else:
                        logger.warning(f"Exchange rate API returned {resp.status}, using cache/fallback")
        except Exception as e:
            logger.error(f"Failed to refresh exchange rates: {e}")
            if not cls._cache:
                cls._cache = cls.FALLBACK_RATES.copy()
                cls._cache_timestamp = time.time()
