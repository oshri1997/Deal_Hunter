import unittest
from unittest.mock import Mock, patch, AsyncMock
from scraper.psprices_new import PSPricesScraper, ScrapedDeal
from datetime import datetime


class TestPSPricesScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = PSPricesScraper()

    def test_parse_price_valid(self):
        """Test price parsing with valid input"""
        self.assertEqual(self.scraper._parse_price("1,799"), 1799.0)
        self.assertEqual(self.scraper._parse_price("5,999"), 5999.0)
        self.assertEqual(self.scraper._parse_price("199"), 199.0)

    def test_parse_price_invalid(self):
        """Test price parsing with invalid input"""
        self.assertIsNone(self.scraper._parse_price("N/A"))
        self.assertIsNone(self.scraper._parse_price(""))
        self.assertIsNone(self.scraper._parse_price("Free"))

    def test_region_map(self):
        """Test region code mapping"""
        self.assertEqual(self.scraper.REGION_MAP["IL"], "il")
        self.assertEqual(self.scraper.REGION_MAP["US"], "us")
        self.assertEqual(self.scraper.REGION_MAP["IN"], "in")

    @patch('scraper.psprices_new.cloudscraper.create_scraper')
    def test_get_scraper_creates_new_session(self, mock_create):
        """Test scraper session creation"""
        mock_scraper = Mock()
        mock_create.return_value = mock_scraper
        
        scraper = self.scraper._get_scraper(force_new=True)
        
        mock_create.assert_called_once()
        self.assertEqual(scraper, mock_scraper)


class TestScrapedDeal(unittest.TestCase):
    def test_scraped_deal_creation(self):
        """Test ScrapedDeal dataclass creation"""
        deal = ScrapedDeal(
            game_id="psp_123",
            title="Test Game",
            cover_url="https://example.com/cover.jpg",
            region_code="IL",
            price=199.0,
            original_price=299.0,
            discount_percent=33,
            currency="ILS",
            sale_end_date=datetime(2026, 12, 31),
            platform="PS5",
            price_tag="New lowest!",
            page_number=1,
            position_on_page=0
        )
        
        self.assertEqual(deal.game_id, "psp_123")
        self.assertEqual(deal.title, "Test Game")
        self.assertEqual(deal.discount_percent, 33)
        self.assertEqual(deal.region_code, "IL")


if __name__ == '__main__':
    unittest.main()
