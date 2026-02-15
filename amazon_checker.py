import logging
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AmazonChecker:
    """Check Amazon India PlayStation gift card availability"""
    
    URL = "https://www.amazon.in/Playstation-Gift-Redeemable-Flat-Cashback/dp/B0C1H473H8"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.last_status = None
    
    async def check_availability(self) -> tuple[bool, str]:
        """Check if gift card is available
        
        Returns:
            (is_available, message)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.URL, headers=self.headers, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error(f"Amazon returned status {resp.status}")
                        return False, f"Error: Status {resp.status}"
                    
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Check for unavailable message
                    unavailable = soup.find('span', class_='a-size-medium a-color-success primary-availability-message')
                    
                    if unavailable and 'unavailable' in unavailable.get_text().lower():
                        return False, "Currently unavailable"
                    
                    # Check for available/in stock
                    available = soup.find('span', class_='a-size-medium a-color-success')
                    if available and 'in stock' in available.get_text().lower():
                        return True, "In Stock!"
                    
                    # Check add to cart button
                    add_to_cart = soup.find('input', {'id': 'add-to-cart-button'})
                    if add_to_cart:
                        return True, "Available (Add to Cart button found)"
                    
                    return False, "Status unknown"
                    
        except Exception as e:
            logger.error(f"Amazon checker error: {e}")
            return False, f"Error: {str(e)}"
