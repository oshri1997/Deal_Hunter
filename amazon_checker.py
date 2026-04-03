import logging
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


AMAZON_URL_2 = "https://www.amazon.in/Rs-1000-Sony-PlayStation-Delivery-Digital/dp/B07K6RYVHR"


class AmazonChecker:
    URL = "https://www.amazon.in/Playstation-Gift-Redeemable-Flat-Cashback/dp/B0C1H473H8"
    last_status = None

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }

    async def check_availability(self) -> tuple[bool, str]:
        import asyncio
        last_error = "Status unknown"
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.URL, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            last_error = f"Error: Status {resp.status}"
                            logger.warning(f"Amazon checker HTTP {resp.status} (attempt {attempt+1})")
                            await asyncio.sleep(3)
                            continue
                        html = await resp.text()
                        return self._parse_availability(html)
            except Exception as e:
                last_error = f"Error: {str(e)}"
                logger.error(f"Amazon checker error (attempt {attempt+1}): {e}")
                await asyncio.sleep(3)
        return False, last_error

    def _parse_availability(self, html: str) -> tuple[bool, str]:
        """Parse Amazon product page to determine availability.
        
        Checks multiple indicators since e-gift cards have different
        page structure than physical products.
        """
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text().lower()

        # --- UNAVAILABLE signals (check first) ---
        # 1. Classic #availability div
        avail_div = soup.find('div', id='availability')
        if avail_div:
            avail_text = avail_div.get_text().strip().lower()
            if 'currently unavailable' in avail_text:
                return False, "Currently unavailable"
            if 'in stock' in avail_text:
                return True, "In Stock"

        # 2. "Currently unavailable" anywhere prominent on the page
        unavail_span = soup.find(string=lambda t: t and 'currently unavailable' in t.lower())
        if unavail_span:
            return False, "Currently unavailable"

        # --- AVAILABLE signals ---
        # 3. "Add to Cart" button (physical products)
        if soup.find('input', {'id': 'add-to-cart-button'}):
            return True, "Available (Add to Cart found)"

        # 4. "Buy Now" button (common for gift cards)
        if soup.find('input', {'id': 'buy-now-button'}):
            return True, "Available (Buy Now found)"

        # 5. Gift card specific: "Send e-Gift Card" or denomination selector
        # Amazon IN gift cards use a "gc-buy-box" or similar gift card UI
        gc_buy_box = soup.find('div', id='gc-buy-box')
        if gc_buy_box:
            return True, "Available (Gift Card buy box found)"

        # 6. Check for any submit button with "add to cart" or "buy" text
        for btn in soup.find_all(['input', 'button', 'span']):
            btn_text = btn.get_text().strip().lower() if btn.name != 'input' else (btn.get('value', '') or '').lower()
            btn_id = (btn.get('id') or '').lower()
            btn_name = (btn.get('name') or '').lower()
            if any(kw in btn_text for kw in ['add to cart', 'buy now', 'send e-gift']):
                return True, f"Available ({btn_text.strip()[:30]})"
            if any(kw in btn_id for kw in ['add-to-cart', 'buy-now', 'submit.buy', 'submit.add-to-cart']):
                return True, f"Available (button id: {btn_id[:30]})"

        # 7. Check for gift card denomination/amount input
        # If there's a price input or denomination selector, the card is likely available
        gc_amount = soup.find('input', {'id': 'custom-amount'}) or soup.find('input', {'name': 'gcCustomAmount'})
        if gc_amount:
            return True, "Available (gift card amount input found)"

        # 8. Check for "a]ddToCart" form action (fallback)
        add_form = soup.find('form', {'id': 'addToCart'})
        if add_form:
            return True, "Available (addToCart form found)"

        # If page is very short, it's likely a CAPTCHA or bot-detection page
        if len(html) < 5000:
            return False, "Could not determine (page too short — possible CAPTCHA)"

        return False, "Could not determine availability (no known indicators found)"
