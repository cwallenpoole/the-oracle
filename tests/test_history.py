import unittest
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.history import History, HistoryEntry
from logic.iching import Reading, IChingHexagram, IChingAbout, IChingLine

class TestHistoryEntry(unittest.TestCase):
    """Test cases for the HistoryEntry model"""

    def setUp(self):
        """Set up test data"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()

        # Initialize test database
        conn = sqlite3.connect(self.test_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS history (
                        username TEXT,
                        question TEXT,
                        hexagram TEXT,
                        reading TEXT,
                        reading_dt TEXT
                     )''')
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up after tests"""
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    def _create_mock_reading(self):
        """Create a mock Reading object for testing"""
        reading = Reading()
        reading.Current = MagicMock()
        reading.Current.Number = 31
        reading.Current.Title = "Influence"
        reading.Current.Symbol = "☱☶"
        reading.Future = None
        return reading

    def test_history_entry_creation_with_string(self):
        """Test creating HistoryEntry with string reading"""
        entry = HistoryEntry("testuser", "Test question?", "31 Influence", "Test reading response")
        entry.db_file = self.test_db_path

        self.assertEqual(entry.username, "testuser")
        self.assertEqual(entry.question, "Test question?")
        self.assertEqual(entry.hexagram, "31 Influence")
        self.assertEqual(entry.get_reading_string(), "Test reading response")

    def test_history_entry_creation_with_reading_object(self):
        """Test creating HistoryEntry with Reading object"""
        mock_reading = self._create_mock_reading()
        entry = HistoryEntry("testuser", "Test question?", "31 Influence", mock_reading)
        entry.db_file = self.test_db_path

        self.assertEqual(entry.username, "testuser")
        self.assertEqual(entry.reading, mock_reading)
        self.assertIsNotNone(entry.get_reading_string())

    def test_reading_property_lazy_parsing(self):
        """Test that reading property lazily parses from string"""
        entry = HistoryEntry("testuser", "Test question?", "31 Influence", "*31 Influence*\nTest content")
        entry.db_file = self.test_db_path

        # First access should parse the reading
        reading = entry.reading
        self.assertIsInstance(reading, Reading)

        # Second access should return the same cached object
        reading2 = entry.reading
        self.assertIs(reading, reading2)

    def test_reading_property_setter(self):
        """Test setting reading property with Reading object"""
        entry = HistoryEntry("testuser", "Test question?", "31 Influence", "Original string")
        entry.db_file = self.test_db_path

        mock_reading = self._create_mock_reading()
        entry.reading = mock_reading

        self.assertEqual(entry.reading, mock_reading)
        # String should be regenerated when accessed
        self.assertIsNotNone(entry.get_reading_string())

    def test_save_history_entry(self):
        """Test saving history entry to database"""
        entry = HistoryEntry("testuser", "Test question?", "31 Influence", "Test reading")
        entry.db_file = self.test_db_path

        success = entry.save()
        self.assertTrue(success)

        # Verify it was saved
        conn = sqlite3.connect(self.test_db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM history WHERE username = ?", ("testuser",))
        row = c.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "testuser")
        self.assertEqual(row[1], "Test question?")
        self.assertEqual(row[2], "31 Influence")
        self.assertEqual(row[3], "Test reading")

    def test_to_dict_without_markdown(self):
        """Test converting entry to dictionary without markdown rendering"""
        entry = HistoryEntry("testuser", "Test question?", "31 Influence", "Test reading")
        entry.db_file = self.test_db_path

        entry_dict = entry.to_dict(render_markdown=False)

        expected_keys = {'username', 'question', 'hexagram', 'reading', 'reading_dt', 'reading_object'}
        self.assertEqual(set(entry_dict.keys()), expected_keys)
        self.assertEqual(entry_dict['username'], "testuser")
        self.assertEqual(entry_dict['question'], "Test question?")
        self.assertEqual(entry_dict['reading'], "Test reading")

    def test_to_dict_with_markdown(self):
        """Test converting entry to dictionary with markdown rendering"""
        entry = HistoryEntry("testuser", "Test question?", "31 Influence", "Test reading")
        entry.db_file = self.test_db_path

        entry_dict = entry.to_dict(render_markdown=True)

        # Should include HTML versions
        self.assertIn('question_html', entry_dict)
        self.assertIn('hexagram_html', entry_dict)
        self.assertIn('reading_html', entry_dict)


class TestHistory(unittest.TestCase):
    """Test cases for the History model"""

    def setUp(self):
        """Set up test database and test data"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()

        # Initialize test database
        conn = sqlite3.connect(self.test_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS history (
                        username TEXT,
                        question TEXT,
                        hexagram TEXT,
                        reading TEXT,
                        reading_dt TEXT
                     )''')
        conn.commit()
        conn.close()

        # Create history manager
        self.history = History("testuser")
        self.history.db_file = self.test_db_path

    def tearDown(self):
        """Clean up after tests"""
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    def _create_mock_reading(self, number=31, title="Influence"):
        """Create a mock Reading object for testing"""
        reading = Reading()
        reading.Current = MagicMock()
        reading.Current.Number = number
        reading.Current.Title = title
        reading.Future = None
        return reading

    def test_add_reading_with_string(self):
        """Test adding reading with string parameters"""
        success = self.history.add_reading("Test question?", "31 Influence", "Test reading response")
        self.assertTrue(success)

        # Verify it was added
        entries = self.history.get_recent(1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].question, "Test question?")
        self.assertEqual(entries[0].hexagram, "31 Influence")

    def test_add_reading_with_reading_object(self):
        """Test adding reading with Reading object"""
        mock_reading = self._create_mock_reading()
        success = self.history.add_reading("Test question?", mock_reading, "Test reading response")
        self.assertTrue(success)

        entries = self.history.get_recent(1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].question, "Test question?")

    def test_get_recent_empty(self):
        """Test getting recent entries when history is empty"""
        entries = self.history.get_recent(3)
        self.assertEqual(len(entries), 0)

    def test_get_recent_with_data(self):
        """Test getting recent entries with data"""
        # Add multiple entries
        self.history.add_reading("Question 1?", "31 Influence", "Reading 1")
        self.history.add_reading("Question 2?", "32 Duration", "Reading 2")
        self.history.add_reading("Question 3?", "33 Retreat", "Reading 3")

        entries = self.history.get_recent(2)
        self.assertEqual(len(entries), 2)
        # Should be in reverse chronological order
        self.assertEqual(entries[0].question, "Question 3?")
        self.assertEqual(entries[1].question, "Question 2?")

    def test_get_all(self):
        """Test getting all history entries"""
        # Add multiple entries
        self.history.add_reading("Question 1?", "31 Influence", "Reading 1")
        self.history.add_reading("Question 2?", "32 Duration", "Reading 2")

        entries = self.history.get_all()
        self.assertEqual(len(entries), 2)

    def test_get_formatted_recent(self):
        """Test getting formatted recent entries"""
        self.history.add_reading("Test question?", "31 Influence", "Test reading")

        formatted = self.history.get_formatted_recent(1, render_markdown=True)
        self.assertEqual(len(formatted), 1)
        self.assertIn('question_html', formatted[0])
        self.assertIn('reading_html', formatted[0])

    def test_get_history_text_for_prompt(self):
        """Test getting history text formatted for AI prompts"""
        self.history.add_reading("Question 1?", "31 Influence", "Reading 1")
        self.history.add_reading("Question 2?", "32 Duration", "Reading 2")

        prompt_text = self.history.get_history_text_for_prompt(2)

        self.assertIn("Here is the user's recent reading history:", prompt_text)
        self.assertIn("Q: Question 1?", prompt_text)
        self.assertIn("Q: Question 2?", prompt_text)
        self.assertIn("Reading 1", prompt_text)
        self.assertIn("Reading 2", prompt_text)

    def test_get_history_text_for_prompt_empty(self):
        """Test getting history text when no history exists"""
        prompt_text = self.history.get_history_text_for_prompt(3)
        self.assertEqual(prompt_text, "")

    def test_get_readings_as_objects(self):
        """Test getting readings as Reading objects"""
        mock_reading1 = self._create_mock_reading(31, "Influence")
        mock_reading2 = self._create_mock_reading(32, "Duration")

        self.history.add_reading("Question 1?", mock_reading1, "Reading 1")
        self.history.add_reading("Question 2?", mock_reading2, "Reading 2")

        reading_objects = self.history.get_readings_as_objects(2)
        self.assertEqual(len(reading_objects), 2)
        self.assertIsInstance(reading_objects[0], Reading)
        self.assertIsInstance(reading_objects[1], Reading)

    def test_get_count(self):
        """Test getting history count"""
        self.assertEqual(self.history.get_count(), 0)

        self.history.add_reading("Question 1?", "31 Influence", "Reading 1")
        self.assertEqual(self.history.get_count(), 1)

        self.history.add_reading("Question 2?", "32 Duration", "Reading 2")
        self.assertEqual(self.history.get_count(), 2)

    def test_clear_all(self):
        """Test clearing all history"""
        # Add some entries
        self.history.add_reading("Question 1?", "31 Influence", "Reading 1")
        self.history.add_reading("Question 2?", "32 Duration", "Reading 2")
        self.assertEqual(self.history.get_count(), 2)

        # Clear all
        success = self.history.clear_all()
        self.assertTrue(success)
        self.assertEqual(self.history.get_count(), 0)

    def test_str_representation(self):
        """Test string representation of history"""
        self.history.add_reading("Test question?", "31 Influence", "Test reading")

        str_repr = str(self.history)
        self.assertIn("testuser", str_repr)
        self.assertIn("count=1", str_repr)


if __name__ == '__main__':
    unittest.main()
