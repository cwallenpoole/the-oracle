import unittest
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.user import User
from models.history import History

class TestUser(unittest.TestCase):
    """Test cases for the User model"""

    def setUp(self):
        """Set up test database and test data"""
        # Create a temporary database file for testing
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()

        # Patch the db_file in User class to use our test database
        self.db_patcher = patch.object(User, '__init__')
        self.mock_init = self.db_patcher.start()

        def custom_init(self, username, password_hash="", birthdate="", about_me=""):
            self.username = username
            self.password_hash = password_hash
            self.birthdate = birthdate
            self.about_me = about_me
            self.db_file = self.test_db_path
            self._history = None

        self.mock_init.side_effect = custom_init

        # Initialize test database
        self._init_test_db()

    def tearDown(self):
        """Clean up after tests"""
        self.db_patcher.stop()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    def _init_test_db(self):
        """Initialize test database with required tables"""
        conn = sqlite3.connect(self.test_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password_hash TEXT,
                        birthdate TEXT,
                        about_me TEXT
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS history (
                        reading_id TEXT PRIMARY KEY,
                        username TEXT,
                        question TEXT,
                        hexagram TEXT,
                        reading TEXT,
                        reading_dt TEXT,
                        divination_type TEXT DEFAULT 'iching'
                     )''')
        conn.commit()
        conn.close()

    def test_user_creation(self):
        """Test basic user creation"""
        user = User("testuser", "hash123", "1990-01-01", "Test about me")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.password_hash, "hash123")
        self.assertEqual(user.birthdate, "1990-01-01")
        self.assertEqual(user.about_me, "Test about me")

    def test_user_create_new(self):
        """Test creating a new user via User.create()"""
        user = User.create("newuser", "password123", "1985-05-15", "New user bio")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.birthdate, "1985-05-15")
        self.assertEqual(user.about_me, "New user bio")

    def test_user_create_duplicate(self):
        """Test that creating a duplicate user returns None"""
        User.create("duplicate", "password123")
        duplicate_user = User.create("duplicate", "password456")
        self.assertIsNone(duplicate_user)

    def test_user_authentication_success(self):
        """Test successful user authentication"""
        original_user = User.create("authuser", "password123")
        authenticated_user = User.authenticate("authuser", "password123")
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.username, "authuser")

    def test_user_authentication_failure(self):
        """Test failed user authentication"""
        User.create("authuser", "password123")
        authenticated_user = User.authenticate("authuser", "wrongpassword")
        self.assertIsNone(authenticated_user)

    def test_user_get_by_username(self):
        """Test getting user by username"""
        User.create("getuser", "password123", "1990-01-01", "Get user test")
        retrieved_user = User.get_by_username("getuser")
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "getuser")
        self.assertEqual(retrieved_user.birthdate, "1990-01-01")
        self.assertEqual(retrieved_user.about_me, "Get user test")

    def test_user_exists(self):
        """Test user existence check"""
        self.assertFalse(User.exists("nonexistent"))
        User.create("existsuser", "password123")
        self.assertTrue(User.exists("existsuser"))

    def test_update_profile(self):
        """Test updating user profile"""
        user = User.create("updateuser", "password123")
        success = user.update_profile(birthdate="1995-12-25", about_me="Updated bio")
        self.assertTrue(success)

        # Verify the update persisted
        updated_user = User.get_by_username("updateuser")
        self.assertEqual(updated_user.birthdate, "1995-12-25")
        self.assertEqual(updated_user.about_me, "Updated bio")

    def test_change_password(self):
        """Test changing user password"""
        user = User.create("pwduser", "oldpassword")
        success = user.change_password("newpassword")
        self.assertTrue(success)

        # Verify old password doesn't work
        self.assertIsNone(User.authenticate("pwduser", "oldpassword"))

        # Verify new password works
        self.assertIsNotNone(User.authenticate("pwduser", "newpassword"))

    def test_to_dict(self):
        """Test converting user to dictionary"""
        user = User.create("dictuser", "password123", "1990-01-01", "Dict test")
        user_dict = user.to_dict()

        expected_keys = {'username', 'birthdate', 'about_me'}
        self.assertEqual(set(user_dict.keys()), expected_keys)
        self.assertEqual(user_dict['username'], "dictuser")
        self.assertEqual(user_dict['birthdate'], "1990-01-01")
        self.assertEqual(user_dict['about_me'], "Dict test")
        self.assertNotIn('password_hash', user_dict)

    @patch('models.history.History')
    def test_lazy_history_property(self, mock_history_class):
        """Test lazy-loaded history property"""
        mock_history_instance = MagicMock()
        mock_history_class.return_value = mock_history_instance

        user = User.create("historyuser", "password123")

        # First access should create the history object
        history1 = user.history
        mock_history_class.assert_called_once_with("historyuser")
        self.assertEqual(history1, mock_history_instance)

        # Second access should return the same cached object
        history2 = user.history
        # Should still only be called once (cached)
        mock_history_class.assert_called_once()
        self.assertEqual(history1, history2)

    def test_str_representation(self):
        """Test string representation of user"""
        user = User("testuser", "hash", "1990-01-01", "About me")
        str_repr = str(user)
        self.assertIn("testuser", str_repr)
        self.assertIn("1990-01-01", str_repr)

if __name__ == '__main__':
    unittest.main()
