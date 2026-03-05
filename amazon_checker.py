import logging
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AmazonChecker:
    URL = "https://www.amazon.in/Playstation-Gift-Redeemable-Flat-Cashback/dp/B0C1H473H8"
    last_status = None

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
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
                            await asyncio.sleep(3)
                            continue
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        # Primary: check the #availability div (most reliable)
                        avail_div = soup.find('div', id='availability')
                        if avail_div:
                            avail_text = avail_div.get_text().strip().lower()
                            if 'unavailable' in avail_text:
                                return False, "Currently unavailable"
                            if 'in stock' in avail_text:
                                return True, "In Stock!"
                        # Secondary: check for Add to Cart button
                        if soup.find('input', {'id': 'add-to-cart-button'}):
                            return True, "Available (Add to Cart button found)"
                        return False, "Currently unavailable"
            except Exception as e:
                last_error = f"Error: {str(e)}"
                logger.error(f"Amazon checker error (attempt {attempt+1}): {e}")
                await asyncio.sleep(3)
        return False, last_error
