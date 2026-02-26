"""
Online search fallback for PSPrices.

When a game is not found in the local DB, this module scrapes
the PSPrices "all-discounts" collection page and tries to match
the user's query against game titles on the page.  If needed it
also hits the PlayStation Store concept search URL which returns
JSON and is much faster / more reliable than HTML scraping.
"""

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import quote

import cloudscraper
from bs4 import BeautifulSoup

from config import config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single game found via online search."""
    game_id: str          # psp_{numeric_id}
    title: str
    cover_url: str | None
    platform: str | None
    region_code: str
    price: float | None           # Current sale price (None if no deal)
    original_price: float | None
    discount_percent: int | None
    currency: str
    psprices_url: str | None      # Direct link to the PSPrices game page


# Browser config for cloudscraper (reuse from main scraper)
_BROWSER_CFG = {"browser": "chrome", "platform": "windows", "mobile": False}


def _normalize(text: str) -> str:
    text = re.sub(r'[™®©]', '', text)
    text = unicodedata.normalize('NFKD', text)
    return text.lower().strip()


def _query_matches(query: str, title: str) -> bool:
    """Check if ALL query words appear in the title (order-independent)."""
    norm_title = _normalize(title)
    return all(w in norm_title for w in _normalize(query).split())


class PSPricesOnlineSearch:
    """Search PSPrices website for games matching a query."""

    BASE = "https://psprices.com"
    REGION_MAP = {
        "IL": "il", "US": "us", "IN": "in",
        "GB": "gb", "DE": "de", "FR": "fr",
    }

    def __init__(self):
        self._scraper: cloudscraper.CloudScraper | None = None

    def _get_scraper(self) -> cloudscraper.CloudScraper:
        if self._scraper is None:
            self._scraper = cloudscraper.create_scraper(browser=_BROWSER_CFG)
        return self._scraper

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        region_codes: list[str] | None = None,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search PSPrices for games matching *query*.

        Searches across the given regions (defaults to all supported).
        De-duplicates by title so the user doesn't see the same game
        listed once per region.

        Strategy:
        1. Scrape page 1 of the "all-discounts" collection for each region.
        2. Filter cards whose title matches the query words.
        3. If not enough results, also try a broader approach by scraping
           the main index page (which includes non-discounted games).
        """
        if region_codes is None:
            region_codes = list(config.REGIONS.keys())

        all_results: list[SearchResult] = []
        seen_titles: set[str] = set()
        loop = asyncio.get_event_loop()

        for rc in region_codes:
            psp_region = self.REGION_MAP.get(rc)
            if not psp_region:
                continue

            # Search discounts page
            results = await loop.run_in_executor(
                None, self._scrape_and_filter, psp_region, rc, query
            )
            for r in results:
                norm = _normalize(r.title)
                if norm not in seen_titles:
                    seen_titles.add(norm)
                    all_results.append(r)
                    if len(all_results) >= max_results:
                        return all_results

        return all_results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _scrape_and_filter(
        self, psp_region: str, region_code: str, query: str
    ) -> list[SearchResult]:
        """Fetch PSPrices search results for the query."""
        url = (
            f"{self.BASE}/region-{psp_region}/games/"
            f"?q={quote(query)}&platform=PS5%2CPS4"
        )
        try:
            scraper = self._get_scraper()
            resp = scraper.get(url, timeout=30)
            if resp.status_code != 200:
                logger.warning(f"[OnlineSearch] HTTP {resp.status_code} for {url}")
                return []
            return self._parse_and_filter(resp.text, region_code, query)
        except Exception as e:
            logger.error(f"[OnlineSearch] Error fetching {url}: {e}")
            return []

    def _parse_and_filter(
        self, html: str, region_code: str, query: str
    ) -> list[SearchResult]:
        """Parse .game-fragment cards and keep only those matching *query*."""
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".game-fragment")
        region_info = config.REGIONS.get(region_code, {})
        currency = region_info.get("currency", "USD")
        results: list[SearchResult] = []

        for card in cards:
            parsed = self._parse_card(card, region_code, currency)
            if parsed and _query_matches(query, parsed.title):
                results.append(parsed)

        return results

    def _parse_card(
        self, card, region_code: str, currency: str
    ) -> SearchResult | None:
        """Parse a single .game-fragment card into a SearchResult."""
        try:
            # Game ID
            gid_el = card.select_one("[data-game-id]")
            raw_id = gid_el.get("data-game-id") if gid_el else None
            if not raw_id:
                return None

            # Title
            h3 = card.select_one("h3")
            if not h3:
                return None
            title = h3.get_text(strip=True)
            title = re.sub(r"^[^\w\s(]+", "", title).strip()
            if not title:
                return None

            # Discount badge
            discount_el = card.select_one(".bg-red-700, .bg-red-600")
            discount_percent = None
            if discount_el:
                m = re.search(r"(\d+)", discount_el.get_text(strip=True))
                if m:
                    discount_percent = int(m.group(1))

            # Price
            price = None
            original_price = None
            price_container = card.select_one(".text-xl.font-bold")
            if price_container:
                txt = price_container.get_text(strip=True)
                if "free" in txt.lower():
                    price = 0.0
                    discount_percent = 100
                else:
                    span = price_container.select_one("span.font-bold")
                    if span:
                        price = self._parse_price(span.get_text(strip=True))

                orig_el = card.select_one(".old-price-strike")
                if orig_el:
                    original_price = self._parse_price(orig_el.get_text(strip=True))

            # Cover
            img_el = card.select_one("img[src*='image.api.playstation.com']")
            cover_url = img_el.get("src") if img_el else None

            # Platform
            platform_imgs = card.select("img[alt*='PlayStation']")
            platforms = [img.get("alt", "") for img in platform_imgs]
            platform = "PS5" if any("5" in p for p in platforms) else "PS4"

            # PSPrices link
            link_el = card.select_one("a[href*='/game/']")
            psprices_url = None
            if link_el:
                href = link_el.get("href", "")
                psprices_url = f"{self.BASE}{href}" if href.startswith("/") else href

            return SearchResult(
                game_id=f"psp_{raw_id}",
                title=title,
                cover_url=cover_url,
                platform=platform,
                region_code=region_code,
                price=price,
                original_price=original_price,
                discount_percent=discount_percent,
                currency=currency,
                psprices_url=psprices_url,
            )
        except Exception as e:
            logger.debug(f"[OnlineSearch] Card parse error: {e}")
            return None

    @staticmethod
    def _parse_price(text: str) -> float | None:
        if not text or text.strip().upper() == "N/A":
            return None
        cleaned = re.sub(r"[^\d.,]", "", text)
        if not cleaned:
            return None
        cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
