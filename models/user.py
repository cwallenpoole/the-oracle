import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Dict, Any

class User:
    """User model for handling user data and authentication"""

    def __init__(self, username: str, password_hash: str = "", birthdate: str = "", about_me: str = ""):
        self.username = username
        self.password_hash = password_hash
        self.birthdate = birthdate
        self.about_me = about_me
        self.db_file = "data/users.db"
        self._history = None  # Lazy-loaded history

    @property
    def history(self):
        """Lazy-loaded history property"""
        if self._history is None:
            from models.history import History  # Import here to avoid circular imports
            self._history = History(self.username)
        return self._history

    @classmethod
    def create(cls, username: str, password: str, birthdate: str = "", about_me: str = "") -> Optional['User']:
        """Create a new user and save to database"""
        if cls.exists(username):
            return None

        password_hash = generate_password_hash(password)
        user = cls(username, password_hash, birthdate, about_me)

        if user.save():
            return user
        return None

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional['User']:
        """Authenticate user with username and password"""
        user = cls.get_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Get user by username from database"""
        conn = sqlite3.connect("data/users.db")
        c = conn.cursor()
        c.execute("SELECT username, password_hash, birthdate, about_me FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()

        if row:
            return cls(row[0], row[1], row[2] or "", row[3] or "")
        return None

    @classmethod
    def exists(cls, username: str) -> bool:
        """Check if user exists in database"""
        conn = sqlite3.connect("data/users.db")
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def save(self) -> bool:
        """Save user to database (insert or update)"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()

            if self.exists(self.username):
                # Update existing user
                c.execute("""UPDATE users
                           SET password_hash = ?, birthdate = ?, about_me = ?
                           WHERE username = ?""",
                         (self.password_hash, self.birthdate, self.about_me, self.username))
            else:
                # Insert new user
                c.execute("""INSERT INTO users (username, password_hash, birthdate, about_me)
                           VALUES (?, ?, ?, ?)""",
                         (self.username, self.password_hash, self.birthdate, self.about_me))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving user: {e}")
            return False

    def update_profile(self, birthdate: str = None, about_me: str = None) -> bool:
        """Update user profile information"""
        if birthdate is not None:
            self.birthdate = birthdate
        if about_me is not None:
            self.about_me = about_me

        return self.save()

    def change_password(self, new_password: str) -> bool:
        """Change user password"""
        self.password_hash = generate_password_hash(new_password)
        return self.save()

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding password hash)"""
        return {
            'username': self.username,
            'birthdate': self.birthdate,
            'about_me': self.about_me
        }

    def __str__(self) -> str:
        return f"User(username='{self.username}', birthdate='{self.birthdate}')"

    def __repr__(self) -> str:
        return self.__str__()
