import logging
import aiohttp

logger = logging.getLogger(__name__)

API_URL = "https://sls.offgamers.com/offer/search/lite"
API_PARAMS = {
    "service_id": "fdf75033-56ee-4ce6-929c-1f9c93a4c642",
    "brand_id": "1f49ed55-574b-432d-b63a-fde20cbb5097",
    "region_id": "492c3ca6-c4e6-47fc-b274-c2c35031b271",
    "country": "IN",
    "currency": "USD",
}


async def check_offgamers_stock() -> tuple[list[str], list[str]]:
    """Return (in_stock, out_of_stock) by querying the OffGamers API directly."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            API_URL, params=API_PARAMS, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

    in_stock, out_of_stock = [], []
    for group in data.get("payload", {}).get("results", []):
        for offer in group.get("offer_results", []):
            title = offer.get("title", "").strip()
            if not title:
                continue
            if offer.get("is_sold_out"):
                out_of_stock.append(title)
            else:
                in_stock.append(title)

    return in_stock, out_of_stock
