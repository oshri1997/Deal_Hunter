import unittest
from config import config


class TestConfig(unittest.TestCase):
    def test_regions_exist(self):
        """Test that required regions are configured"""
        self.assertIn("IL", config.REGIONS)
        self.assertIn("US", config.REGIONS)
        self.assertIn("IN", config.REGIONS)

    def test_region_has_required_fields(self):
        """Test that each region has required fields"""
        for region_code, region_info in config.REGIONS.items():
            self.assertIn("name", region_info)
            self.assertIn("flag", region_info)
            self.assertIn("currency", region_info)
            self.assertIn("currency_symbol", region_info)
            self.assertIn("store_url", region_info)

    def test_israel_config(self):
        """Test Israel region configuration"""
        il = config.REGIONS["IL"]
        self.assertEqual(il["name"], "Israel")
        self.assertEqual(il["currency"], "ILS")
        self.assertEqual(il["currency_symbol"], "₪")

    def test_usa_config(self):
        """Test USA region configuration"""
        us = config.REGIONS["US"]
        self.assertEqual(us["name"], "USA")
        self.assertEqual(us["currency"], "USD")
        self.assertEqual(us["currency_symbol"], "$")

    def test_india_config(self):
        """Test India region configuration"""
        india = config.REGIONS["IN"]
        self.assertEqual(india["name"], "India")
        self.assertEqual(india["currency"], "INR")
        self.assertEqual(india["currency_symbol"], "₹")

    def test_bot_token_exists(self):
        """Test that bot token is configured"""
        self.assertIsNotNone(config.TELEGRAM_BOT_TOKEN)
        self.assertIsInstance(config.TELEGRAM_BOT_TOKEN, str)

    def test_database_url_exists(self):
        """Test that database URL is configured"""
        self.assertIsNotNone(config.DATABASE_URL)
        self.assertIn("postgresql", config.DATABASE_URL)


if __name__ == '__main__':
    unittest.main()
