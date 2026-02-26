import logging
import time

import aiohttp

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """Fetches and caches exchange rates to ILS.

    Uses USD as the API base (free tier of open.er-api supports USD only).
    Conversion formula:  1 CURRENCY = (ILS_per_USD / CURRENCY_per_USD) ILS
    """

    # USD as base — free tier of open.er-api always supports this
    API_URL = "https://open.er-api.com/v6/latest/USD"

    _cache: dict[str, float] = {}
    _cache_timestamp: float = 0
    CACHE_TTL = 86400  # 24 hours

    # Fallback: 1 unit of currency = X ILS
    FALLBACK_RATES = {
        "USD": 3.62,
        "INR": 0.043,
        "ILS": 1.0,
        "GBP": 4.55,
        "EUR": 3.80,
        "BRL": 0.62,
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
        """Fetch latest USD-based rates and compute X-to-ILS conversions."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(cls.API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # rates[code] = how many of 'code' per 1 USD
                        # e.g. rates["INR"] = 86, rates["ILS"] = 3.62
                        rates = data.get("rates", {})
                        ils_per_usd = rates.get("ILS")

                        if not ils_per_usd or ils_per_usd <= 0:
                            logger.warning("ILS not found in exchange rates — using fallback")
                            if not cls._cache:
                                cls._cache = cls.FALLBACK_RATES.copy()
                                cls._cache_timestamp = time.time()
                            return

                        # 1 CURRENCY = (1 / rates[CURRENCY]) USD = ils_per_usd / rates[CURRENCY] ILS
                        cls._cache = {"ILS": 1.0, "USD": ils_per_usd}
                        for code, units_per_usd in rates.items():
                            if units_per_usd > 0:
                                cls._cache[code] = ils_per_usd / units_per_usd

                        cls._cache_timestamp = time.time()
                        logger.info(
                            f"Exchange rates refreshed: "
                            f"1 USD={cls._cache.get('USD', '?'):.3f}₪, "
                            f"1 INR={cls._cache.get('INR', '?'):.4f}₪"
                        )
                    else:
                        logger.warning(f"Exchange rate API returned {resp.status}, using cache/fallback")
        except Exception as e:
            logger.error(f"Failed to refresh exchange rates: {e}")
            if not cls._cache:
                cls._cache = cls.FALLBACK_RATES.copy()
                cls._cache_timestamp = time.time()
