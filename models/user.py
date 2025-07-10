import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Dict, Any
from models import get_database_path

class User:
    """User model for handling user data and authentication"""

    def __init__(self, username: str, password_hash: str = "", birthdate: str = "", about_me: str = "",
                 birth_time: str = "", birth_latitude: str = "", birth_longitude: str = ""):
        self.username = username
        self.password_hash = password_hash
        self.birthdate = birthdate
        self.about_me = about_me
        self.birth_time = birth_time
        self.birth_latitude = birth_latitude
        self.birth_longitude = birth_longitude
        self._history = None  # Lazy-loaded history

    @property
    def db_file(self) -> str:
        """Get the current database file path"""
        return get_database_path()

    @property
    def history(self):
        """Lazy-loaded history property"""
        if self._history is None:
            from models.history import History  # Import here to avoid circular imports
            self._history = History(self.username)
        return self._history

    @classmethod
    def create(cls, username: str, password: str, birthdate: str = "", about_me: str = "",
               birth_time: str = "", birth_latitude: str = "", birth_longitude: str = "") -> Optional['User']:
        """Create a new user and save to database"""
        if cls.exists(username):
            return None

        password_hash = generate_password_hash(password)
        user = cls(username, password_hash, birthdate, about_me, birth_time, birth_latitude, birth_longitude)

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
        conn = sqlite3.connect(get_database_path())
        c = conn.cursor()
        c.execute("""SELECT username, password_hash, birthdate, about_me,
                           birth_time, birth_latitude, birth_longitude
                    FROM users WHERE username = ?""", (username,))
        row = c.fetchone()
        conn.close()

        if row:
            return cls(row[0], row[1], row[2] or "", row[3] or "",
                      row[4] or "", row[5] or "", row[6] or "")
        return None

    @classmethod
    def exists(cls, username: str) -> bool:
        """Check if user exists in database"""
        conn = sqlite3.connect(get_database_path())
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
                           SET password_hash = ?, birthdate = ?, about_me = ?,
                               birth_time = ?, birth_latitude = ?, birth_longitude = ?
                           WHERE username = ?""",
                         (self.password_hash, self.birthdate, self.about_me,
                          self.birth_time, self.birth_latitude, self.birth_longitude,
                          self.username))
            else:
                # Insert new user
                c.execute("""INSERT INTO users (username, password_hash, birthdate, about_me,
                                              birth_time, birth_latitude, birth_longitude)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (self.username, self.password_hash, self.birthdate, self.about_me,
                          self.birth_time, self.birth_latitude, self.birth_longitude))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving user: {e}")
            return False

    def update_profile(self, birthdate: str = None, about_me: str = None,
                      birth_time: str = None, birth_latitude: str = None, birth_longitude: str = None) -> bool:
        """Update user profile information"""
        if birthdate is not None:
            self.birthdate = birthdate
        if about_me is not None:
            self.about_me = about_me
        if birth_time is not None:
            self.birth_time = birth_time
        if birth_latitude is not None:
            self.birth_latitude = birth_latitude
        if birth_longitude is not None:
            self.birth_longitude = birth_longitude

        return self.save()

    def change_password(self, current_password: str, new_password: str) -> bool:
        """Change user password"""
        # Verify current password
        if not check_password_hash(self.password_hash, current_password):
            return False

        self.password_hash = generate_password_hash(new_password)
        return self.save()

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding password hash)"""
        return {
            'username': self.username,
            'birthdate': self.birthdate,
            'about_me': self.about_me,
            'birth_time': self.birth_time,
            'birth_latitude': self.birth_latitude,
            'birth_longitude': self.birth_longitude
        }

    def __str__(self) -> str:
        return f"User(username='{self.username}', birthdate='{self.birthdate}')"

    def __repr__(self) -> str:
        return self.__str__()
