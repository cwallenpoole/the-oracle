import unittest
import tempfile
import os
import sqlite3
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import database configuration
from models import set_database_path, reset_database_path
from app import app
from models.user import User

class BaseRouteTest(unittest.TestCase):
    """Base test class for route tests"""

    def setUp(self):
        """Set up test environment"""
        # Create test database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')

        # Set the test database path
        set_database_path(self.test_db_path)

        # Initialize test database
        self._init_test_db()

        # Set up Flask test client
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.client = app.test_client()

    def tearDown(self):
        """Clean up test environment"""
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

    def login_user(self, username: str, password: str = "testpass123"):
        """Helper method to log in a user"""
        # Create user if doesn't exist
        if not User.exists(username):
            User.create(username, password)

        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

class TestPublicRoutes(BaseRouteTest):
    """Test public routes that don't require authentication"""

    def test_index_route(self):
        """Test the index route"""
        response = self.client.get('/')
        # Should redirect to login if not authenticated
        self.assertEqual(response.status_code, 302)

    def test_login_route_get(self):
        """Test login route GET request"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_register_route_get(self):
        """Test register route GET request"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'register', response.data.lower())

class TestAuthRoutes(BaseRouteTest):
    """Test authentication-related routes"""

    def test_register_user(self):
        """Test user registration"""
        response = self.client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)

        # Should redirect to index after successful registration
        self.assertEqual(response.status_code, 200)

        # User should be created in database
        user = User.get_by_username('newuser')
        self.assertIsNotNone(user)

    def test_login_user(self):
        """Test user login"""
        # Create a user first
        User.create('loginuser', 'loginpass123')

        response = self.client.post('/login', data={
            'username': 'loginuser',
            'password': 'loginpass123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass'
        }, follow_redirects=True)

        # Should stay on login page or show error
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        """Test user logout"""
        # Login first
        self.login_user('logoutuser')

        # Then logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

class TestProtectedRoutes(BaseRouteTest):
    """Test routes that require authentication"""

    def test_profile_route_requires_login(self):
        """Test that profile route requires login"""
        response = self.client.get('/profile')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_profile_route_authenticated(self):
        """Test profile route when authenticated"""
        # Login first
        self.login_user('profileuser')

        # Access profile
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'profile', response.data.lower())

    def test_hexagrams_route(self):
        """Test hexagrams listing route"""
        response = self.client.get('/hexagrams')
        self.assertEqual(response.status_code, 200)

    def test_trigrams_route(self):
        """Test trigrams listing route"""
        response = self.client.get('/trigrams')
        self.assertEqual(response.status_code, 200)

class TestAPIRoutes(BaseRouteTest):
    """Test API routes"""

    def test_api_reading_requires_login(self):
        """Test that API reading route requires login"""
        response = self.client.post('/', json={
            'question': 'Test question',
            'system': 'three_coin'
        })
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 302)

class TestErrorHandling(BaseRouteTest):
    """Test error handling in routes"""

    def test_nonexistent_route(self):
        """Test 404 for non-existent routes"""
        response = self.client.get('/nonexistent-route')
        self.assertEqual(response.status_code, 404)

    def test_invalid_hexagram_number(self):
        """Test invalid hexagram number"""
        response = self.client.get('/hexagram/999/invalid')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
