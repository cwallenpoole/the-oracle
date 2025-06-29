import unittest
import os
import tempfile
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import app
from models.user import User

class TestFlaskApp(unittest.TestCase):
    """Integration tests for the Flask application"""

    def setUp(self):
        """Set up test client and test database"""
        # Create temporary database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()

        # Configure app for testing
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        app.DB_FILE = self.test_db_path

        # Patch User class to use test database
        self.user_patcher = patch.object(User, '__init__')
        self.mock_user_init = self.user_patcher.start()

        def custom_user_init(self, username, password_hash="", birthdate="", about_me=""):
            self.username = username
            self.password_hash = password_hash
            self.birthdate = birthdate
            self.about_me = about_me
            self.db_file = self.test_db_path
            self._history = None

        self.mock_user_init.side_effect = custom_user_init

        # Initialize test database
        app.init_db()

        self.client = app.app.test_client()

    def tearDown(self):
        """Clean up after tests"""
        self.user_patcher.stop()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

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
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login

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
            'password': 'differentpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on register page
        self.assertIn(b'already exists', response.data.lower())

    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        # Create test user
        User.create('testuser', 'password123')

        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to index

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create test user
        User.create('testuser', 'password123')

        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertIn(b'invalid', response.data.lower())

    def test_index_requires_login(self):
        """Test that index page requires login"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_requires_login(self):
        """Test that profile page requires login"""
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_logout(self):
        """Test logout functionality"""
        # Create and login user
        User.create('testuser', 'password123')
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)  # Redirect to login

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
        self.assertIn(b'1990-01-01', response.data)
        self.assertIn(b'Test bio', response.data)

    def test_profile_post_update(self):
        """Test POST request to update profile"""
        # Create user and set session
        User.create('testuser', 'password123')
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        response = self.client.post('/profile', data={
            'birthdate': '1995-12-25',
            'about_me': 'Updated bio'
        })
        self.assertEqual(response.status_code, 302)  # Redirect back to profile

        # Verify update
        user = User.get_by_username('testuser')
        self.assertEqual(user.birthdate, '1995-12-25')
        self.assertEqual(user.about_me, 'Updated bio')

    @patch('app.client.chat.completions.create')
    @patch('logic.iching.cast_hexagrams')
    @patch('llm.memory.search')
    def test_index_post_reading(self, mock_search, mock_cast, mock_openai):
        """Test POST request to create a new reading"""
        # Setup mocks
        mock_reading = MagicMock()
        mock_reading.Current.Number = 31
        mock_reading.Current.Title = "Influence"
        mock_reading.Future = None
        mock_reading.has_transition.return_value = False
        mock_cast.return_value = mock_reading

        mock_search.return_value = [{'metadata': 'test metadata'}]

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test AI reading response"
        mock_openai.return_value = mock_response

        # Create user and set session
        User.create('testuser', 'password123')
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        response = self.client.post('/', data={
            'question': 'Will I find love?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test AI reading response', response.data)

        # Verify reading was saved to history
        user = User.get_by_username('testuser')
        history_count = user.history.get_count()
        self.assertEqual(history_count, 1)


class TestAppPerformance(unittest.TestCase):
    """Performance tests for the Flask application"""

    def setUp(self):
        """Set up test client"""
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_static_page_performance(self):
        """Test that static pages load quickly"""
        import time

        start_time = time.time()
        for _ in range(10):
            response = self.client.get('/login')
            self.assertEqual(response.status_code, 200)
        end_time = time.time()

        # 10 page loads should complete in less than 1 second
        elapsed = end_time - start_time
        self.assertLess(elapsed, 1.0, f"10 login page loads took {elapsed:.3f}s, should be < 1.0s")

    @patch('models.user.User.get_by_username')
    def test_authenticated_page_performance(self, mock_get_user):
        """Test that authenticated pages load quickly"""
        import time

        # Mock user
        mock_user = MagicMock()
        mock_user.username = 'testuser'
        mock_user.birthdate = '1990-01-01'
        mock_user.about_me = 'Test bio'
        mock_user.history.get_formatted_recent.return_value = []
        mock_get_user.return_value = mock_user

        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'

        start_time = time.time()
        for _ in range(10):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
        end_time = time.time()

        # 10 authenticated page loads should complete in less than 2 seconds
        elapsed = end_time - start_time
        self.assertLess(elapsed, 2.0, f"10 authenticated page loads took {elapsed:.3f}s, should be < 2.0s")


if __name__ == '__main__':
    unittest.main()
