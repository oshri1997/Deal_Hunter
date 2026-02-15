import unittest
from bot.helpers import _escape_md


class TestHelpers(unittest.TestCase):
    def test_escape_md_basic(self):
        """Test basic markdown escaping"""
        self.assertEqual(_escape_md("Hello World"), "Hello World")

    def test_escape_md_special_chars(self):
        """Test escaping special markdown characters"""
        # Test common special characters
        text = "Test-Game_2024"
        escaped = _escape_md(text)
        self.assertIn("\\-", escaped)
        self.assertIn("\\_", escaped)

    def test_escape_md_parentheses(self):
        """Test escaping parentheses"""
        text = "Game (2024)"
        escaped = _escape_md(text)
        self.assertIn("\\(", escaped)
        self.assertIn("\\)", escaped)

    def test_escape_md_dots(self):
        """Test escaping dots"""
        text = "Game v1.0"
        escaped = _escape_md(text)
        self.assertIn("\\.", escaped)

    def test_escape_md_empty_string(self):
        """Test escaping empty string"""
        self.assertEqual(_escape_md(""), "")


if __name__ == '__main__':
    unittest.main()
