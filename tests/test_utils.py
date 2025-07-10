import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import tempfile
import sqlite3
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.db_utils import init_db
from utils.hexagram_utils import get_hexagram_symbols, create_hexagram_url_name
from utils.template_utils import register_template_filters
from utils.calendar_utils import get_chinese_year_and_animal, get_mayan_calendars
from utils.trigram_utils import get_trigram_info


class TestDBUtils(unittest.TestCase):
    """Test cases for database utilities"""

    def setUp(self):
        """Set up test database"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        os.close(self.test_db_fd)

    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_init_db_creates_tables(self):
        """Test that init_db creates required tables"""
        # Save original DB_FILE
        import utils.db_utils
        original_db_file = utils.db_utils.DB_FILE

        try:
            # Temporarily set DB_FILE to test database
            utils.db_utils.DB_FILE = self.test_db_path

            init_db()

            # Verify tables exist
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ['users', 'history', 'user_settings', 'llm_requests']
            for table in expected_tables:
                self.assertIn(table, tables)

            conn.close()

        finally:
            # Restore original DB_FILE
            utils.db_utils.DB_FILE = original_db_file


class TestHexagramUtils(unittest.TestCase):
    """Test cases for hexagram utilities"""

    def test_get_hexagram_symbols_returns_dict(self):
        """Test that get_hexagram_symbols returns a dictionary"""
        symbols = get_hexagram_symbols()
        self.assertIsInstance(symbols, dict)
        self.assertGreater(len(symbols), 0)

    def test_get_hexagram_symbols_has_expected_keys(self):
        """Test that hexagram symbols have expected structure"""
        symbols = get_hexagram_symbols()

        # Check that we have hexagrams 1-64
        self.assertIn(1, symbols)
        self.assertIn(64, symbols)

    def test_create_hexagram_url_name(self):
        """Test hexagram URL name creation"""
        # Test normal case
        url_name = create_hexagram_url_name("The Creative")
        self.assertEqual(url_name, "the_creative")

        # Test with special characters
        url_name = create_hexagram_url_name("Difficulty at the Beginning")
        self.assertEqual(url_name, "difficulty_at_the_beginning")

        # Test with numbers
        url_name = create_hexagram_url_name("The 64 Hexagrams")
        self.assertEqual(url_name, "the_64_hexagrams")

    def test_create_hexagram_url_name_edge_cases(self):
        """Test edge cases for hexagram URL name creation"""
        # Empty string
        url_name = create_hexagram_url_name("")
        self.assertEqual(url_name, "")

        # Special characters
        url_name = create_hexagram_url_name("Test/Name & Title")
        self.assertEqual(url_name, "name_title")

        # Multiple spaces
        url_name = create_hexagram_url_name("Multiple   Spaces")
        self.assertEqual(url_name, "multiple_spaces")


class TestTrigramUtils(unittest.TestCase):
    """Test cases for trigram utilities"""

    def test_get_trigram_info_returns_list(self):
        """Test that get_trigram_info returns a list"""
        trigrams = get_trigram_info()
        self.assertIsInstance(trigrams, list)
        self.assertEqual(len(trigrams), 8)

    def test_get_trigram_info_has_expected_structure(self):
        """Test that trigram info has expected structure"""
        trigrams = get_trigram_info()

        # Check structure of a trigram entry
        for trigram in trigrams:
            self.assertIn('id', trigram)
            self.assertIn('name', trigram)
            self.assertIn('symbol', trigram)
            self.assertIn('chinese', trigram)
            self.assertIn('attributes', trigram)
            self.assertIn('description', trigram)

    def test_trigram_info_content(self):
        """Test trigram info content"""
        trigrams = get_trigram_info()

        # Check that we have the expected trigrams
        trigram_names = [t['name'] for t in trigrams]
        expected_names = ['Heaven', 'Earth', 'Thunder', 'Water', 'Mountain', 'Wind', 'Fire', 'Lake']

        for name in expected_names:
            self.assertIn(name, trigram_names)

    def test_trigram_info_consistency(self):
        """Test that trigram info is consistent"""
        trigrams = get_trigram_info()

        for trigram in trigrams:
            # Each trigram should have a non-empty description
            self.assertGreater(len(trigram['description']), 0)

            # Attributes should be a list
            self.assertIsInstance(trigram['attributes'], list)
            self.assertGreater(len(trigram['attributes']), 0)


class TestTemplateUtils(unittest.TestCase):
    """Test cases for template utilities"""

    def test_register_template_filters(self):
        """Test that template filters are registered"""
        from flask import Flask

        app = Flask(__name__)

        # Register filters
        register_template_filters(app)

        # Check that filters were registered
        self.assertIn('markdown', app.jinja_env.filters)

    def test_markdown_filter(self):
        """Test markdown filter functionality"""
        from flask import Flask

        app = Flask(__name__)
        register_template_filters(app)

        # Test markdown conversion
        with app.app_context():
            markdown_filter = app.jinja_env.filters['markdown']
            result = markdown_filter("# Test Header")
            self.assertIn("<h1>", result)
            self.assertIn("Test Header", result)


class TestCalendarUtils(unittest.TestCase):
    """Test cases for calendar utilities"""

    def test_get_chinese_year_and_animal(self):
        """Test Chinese zodiac calculation"""
        # Test with a known date
        result = get_chinese_year_and_animal(2023, 12, 25)
        self.assertIsInstance(result, dict)
        self.assertIn('chinese_year', result)
        self.assertIn('animal', result)
        self.assertIn('element', result)
        self.assertIn('yin_yang', result)

    def test_chinese_zodiac_animals(self):
        """Test that Chinese zodiac returns valid animals"""
        result = get_chinese_year_and_animal(2024, 2, 15)  # Dragon year

        valid_animals = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
                        "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]
        self.assertIn(result['animal'], valid_animals)

        valid_elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
        self.assertIn(result['element'], valid_elements)

        self.assertIn(result['yin_yang'], ['Yin', 'Yang'])

    def test_get_mayan_calendars(self):
        """Test Mayan calendar calculation"""
        # Test with a known date
        result = get_mayan_calendars(2023, 12, 25)
        self.assertIsInstance(result, dict)
        self.assertIn('tzolkin', result)
        self.assertIn('haab', result)
        self.assertIn('long_count', result)
        self.assertIn('lord_of_night', result)

    def test_mayan_calendar_structure(self):
        """Test Mayan calendar data structure"""
        result = get_mayan_calendars(2023, 6, 15)

        # Check Tzolk'in structure
        tzolkin = result['tzolkin']
        self.assertIn('number', tzolkin)
        self.assertIn('day_name', tzolkin)
        self.assertIn('formatted', tzolkin)
        self.assertGreaterEqual(tzolkin['number'], 1)
        self.assertLessEqual(tzolkin['number'], 13)

        # Check Haab structure
        haab = result['haab']
        self.assertIn('day', haab)
        self.assertIn('month', haab)
        self.assertIn('formatted', haab)

        # Check Long Count structure
        long_count = result['long_count']
        self.assertIn('baktun', long_count)
        self.assertIn('katun', long_count)
        self.assertIn('tun', long_count)
        self.assertIn('winal', long_count)
        self.assertIn('kin', long_count)
        self.assertIn('formatted', long_count)

    def test_calendar_utils_edge_cases(self):
        """Test edge cases for calendar utilities"""
        # Test with leap year
        result = get_chinese_year_and_animal(2024, 2, 29)
        self.assertIsInstance(result, dict)

        # Test with year boundaries
        result = get_mayan_calendars(2024, 1, 1)
        self.assertIsInstance(result, dict)


class TestUtilsPerformance(unittest.TestCase):
    """Test performance of utility functions"""

    def test_hexagram_symbols_performance(self):
        """Test that hexagram symbols can be retrieved quickly"""
        import time

        start_time = time.time()
        for _ in range(100):
            get_hexagram_symbols()
        end_time = time.time()

        # Should complete 100 calls in less than 1 second
        self.assertLess(end_time - start_time, 1.0)

    def test_trigram_info_performance(self):
        """Test that trigram info can be retrieved quickly"""
        import time

        start_time = time.time()
        for _ in range(100):
            get_trigram_info()
        end_time = time.time()

        # Should complete 100 calls in less than 1 second
        self.assertLess(end_time - start_time, 1.0)

    def test_calendar_utils_performance(self):
        """Test that calendar utilities perform well"""
        import time

        start_time = time.time()
        for _ in range(50):
            get_chinese_year_and_animal(2023, 6, 15)
            get_mayan_calendars(2023, 6, 15)
        end_time = time.time()

        # Should complete 50 iterations in less than 1 second
        self.assertLess(end_time - start_time, 1.0)


if __name__ == '__main__':
    unittest.main()
