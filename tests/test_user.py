import unittest
import os
import sqlite3
import tempfile
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import database configuration
from models import set_database_path, reset_database_path, get_database_path
from models.user import User

class TestUser(unittest.TestCase):
    """Test cases for the User model"""

    def setUp(self):
        """Set up test database and test data"""
        # Create a temporary database file for testing
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')

        # Set the test database path
        set_database_path(self.test_db_path)

        # Create and initialize the test database
        self._init_test_db()

    def tearDown(self):
        """Clean up test database"""
        # Reset database path to default
        reset_database_path()

        # Close and remove temporary database file
        os.close(self.test_db_fd)
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def _init_test_db(self):
        """Initialize test database with required tables"""
        conn = sqlite3.connect(self.test_db_path)
        c = conn.cursor()

        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                birthdate TEXT,
                about_me TEXT,
                birth_time TEXT,
                birth_latitude TEXT,
                birth_longitude TEXT
            )
        ''')

        # Create history table
        c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_id TEXT,
                username TEXT,
                question TEXT,
                hexagram TEXT,
                reading TEXT,
                reading_dt TEXT,
                divination_type TEXT DEFAULT 'iching'
            )
        ''')

        # Create user_settings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                username TEXT PRIMARY KEY,
                settings_json TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def test_user_creation(self):
        """Test user creation"""
        # Test successful user creation
        user = User.create("testuser", "password123", "1990-01-01", "Test user")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.birthdate, "1990-01-01")
        self.assertEqual(user.about_me, "Test user")

        # Test duplicate user creation fails
        duplicate_user = User.create("testuser", "password456")
        self.assertIsNone(duplicate_user)

    def test_user_authentication(self):
        """Test user authentication"""
        # Create a user first
        User.create("authuser", "securepass", "1985-05-15")

        # Test successful authentication
        user = User.authenticate("authuser", "securepass")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "authuser")
        self.assertEqual(user.birthdate, "1985-05-15")

        # Test failed authentication with wrong password
        user = User.authenticate("authuser", "wrongpass")
        self.assertIsNone(user)

        # Test failed authentication with non-existent user
        user = User.authenticate("nonexistent", "password")
        self.assertIsNone(user)

    def test_user_exists(self):
        """Test user existence check"""
        # User doesn't exist initially
        self.assertFalse(User.exists("existuser"))

        # Create user
        User.create("existuser", "password")

        # User should exist now
        self.assertTrue(User.exists("existuser"))

    def test_get_by_username(self):
        """Test getting user by username"""
        # Create a user with full profile
        User.create("profileuser", "password", "1992-03-20", "Profile description",
                   "14:30", "40.7128", "-74.0060")

        # Get user by username
        user = User.get_by_username("profileuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "profileuser")
        self.assertEqual(user.birthdate, "1992-03-20")
        self.assertEqual(user.about_me, "Profile description")
        self.assertEqual(user.birth_time, "14:30")
        self.assertEqual(user.birth_latitude, "40.7128")
        self.assertEqual(user.birth_longitude, "-74.0060")

        # Test non-existent user
        user = User.get_by_username("nonexistent")
        self.assertIsNone(user)

    def test_update_profile(self):
        """Test updating user profile"""
        # Create a user
        user = User.create("updateuser", "password", "1990-01-01")
        self.assertIsNotNone(user)

        # Update profile
        success = user.update_profile(
            birthdate="1991-02-02",
            about_me="Updated description",
            birth_time="09:15",
            birth_latitude="51.5074",
            birth_longitude="-0.1278"
        )
        self.assertTrue(success)

        # Verify updates by getting user from database
        updated_user = User.get_by_username("updateuser")
        self.assertEqual(updated_user.birthdate, "1991-02-02")
        self.assertEqual(updated_user.about_me, "Updated description")
        self.assertEqual(updated_user.birth_time, "09:15")
        self.assertEqual(updated_user.birth_latitude, "51.5074")
        self.assertEqual(updated_user.birth_longitude, "-0.1278")

    def test_change_password(self):
        """Test changing user password"""
        # Create a user
        user = User.create("passuser", "oldpassword")
        self.assertIsNotNone(user)

        # Change password successfully
        success = user.change_password("oldpassword", "newpassword")
        self.assertTrue(success)

        # Test authentication with new password
        auth_user = User.authenticate("passuser", "newpassword")
        self.assertIsNotNone(auth_user)

        # Test authentication with old password fails
        auth_user = User.authenticate("passuser", "oldpassword")
        self.assertIsNone(auth_user)

        # Test changing password with wrong current password
        success = user.change_password("wrongold", "anotherpass")
        self.assertFalse(success)

    def test_to_dict(self):
        """Test converting user to dictionary"""
        user = User.create("dictuser", "password", "1988-12-25", "Dictionary user",
                          "16:45", "48.8566", "2.3522")
        user_dict = user.to_dict()

        expected_dict = {
            'username': 'dictuser',
            'birthdate': '1988-12-25',
            'about_me': 'Dictionary user',
            'birth_time': '16:45',
            'birth_latitude': '48.8566',
            'birth_longitude': '2.3522'
        }

        self.assertEqual(user_dict, expected_dict)
        # Ensure password hash is not included
        self.assertNotIn('password_hash', user_dict)

    def test_user_string_representation(self):
        """Test string representation of user"""
        user = User.create("stringuser", "password", "1995-06-10")
        user_str = str(user)
        self.assertIn("stringuser", user_str)
        self.assertIn("1995-06-10", user_str)

    def test_db_file_property(self):
        """Test that db_file property returns correct path"""
        user = User("testuser")
        self.assertEqual(user.db_file, self.test_db_path)

    def test_history_property(self):
        """Test that history property is lazy-loaded"""
        user = User.create("historyuser", "password")

        # History should be lazy-loaded
        self.assertIsNone(user._history)

        # Accessing history should load it
        history = user.history
        self.assertIsNotNone(history)
        self.assertEqual(history.username, "historyuser")

        # Second access should return the same object
        history2 = user.history
        self.assertIs(history, history2)

if __name__ == '__main__':
    unittest.main()
