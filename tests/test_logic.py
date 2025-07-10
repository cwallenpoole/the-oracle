import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import tempfile
import uuid

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logic.runes import RuneElement, RunicReading, RunicSystem, cast_single_rune, cast_three_norns, cast_five_cross, cast_seven_chakras
from logic.divination import create_reading, get_system, get_all_systems, is_supported
from logic.base import DivinationReading, DivinationType, DivinationRegistry, DivinationElement
from logic.iching_adapter import IChingSystem, IChingReading
from models.history import HistoryEntry


class TestRuneElement(unittest.TestCase):
    """Test cases for RuneElement functionality"""

    def test_rune_element_creation(self):
        """Test creating a RuneElement object"""
        rune = RuneElement(
            identifier="Fehu",
            name="Fehu",
            symbol="ᚠ",
            description="Wealth, cattle, prosperity",
            phonetic="F",
            element="Fire",
            deity="Freyr",
            reversed_meaning="Loss, greed, materialism",
            is_reversed=False
        )

        self.assertEqual(rune.name, "Fehu")
        self.assertEqual(rune.symbol, "ᚠ")
        self.assertEqual(rune.phonetic, "F")
        self.assertFalse(rune.is_reversed)

    def test_rune_element_display_meaning_normal(self):
        """Test getting display meaning for normal rune"""
        rune = RuneElement(
            identifier="Fehu",
            name="Fehu",
            symbol="ᚠ",
            description="Wealth, prosperity",
            phonetic="F",
            element="Fire",
            deity="Freyr",
            reversed_meaning="Loss, greed",
            is_reversed=False
        )

        meaning = rune.get_display_meaning()
        self.assertEqual(meaning, "Wealth, prosperity")

    def test_rune_element_display_meaning_reversed(self):
        """Test getting display meaning for reversed rune"""
        rune = RuneElement(
            identifier="Fehu",
            name="Fehu",
            symbol="ᚠ",
            description="Wealth, prosperity",
            phonetic="F",
            element="Fire",
            deity="Freyr",
            reversed_meaning="Loss, greed",
            is_reversed=True
        )

        meaning = rune.get_display_meaning()
        self.assertEqual(meaning, "Wealth, prosperity (Reversed: Loss, greed)")

    def test_rune_element_string_representation(self):
        """Test string representation of rune"""
        rune = RuneElement(
            identifier="Fehu",
            name="Fehu",
            symbol="ᚠ",
            description="Wealth, prosperity",
            phonetic="F",
            element="Fire",
            deity="Freyr",
            is_reversed=False
        )

        str_repr = str(rune)
        self.assertIn("Fehu", str_repr)
        self.assertIn("ᚠ", str_repr)


class TestRunicSystem(unittest.TestCase):
    """Test cases for RunicSystem functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.system = RunicSystem()

    def test_runic_system_creation(self):
        """Test creating a RunicSystem object"""
        self.assertEqual(self.system.divination_type, DivinationType.RUNES)
        self.assertEqual(self.system.get_system_name(), "Elder Futhark Runes")

    def test_get_all_elements(self):
        """Test getting all runes"""
        runes = self.system.get_all_elements()
        self.assertIsInstance(runes, list)
        self.assertEqual(len(runes), 24)  # Elder Futhark has 24 runes

        # Check that all items are RuneElement objects
        for rune in runes:
            self.assertIsInstance(rune, RuneElement)
            self.assertIsInstance(rune.name, str)
            self.assertIsInstance(rune.symbol, str)

    def test_get_element_by_identifier(self):
        """Test getting rune by identifier"""
        # Test valid rune name
        rune = self.system.get_element_by_identifier("Fehu")
        self.assertIsNotNone(rune)
        self.assertEqual(rune.name, "Fehu")

        # Test invalid rune name
        rune = self.system.get_element_by_identifier("InvalidRune")
        self.assertIsNone(rune)

    def test_get_element_by_name(self):
        """Test getting rune by name"""
        rune = self.system.get_element_by_name("Fehu")
        self.assertIsNotNone(rune)
        self.assertEqual(rune.name, "Fehu")

    def test_create_single_reading(self):
        """Test creating a single rune reading"""
        reading = self.system.create_reading("single")

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 1)
        self.assertEqual(reading.spread_type, "Single")

    def test_create_three_norns_reading(self):
        """Test creating a three norns reading"""
        reading = self.system.create_reading("three_norns")

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 3)
        self.assertEqual(reading.spread_type, "Three Norns")

    def test_create_five_cross_reading(self):
        """Test creating a five cross reading"""
        reading = self.system.create_reading("five_cross")

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 5)
        self.assertEqual(reading.spread_type, "Five Cross")

    def test_create_seven_chakras_reading(self):
        """Test creating a seven chakras reading"""
        reading = self.system.create_reading("seven_chakras")

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 7)
        self.assertEqual(reading.spread_type, "Seven Chakras")

    def test_create_invalid_spread(self):
        """Test creating reading with invalid spread type defaults to single"""
        reading = self.system.create_reading("invalid_spread")

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 1)


class TestRunicReading(unittest.TestCase):
    """Test cases for RunicReading functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.rune1 = RuneElement(
            identifier="Fehu",
            name="Fehu",
            symbol="ᚠ",
            description="Wealth",
            phonetic="F",
            element="Fire",
            deity="Freyr",
            is_reversed=False
        )
        self.rune2 = RuneElement(
            identifier="Uruz",
            name="Uruz",
            symbol="ᚢ",
            description="Strength",
            phonetic="U",
            element="Earth",
            deity="Thor",
            is_reversed=True
        )

    def test_runic_reading_creation(self):
        """Test creating a RunicReading object"""
        reading = RunicReading(
            runes=[self.rune1, self.rune2],
            spread_type="Two Rune Spread",
            spread_positions={"position_1": "Present", "position_2": "Future"}
        )

        self.assertEqual(len(reading.runes), 2)
        self.assertEqual(reading.spread_type, "Two Rune Spread")
        self.assertIn("position_1", reading.spread_positions)

    def test_runic_reading_get_elements(self):
        """Test getting elements from reading"""
        reading = RunicReading(
            runes=[self.rune1, self.rune2],
            spread_type="Test",
            spread_positions={}
        )

        elements = reading.get_elements()
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0], self.rune1)

    def test_runic_reading_get_primary_element(self):
        """Test getting primary element"""
        reading = RunicReading(
            runes=[self.rune1, self.rune2],
            spread_type="Test",
            spread_positions={}
        )

        primary = reading.get_primary_element()
        self.assertEqual(primary, self.rune1)

    def test_runic_reading_has_transition(self):
        """Test that runic readings don't have transitions"""
        reading = RunicReading(
            runes=[self.rune1],
            spread_type="Test",
            spread_positions={}
        )

        self.assertFalse(reading.has_transition())

    def test_runic_reading_get_summary(self):
        """Test getting reading summary"""
        reading = RunicReading(
            runes=[self.rune1, self.rune2],
            spread_type="Test Spread",
            spread_positions={}
        )

        summary = reading.get_summary()
        self.assertIn("Test Spread", summary)
        self.assertIn("Fehu", summary)
        self.assertIn("Uruz", summary)

    def test_runic_reading_get_display_data(self):
        """Test getting display data"""
        reading = RunicReading(
            runes=[self.rune1],
            spread_type="Test",
            spread_positions={"position_1": "Present"}
        )

        data = reading.get_display_data()
        self.assertEqual(data["type"], "runic")
        self.assertEqual(data["spread_type"], "Test")
        self.assertEqual(len(data["runes"]), 1)
        self.assertEqual(data["runes"][0]["name"], "Fehu")

    def test_runic_reading_string_representation(self):
        """Test string representation"""
        reading = RunicReading(
            runes=[self.rune1],
            spread_type="Test",
            spread_positions={"position_1": "Present"}
        )

        str_repr = str(reading)
        self.assertIn("Test", str_repr)
        self.assertIn("Fehu", str_repr)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""

    def test_cast_single_rune(self):
        """Test casting a single rune"""
        reading = cast_single_rune()

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 1)
        self.assertEqual(reading.spread_type, "Single")

    def test_cast_three_norns(self):
        """Test casting three norns"""
        reading = cast_three_norns()

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 3)
        self.assertEqual(reading.spread_type, "Three Norns")

    def test_cast_five_cross(self):
        """Test casting five cross"""
        reading = cast_five_cross()

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 5)
        self.assertEqual(reading.spread_type, "Five Cross")

    def test_cast_seven_chakras(self):
        """Test casting seven chakras"""
        reading = cast_seven_chakras()

        self.assertIsInstance(reading, RunicReading)
        self.assertEqual(len(reading.runes), 7)
        self.assertEqual(reading.spread_type, "Seven Chakras")


class TestDivinationRegistry(unittest.TestCase):
    """Test cases for divination registry functionality"""

    def test_get_all_systems(self):
        """Test getting all registered systems"""
        systems = get_all_systems()
        self.assertIsInstance(systems, dict)
        self.assertIn(DivinationType.RUNES, systems)
        self.assertIn(DivinationType.ICHING, systems)

    def test_get_system(self):
        """Test getting specific systems"""
        runic_system = get_system(DivinationType.RUNES)
        self.assertIsInstance(runic_system, RunicSystem)

        iching_system = get_system(DivinationType.ICHING)
        self.assertIsInstance(iching_system, IChingSystem)

    def test_is_supported(self):
        """Test checking if divination types are supported"""
        self.assertTrue(is_supported(DivinationType.RUNES))
        self.assertTrue(is_supported(DivinationType.ICHING))
        self.assertFalse(is_supported(DivinationType.TAROT))

    def test_create_reading(self):
        """Test creating readings through the registry"""
        # Test default (I Ching)
        reading = create_reading()
        self.assertIsInstance(reading, IChingReading)

        # Test specific type
        reading = create_reading(DivinationType.RUNES)
        self.assertIsInstance(reading, RunicReading)

    def test_create_reading_unsupported_type(self):
        """Test creating reading with unsupported type"""
        with self.assertRaises(ValueError):
            create_reading(DivinationType.TAROT)


class TestHistoryEntryIdGeneration(unittest.TestCase):
    """Test cases for reading ID generation"""

    def test_reading_id_generation(self):
        """Test generating a reading ID through HistoryEntry"""
        entry = HistoryEntry(
            username="testuser",
            question="Test question?",
            hexagram="Test hexagram",
            reading_data="Test reading"
        )

        self.assertIsInstance(entry.reading_id, str)
        self.assertGreater(len(entry.reading_id), 0)
        self.assertTrue(entry.reading_id.startswith("testuser-") or len(entry.reading_id) == 12)

    def test_reading_id_uniqueness(self):
        """Test that reading IDs are unique"""
        entry1 = HistoryEntry("user1", "Q1", "H1", reading_data="R1")
        entry2 = HistoryEntry("user1", "Q2", "H2", reading_data="R2")

        self.assertNotEqual(entry1.reading_id, entry2.reading_id)

    def test_reading_id_with_custom_id(self):
        """Test creating entry with custom reading ID"""
        custom_id = "custom-test-id"
        entry = HistoryEntry(
            username="testuser",
            question="Test question?",
            hexagram="Test hexagram",
            reading_data="Test reading",
            reading_id=custom_id
        )

        self.assertEqual(entry.reading_id, custom_id)


class TestIChingAdapter(unittest.TestCase):
    """Test cases for I Ching adapter functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.system = IChingSystem()

    def test_iching_system_creation(self):
        """Test creating an IChingSystem object"""
        self.assertEqual(self.system.divination_type, DivinationType.ICHING)
        self.assertEqual(self.system.get_system_name(), "I Ching")

    @patch('logic.iching.get_hexagram_section')
    def test_iching_system_get_hexagram(self, mock_get_section):
        """Test getting hexagram through adapter"""
        from logic.iching import IChingHexagram

        # Create a mock hexagram object
        mock_hexagram = MagicMock()
        mock_hexagram.Number = 1
        mock_hexagram.Title = "Creative"
        mock_hexagram.Symbol = "☰"
        mock_hexagram.About.Description = "Test description"
        mock_get_section.return_value = mock_hexagram

        # Test getting hexagram by identifier
        element = self.system.get_element_by_identifier("1")
        self.assertIsNotNone(element)
        self.assertEqual(element.name, "Creative")
        mock_get_section.assert_called_with(1)

    def test_iching_system_methods(self):
        """Test basic IChingSystem methods"""
        self.assertIsInstance(self.system.get_system_description(), str)
        self.assertGreater(len(self.system.get_system_description()), 0)

    def test_create_iching_reading(self):
        """Test creating an I Ching reading"""
        reading = self.system.create_reading()
        self.assertIsInstance(reading, IChingReading)


class TestLogicPerformance(unittest.TestCase):
    """Test cases for logic performance"""

    def test_rune_casting_performance(self):
        """Test that rune casting performs well"""
        import time

        start_time = time.time()
        for _ in range(10):
            cast_single_rune()
        end_time = time.time()

        # Should complete 10 castings in less than 1 second
        self.assertLess(end_time - start_time, 1.0)

    def test_reading_id_generation_performance(self):
        """Test that reading ID generation performs well"""
        import time

        start_time = time.time()
        ids = []
        for i in range(100):
            entry = HistoryEntry(f"user{i}", "question", "hexagram", reading_data="reading")
            ids.append(entry.reading_id)
        end_time = time.time()

        # Should generate 100 IDs in less than 1 second
        self.assertLess(end_time - start_time, 1.0)

        # All IDs should be unique
        self.assertEqual(len(ids), len(set(ids)))


class TestLogicIntegration(unittest.TestCase):
    """Test cases for logic integration workflows"""

    def test_rune_reading_integration(self):
        """Test full rune reading workflow"""
        # Create system
        system = RunicSystem()

        # Create reading
        reading = system.create_reading("three_norns")

        # Verify reading structure
        self.assertEqual(len(reading.runes), 3)

        # Test display data
        display_data = reading.get_display_data()
        self.assertEqual(display_data["type"], "runic")
        self.assertEqual(len(display_data["runes"]), 3)

        # Test string representation
        str_repr = str(reading)
        self.assertIn("Three Norns", str_repr)

    def test_divination_workflow(self):
        """Test complete divination workflow"""
        # Test registry functionality
        systems = get_all_systems()
        self.assertGreater(len(systems), 0)

        # Test system retrieval
        runic_system = get_system(DivinationType.RUNES)
        self.assertIsNotNone(runic_system)

        # Test reading creation
        reading = runic_system.create_reading("single")
        self.assertIsInstance(reading, RunicReading)

        # Test element retrieval
        all_runes = runic_system.get_all_elements()
        self.assertEqual(len(all_runes), 24)

        # Test specific element lookup
        fehu = runic_system.get_element_by_name("Fehu")
        self.assertIsNotNone(fehu)
        self.assertEqual(fehu.name, "Fehu")


if __name__ == '__main__':
    unittest.main()
