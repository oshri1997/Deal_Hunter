import logging
import asyncio

logger = logging.getLogger(__name__)

URL = "https://www.offgamers.com/product/playstation-store-gift-cards?region_id=492c3ca6-c4e6-47fc-b274-c2c35031b271"


async def check_offgamers_stock() -> tuple[list[str], list[str]]:
    """Return (in_stock, out_of_stock) using Playwright to render the Vue SPA."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_selector(".h-denom-card", timeout=15000)

            in_stock, out_of_stock = [], []
            for card in await page.query_selector_all(".h-denom-card"):
                span = await card.query_selector("span.text-body1")
                if not span:
                    continue
                text = (await span.inner_text()).strip()
                classes = await span.get_attribute("class") or ""
                if "h-denom-card--dimmed" in classes:
                    out_of_stock.append(text)
                else:
                    in_stock.append(text)

            return in_stock, out_of_stock
        finally:
            await browser.close()
