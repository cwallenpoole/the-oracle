import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logic.iching import (
    Reading, IChingHexagram, IChingAbout, IChingLine,
    cast_hexagrams, get_hexagram, get_hexagram_section,
    get_text_from_hexagram, get_num_from_hexagram
)

class TestIChingStructures(unittest.TestCase):
    """Test cases for I Ching data structures"""

    def test_iching_line_creation(self):
        """Test creating IChingLine object"""
        line = IChingLine(Quote="Test quote", Text="Test text")
        self.assertEqual(line.Quote, "Test quote")
        self.assertEqual(line.Text, "Test text")

    def test_iching_about_creation(self):
        """Test creating IChingAbout object"""
        about = IChingAbout(Above="Heaven", Below="Earth", Description="Test description")
        self.assertEqual(about.Above, "Heaven")
        self.assertEqual(about.Below, "Earth")
        self.assertEqual(about.Description, "Test description")

    def test_reading_creation(self):
        """Test creating Reading object"""
        reading = Reading()
        self.assertIsNone(reading.Current)
        self.assertIsNone(reading.Future)
        self.assertFalse(reading.has_transition())

    def test_reading_with_transition(self):
        """Test Reading object with transition"""
        reading = Reading()
        reading.Current = MagicMock()
        reading.Future = MagicMock()
        self.assertTrue(reading.has_transition())

    def test_reading_str_representation(self):
        """Test string representation of Reading"""
        reading = Reading()

        # Mock hexagram objects
        current_hex = MagicMock()
        current_hex.Number = 31
        current_hex.Title = "Influence"
        current_hex.About.Above = "Lake"
        current_hex.About.Below = "Mountain"
        current_hex.About.Description = "Test description"

        future_hex = MagicMock()
        future_hex.Number = 32
        future_hex.Title = "Duration"
        future_hex.About.Above = "Thunder"
        future_hex.About.Below = "Wind"
        future_hex.About.Description = "Future description"

        reading.Current = current_hex
        reading.Future = future_hex

        str_repr = str(reading)
        self.assertIn("31 Influence", str_repr)
        self.assertIn("transitioning to", str_repr)
        self.assertIn("32 Duration", str_repr)


class TestIChingFunctions(unittest.TestCase):
    """Test cases for I Ching utility functions"""

    def test_get_text_from_hexagram(self):
        """Test extracting text from hexagram string"""
        result = get_text_from_hexagram("31 Influence")
        self.assertEqual(result, "Influence")

        result = get_text_from_hexagram("1 Creative")
        self.assertEqual(result, "Creative")

    def test_get_num_from_hexagram(self):
        """Test extracting number from hexagram string"""
        result = get_num_from_hexagram("31 Influence")
        self.assertEqual(result, 31)

        result = get_num_from_hexagram("1 Creative")
        self.assertEqual(result, 1)

    def test_get_hexagram(self):
        """Test getting hexagram from line pattern"""
        # Test a known pattern
        result = get_hexagram('LLLLLL')
        self.assertEqual(result, '1 Creative')

        result = get_hexagram('GGGGGG')
        self.assertEqual(result, '2 Receptive')

        # Test unknown pattern
        result = get_hexagram('UNKNOWN')
        self.assertIsNone(result)

    @patch('random.choices')
    def test_cast_hexagrams_no_transition(self, mock_choices):
        """Test casting hexagrams without transition"""
        # Mock random choices to return consistent results
        # [0, 1, 1] would result in 'L' (no transition)
        mock_choices.side_effect = [
            [0, 1, 1],  # Line 1: L
            [0, 1, 1],  # Line 2: L
            [0, 1, 1],  # Line 3: L
            [0, 1, 1],  # Line 4: L
            [0, 1, 1],  # Line 5: L
            [0, 1, 1],  # Line 6: L
        ]

        with patch('logic.iching.get_hexagram_section_from_hexagram') as mock_get_section:
            mock_hexagram = MagicMock()
            mock_get_section.return_value = mock_hexagram

            reading = cast_hexagrams()

            self.assertIsNotNone(reading.Current)
            self.assertIsNone(reading.Future)
            self.assertFalse(reading.has_transition())

    @patch('random.choices')
    def test_cast_hexagrams_with_transition(self, mock_choices):
        """Test casting hexagrams with transition"""
        # Mock random choices to create changing lines
        # [1, 1, 1] would result in 'G' changing to 'L'
        mock_choices.side_effect = [
            [1, 1, 1],  # Line 1: G -> L (changing)
            [0, 1, 1],  # Line 2: L (stable)
            [0, 1, 1],  # Line 3: L (stable)
            [0, 1, 1],  # Line 4: L (stable)
            [0, 1, 1],  # Line 5: L (stable)
            [0, 1, 1],  # Line 6: L (stable)
        ]

        with patch('logic.iching.get_hexagram_section_from_hexagram') as mock_get_section:
            mock_current = MagicMock()
            mock_future = MagicMock()
            mock_get_section.side_effect = [mock_current, mock_future]

            reading = cast_hexagrams()

            self.assertIsNotNone(reading.Current)
            self.assertIsNotNone(reading.Future)
            self.assertTrue(reading.has_transition())


class TestIChingTextParsing(unittest.TestCase):
    """Test cases for I Ching text parsing functions"""

    @patch('logic.iching.get_text')
    def test_get_hexagram_section_not_found(self, mock_get_text):
        """Test getting hexagram section that doesn't exist"""
        mock_get_text.return_value = "## 1. Creative\n\nSome content"

        hexagram = get_hexagram_section(999)
        self.assertIsNone(hexagram)


class TestPerformance(unittest.TestCase):
    """Performance-related tests"""

    def test_cast_hexagrams_performance(self):
        """Test that casting hexagrams is reasonably fast"""
        import time

        start_time = time.time()
        for _ in range(100):
            with patch('logic.iching.get_hexagram_section_from_hexagram'):
                cast_hexagrams()
        end_time = time.time()

        # Should complete 100 castings in less than 1 second
        elapsed = end_time - start_time
        self.assertLess(elapsed, 1.0, f"Casting 100 hexagrams took {elapsed:.3f}s, should be < 1.0s")

    @patch('logic.iching.get_text')
    def test_text_parsing_performance(self, mock_get_text):
        """Test that text parsing is reasonably fast"""
        import time

        # Create a large mock text
        mock_text = "## 1. Creative ☰☰\n\n> above Heaven\n> below Heaven\n\nDescription\n\n### THE JUDGEMENT\n\n> Quote\n\nText\n\n#### THE IMAGE\n\n> Quote\n\nText\n\n#### THE LINES\n\n> **Line**\n\nText\n\n" * 64
        mock_get_text.return_value = mock_text

        start_time = time.time()
        for i in range(1, 11):  # Parse 10 different hexagrams
            get_hexagram_section(i)
        end_time = time.time()

        # Should complete 10 parsings in less than 0.5 seconds
        elapsed = end_time - start_time
        self.assertLess(elapsed, 0.5, f"Parsing 10 hexagrams took {elapsed:.3f}s, should be < 0.5s")


if __name__ == '__main__':
    unittest.main()
