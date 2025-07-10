import unittest
import os
import tempfile
import sqlite3
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import database configuration
from models import set_database_path, reset_database_path
import app
from models.user import User

class TestFlaskApp(unittest.TestCase):
    """Integration tests for the Flask application"""

    def setUp(self):
        """Set up test client and test database"""
        # Create temporary database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')

        # Set the test database path
        set_database_path(self.test_db_path)

        # Initialize test database
        self._init_test_db()

        # Configure app for testing
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False

        self.client = app.app.test_client()

    def tearDown(self):
        """Clean up after tests"""
        # Reset database path
        reset_database_path()

        # Clean up test database
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

        # Create llm_requests table
        c.execute('''
            CREATE TABLE IF NOT EXISTS llm_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_id TEXT,
                request_data TEXT,
                response_data TEXT,
                model_used TEXT,
                request_dt TEXT,
                request_type TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def test_login_page_get(self):
        """Test GET request to login page"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_register_page_get(self):
        """Test GET request to register page"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'register', response.data.lower())

    def test_register_new_user(self):
        """Test registering a new user"""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify user was created
        user = User.get_by_username('testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_register_duplicate_user(self):
        """Test registering a duplicate user"""
        # Create first user
        User.create('testuser', 'password123')

        # Try to create duplicate
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'differentpassword',
            'confirm_password': 'differentpassword'
        })
        # Should stay on register page or show error
        self.assertEqual(response.status_code, 200)

    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        # Create test user
        User.create('testuser', 'password123')

        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create test user
        User.create('testuser', 'password123')

        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should stay on login page
        self.assertEqual(response.status_code, 200)

    def test_index_requires_login(self):
        """Test that index page requires login"""
        response = self.client.get('/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_login(self):
        """Test that profile page requires login"""
        response = self.client.get('/profile')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        """Test logout functionality"""
        # Create and login user
        User.create('testuser', 'password123')
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify session is cleared
        with self.client.session_transaction() as sess:
            self.assertNotIn('username', sess)

    def test_profile_get_authenticated(self):
        """Test GET request to profile page when authenticated"""
        # Create user and set session
        user = User.create('testuser', 'password123', '1990-01-01', 'Test bio')
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)

    def test_profile_post_update(self):
        """Test POST request to update profile"""
        # Create user and set session
        User.create('testuser', 'password123')
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        response = self.client.post('/profile', data={
            'birthdate': '1995-12-25',
            'about_me': 'Updated bio'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify update
        user = User.get_by_username('testuser')
        self.assertEqual(user.birthdate, '1995-12-25')
        self.assertEqual(user.about_me, 'Updated bio')

    @patch('logic.ai_readers.generate_text_with_llm')
    @patch('logic.iching.cast_hexagrams')
    @patch('llm.memory.search')
    def test_index_post_reading(self, mock_search, mock_cast, mock_ai_generate):
        """Test POST request to create a new reading"""
        # Setup mocks with proper structure
        mock_current = MagicMock()
        mock_current.Number = 31
        mock_current.Title = "Ch'ien / The Creative"  # Proper title format

        mock_reading = MagicMock()
        mock_reading.Current = mock_current
        mock_reading.Future = None
        mock_reading.has_transition.return_value = False
        mock_cast.return_value = mock_reading

        mock_search.return_value = [{'metadata': 'test metadata'}]
        mock_ai_generate.return_value = "Test AI reading response"

        # Create user and set session
        User.create('testuser', 'password123')
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        response = self.client.post('/', data={
            'question': 'Will I find love?'
        })  # Don't follow redirects to avoid template rendering issues
        # Should redirect to reading detail page
        self.assertEqual(response.status_code, 302)

        # Verify reading was saved to history
        user = User.get_by_username('testuser')
        history_count = user.history.get_count()
        self.assertEqual(history_count, 1)


class TestAppPerformance(unittest.TestCase):
    """Performance tests for the Flask application"""

    def setUp(self):
        """Set up performance test environment"""
        # Create temporary database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')

        # Set the test database path
        set_database_path(self.test_db_path)

        # Initialize test database
        self._init_test_db()

        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def tearDown(self):
        """Clean up performance test environment"""
        # Reset database path
        reset_database_path()

        # Clean up test database
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

        conn.commit()
        conn.close()

    def test_static_page_performance(self):
        """Test performance of static pages"""
        import time

        start_time = time.time()
        response = self.client.get('/login')
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        # Should load within reasonable time (1 second)
        self.assertLess(end_time - start_time, 1.0)

    def test_authenticated_page_performance(self):
        """Test performance of authenticated pages"""
        import time

        # Create user and authenticate
        User.create('perfuser', 'password123')
        with self.client.session_transaction() as sess:
            sess['username'] = 'perfuser'

        start_time = time.time()
        response = self.client.get('/profile')
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        # Should load within reasonable time (1 second)
        self.assertLess(end_time - start_time, 1.0)


if __name__ == '__main__':
    unittest.main()
