import logging
import asyncio
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime

import cloudscraper
from bs4 import BeautifulSoup

from config import config

logger = logging.getLogger(__name__)


@dataclass
class ScrapedDeal:
    game_id: str
    title: str
    cover_url: str | None
    region_code: str
    price: float
    original_price: float
    discount_percent: int
    currency: str
    sale_end_date: datetime | None
    platform: str | None = None
    genre: str | None = None
    price_tag: str | None = None  # "New lowest!", "Lowest", etc.
    page_number: int = 1  # Which page (1, 2, 3...)
    position_on_page: int = 0  # Position on page (0-35)


# Browser profiles to rotate through when Cloudflare blocks us
_BROWSER_CONFIGS = [
    {"browser": "chrome", "platform": "windows", "mobile": False},
    {"browser": "firefox", "platform": "windows", "mobile": False},
    {"browser": "chrome", "platform": "linux", "mobile": False},
    {"browser": "chrome", "platform": "darwin", "mobile": False},
]


class PSPricesScraper:
    """Scrapes PSPrices.com/region-XX/collection/all-discounts using cloudscraper.

    Tested against the live HTML as of Feb 2026.
    URL pattern:
        https://psprices.com/region-{region}/collection/all-discounts
            ?page={page}&platform=PS5%2CPS4
    """

    REGION_MAP = {
        "IL": "il",
        "US": "us",
        "IN": "in",
        "GB": "gb",
        "DE": "de",
        "FR": "fr",
        "BR": "br",
        "JP": "jp",
        "AU": "au",
        "RU": "ru",
    }

    def __init__(self):
        self.base_url = "https://psprices.com"
        # Persistent session — keeps cookies across pages so Cloudflare
        # recognises us as the same "browser" and doesn't re-challenge.
        self._scraper: cloudscraper.CloudScraper | None = None
        self._cfg_index = 0

    def _get_scraper(self, force_new: bool = False) -> cloudscraper.CloudScraper:
        """Return the current session, or create a new one."""
        if self._scraper is None or force_new:
            cfg = _BROWSER_CONFIGS[self._cfg_index % len(_BROWSER_CONFIGS)]
            self._cfg_index += 1
            self._scraper = cloudscraper.create_scraper(browser=cfg)
            logger.info(
                f"[PSPrices] New session: {cfg['browser']}/{cfg['platform']}"
            )
        return self._scraper

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def scrape_region(
        self,
        region_code: str,
        max_pages: int = 5,
        full_scrape: bool = False,
    ) -> list[ScrapedDeal]:
        """Scrape deals for *region_code* in REVERSE order (pages 50→1 or 5→1).

        Args:
            region_code: Two-letter region code (e.g. "US", "IN").
            max_pages:   Maximum pages to fetch (default 5, each page ~36 deals).
            full_scrape: If True, override max_pages and fetch up to 50 pages.
        """
        psp_region = self.REGION_MAP.get(region_code)
        if not psp_region:
            logger.warning(f"Unsupported region for PSPrices: {region_code}")
            return []

        pages = self._get_total_pages(psp_region) if full_scrape else max_pages
        all_deals: list[ScrapedDeal] = []
        seen_ids: set[str] = set()
        consecutive_empty = 0
        loop = asyncio.get_event_loop()

        # Scrape from page 1 to max_pages (newest to oldest)
        for page in range(1, pages + 1):
            url = (
                f"{self.base_url}/region-{psp_region}/collection/all-discounts"
                f"?page={page}&platform=PS5%2CPS4"
            )
            logger.info(f"[PSPrices] Scraping {region_code} page {page} ...")

            page_deals = await loop.run_in_executor(
                None, self._fetch_and_parse, url, region_code, page
            )

            if not page_deals:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    logger.info(
                        f"[PSPrices] 2 empty pages in a row — stopping for {region_code}"
                    )
                    break
                continue

            consecutive_empty = 0

            # De-duplicate across pages
            new_deals = [d for d in page_deals if d.game_id not in seen_ids]
            if not new_deals:
                logger.info(
                    f"[PSPrices] Page {page} returned only duplicates — stopping"
                )
                break

            for d in new_deals:
                seen_ids.add(d.game_id)
            all_deals.extend(new_deals)
            logger.info(
                f"[PSPrices] +{len(new_deals)} deals from page {page}  "
                f"(total {len(all_deals)})"
            )

            # Random delay between pages — looks more human
            if page < pages:
                delay = random.uniform(5, 10)
                logger.debug(f"[PSPrices] Waiting {delay:.1f}s before next page")
                await asyncio.sleep(delay)

        logger.info(f"[PSPrices] {region_code} done — {len(all_deals)} deals total")
        return all_deals

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    def _get_total_pages(self, psp_region: str) -> int:
        """Fetch page 1 and extract total page count from 'Page X of Y' span."""
        url = (
            f"{self.base_url}/region-{psp_region}/collection/all-discounts"
            f"?page=1&platform=PS5%2CPS4"
        )
        try:
            scraper = self._get_scraper()
            resp = scraper.get(url, timeout=30)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                span = soup.find("span", class_=lambda c: c and "text-gray-700" in c)
                if span:
                    match = re.search(r"of\s+(\d+)", span.get_text())
                    if match:
                        total = int(match.group(1))
                        logger.info(f"[PSPrices] {psp_region} has {total} pages")
                        return min(total, 200)
        except Exception as e:
            logger.error(f"[PSPrices] Failed to get total pages: {e}")
        return 999

    def _fetch_and_parse(self, url: str, region_code: str, page: int) -> list[ScrapedDeal]:
        """Synchronous fetch + parse (runs in executor).

        Uses a persistent session so cookies carry over between pages.
        On failure, rotates to a new browser profile and retries.
        """
        max_retries = 5

        for attempt in range(max_retries):
            try:
                # First attempt: reuse existing session
                # After a failure: create a fresh session with a different profile
                scraper = self._get_scraper(force_new=(attempt > 0))

                # Small random pre-request jitter
                time.sleep(random.uniform(0.5, 2.0))

                resp = scraper.get(url, timeout=30)

                if resp.status_code == 200:
                    deals = self._parse_page(resp.text, region_code, page)
                    if deals:
                        return deals
                    # 200 but empty — could be a Cloudflare JS challenge page
                    logger.warning(
                        "[PSPrices] 200 but 0 deals — possible challenge page"
                    )

                if resp.status_code in (403, 429, 503):
                    wait = random.uniform(5, 10) * (attempt + 1)
                    logger.warning(
                        f"[PSPrices] HTTP {resp.status_code} — "
                        f"retry {attempt + 1}/{max_retries} in {wait:.0f}s"
                    )
                    time.sleep(wait)
                    continue

                logger.error(f"[PSPrices] HTTP {resp.status_code} for {url}")
                break

            except Exception as e:
                logger.error(
                    f"[PSPrices] Fetch error (attempt {attempt + 1}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(3, 6))

        return []

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_page(self, html: str, region_code: str, page_number: int = 1) -> list[ScrapedDeal]:
        """Parse PSPrices all-discounts page.

        Selectors verified against the live site (Feb 2026):
          - Card container:   .game-fragment
          - Game ID:          [data-game-id]  (attribute on inner div)
          - Title:            h3              (text, flag img prefix removed)
          - Discount badge:   .bg-red-700 / .bg-red-600  (text like "−70%")
          - Sale price:       .text-xl.font-bold > span.font-bold
          - Original price:   .old-price-strike
          - Cover image:      img[src*='image.api.playstation.com']
          - End date:         text containing "until MM/DD/YYYY"
          - Platform:         img[alt*='PlayStation']
        """
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".game-fragment")
        if not cards:
            logger.info("[PSPrices] No .game-fragment cards found on page")
            return []

        region_info = config.REGIONS.get(region_code, {})
        currency = region_info.get("currency", "USD")

        deals: list[ScrapedDeal] = []
        for position, card in enumerate(cards):
            deal = self._parse_card(card, region_code, currency, page_number, position)
            if deal:
                deals.append(deal)

        return deals

    def _parse_card(
        self, card, region_code: str, currency: str, page_number: int, position: int
    ) -> ScrapedDeal | None:
        """Parse a single .game-fragment card element."""
        try:
            # ---- Game ID (numeric, from data-game-id attribute) ----
            gid_el = card.select_one("[data-game-id]")
            raw_game_id = gid_el.get("data-game-id") if gid_el else None
            if not raw_game_id:
                return None

            # ---- Title ----
            h3 = card.select_one("h3")
            if not h3:
                return None
            title = h3.get_text(strip=True)
            # The h3 may contain a flag <img> whose alt text leaks in — strip it
            title = re.sub(r"^[^\w\s(]+", "", title).strip()
            if not title:
                return None

            # ---- Discount badge  (e.g. "−70%") ----
            discount_el = card.select_one(".bg-red-700, .bg-red-600")
            discount_percent = 0
            
            if discount_el:
                disc_match = re.search(r"(\d+)", discount_el.get_text(strip=True))
                if disc_match:
                    discount_percent = int(disc_match.group(1))

            # ---- Sale price ----
            # Structure: <span class="text-xl font-bold"> ... <span class="font-bold">1,799</span>
            price_container = card.select_one(".text-xl.font-bold")
            if not price_container:
                return None
            
            # Check if it's a free game
            is_free = False
            price_text = price_container.get_text(strip=True)
            if "free" in price_text.lower():
                is_free = True
                discount_percent = 100
            
            # Skip if no discount and not free
            if discount_percent == 0 and not is_free:
                return None
            
            # Parse price
            if is_free:
                price = 0.0
                original_price = 0.0  # Will be calculated later if needed
            else:
                price_span = price_container.select_one("span.font-bold")
                if not price_span:
                    return None
                price = self._parse_price(price_span.get_text(strip=True))
                if price is None:
                    return None
                
                # ---- Original price ----
                orig_el = card.select_one(".old-price-strike")
                original_price = (
                    self._parse_price(orig_el.get_text(strip=True)) if orig_el else None
                )
                # If original price is missing or "N/A", compute from discount
                if not original_price or original_price <= 0:
                    if discount_percent > 0 and discount_percent < 100:
                        original_price = round(price / (1 - discount_percent / 100), 2)
                    else:
                        original_price = price

            if price >= original_price:
                # Safety check — should be a discount
                pass  # allow it, the discount badge already confirmed it

            # ---- Cover image ----
            img_el = card.select_one("img[src*='image.api.playstation.com']")
            cover_url = img_el.get("src") if img_el else None

            # ---- Sale end date (text: "until MM/DD/YYYY") ----
            sale_end_date = None
            date_text = card.find(string=re.compile(r"until", re.I))
            if date_text:
                date_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", date_text.strip())
                if date_match:
                    month, day, year = date_match.groups()
                    try:
                        sale_end_date = datetime(int(year), int(month), int(day))
                    except ValueError:
                        pass

            # ---- Platform ----
            platform_imgs = card.select("img[alt*='PlayStation']")
            platforms = [img.get("alt", "") for img in platform_imgs]
            if any("5" in p for p in platforms):
                platform = "PS5"
            elif any("4" in p for p in platforms):
                platform = "PS4"
            else:
                platform = "PS5"

            # ---- Game link (for reference) ----
            link_el = card.select_one("a[href*='/game/']")
            game_url = link_el.get("href", "") if link_el else ""

            # ---- Price tag ("New lowest!", "Lowest") ----
            price_tag = None
            tag_el = card.select_one(".text-purple-700, .text-green-700")
            if tag_el:
                tag_text = tag_el.get_text(strip=True)
                if "New lowest" in tag_text:
                    price_tag = "New lowest!"
                elif "Lowest" in tag_text:
                    price_tag = "Lowest"

            return ScrapedDeal(
                game_id=f"psp_{raw_game_id}",
                title=title,
                cover_url=cover_url,
                region_code=region_code,
                price=price,
                original_price=original_price,
                discount_percent=discount_percent,
                currency=currency,
                sale_end_date=sale_end_date,
                platform=platform,
                price_tag=price_tag,
                page_number=page_number,
                position_on_page=position,
            )

        except Exception as e:
            logger.debug(f"[PSPrices] Card parse error: {e}")
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_price(text: str) -> float | None:
        """Extract a numeric price from text like '1,799' or '5,999'."""
        if not text or text.strip().upper() == "N/A":
            return None
        cleaned = re.sub(r"[^\d.,]", "", text)
        if not cleaned:
            return None
        # Indian / US format: commas are thousands separators
        cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
