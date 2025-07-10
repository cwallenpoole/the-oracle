import sqlite3
import json
from typing import Optional, Dict, Any, List
from enum import Enum
from models import get_database_path

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"

class Permission:
    """Permission model for handling user permissions and settings"""

    def __init__(self, username: str, settings: Dict[str, Any] = None):
        self.username = username
        # Default settings if none provided
        if settings is None:
            settings = {
                "log_level": "warn",
                "can_admin": False,
                "can_debug": False,
                "can_export": True,
                "can_share": True
            }
        self.settings = settings

    @property
    def db_file(self) -> str:
        """Get the current database file path"""
        return get_database_path()

    @property
    def log_level(self) -> str:
        return self.settings.get("log_level", "warn")

    @property
    def can_admin(self) -> bool:
        return self.settings.get("can_admin", False)

    @property
    def can_debug(self) -> bool:
        return self.settings.get("can_debug", False)

    @property
    def can_export(self) -> bool:
        return self.settings.get("can_export", True)

    @property
    def can_share(self) -> bool:
        return self.settings.get("can_share", True)

    @classmethod
    def create_default(cls, username: str) -> 'Permission':
        """Create default permissions for a new user"""
        permission = cls(username)  # Uses default settings from __init__
        permission.save()
        return permission

    @classmethod
    def get_by_username(cls, username: str) -> Optional['Permission']:
        """Get permissions by username from database"""
        conn = sqlite3.connect(get_database_path())
        c = conn.cursor()
        c.execute("""SELECT username, settings_json
                    FROM user_settings WHERE username = ?""", (username,))
        row = c.fetchone()
        conn.close()

        if row:
            try:
                settings = json.loads(row[1])
                return cls(row[0], settings)
            except json.JSONDecodeError:
                # If JSON is corrupted, create default permissions
                return cls.create_default(username)

        # If no permissions exist, create default ones
        return cls.create_default(username)

    @classmethod
    def exists(cls, username: str) -> bool:
        """Check if permissions exist for user in database"""
        conn = sqlite3.connect(get_database_path())
        c = conn.cursor()
        c.execute("SELECT username FROM user_settings WHERE username = ?", (username,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def save(self) -> bool:
        """Save permissions to database (insert or update)"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            settings_json = json.dumps(self.settings)

            if self.exists(self.username):
                # Update existing permissions
                c.execute("""UPDATE user_settings
                           SET settings_json = ?
                           WHERE username = ?""",
                         (settings_json, self.username))
            else:
                # Insert new permissions
                c.execute("""INSERT INTO user_settings (username, settings_json)
                           VALUES (?, ?)""",
                         (self.username, settings_json))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving permissions: {e}")
            return False

    def update_permissions(self, **kwargs) -> bool:
        """Update user permissions with keyword arguments"""
        for key, value in kwargs.items():
            if key == "log_level":
                # Validate log level
                valid_levels = [level.value for level in LogLevel]
                if value in valid_levels:
                    self.settings["log_level"] = value
                else:
                    return False
            elif key in ["can_admin", "can_debug", "can_export", "can_share"]:
                self.settings[key] = bool(value)
            else:
                # Allow setting any additional custom settings
                self.settings[key] = value

        return self.save()

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        permission_map = {
            'admin': self.can_admin,
            'debug': self.can_debug,
            'export': self.can_export,
            'share': self.can_share
        }
        return permission_map.get(permission_name, False)

    def get_log_level_numeric(self) -> int:
        """Get numeric log level for logging configuration"""
        level_map = {
            'debug': 10,
            'info': 20,
            'warn': 30,
            'error': 40,
            'critical': 50
        }
        return level_map.get(self.log_level, 30)  # Default to WARN

    def to_dict(self) -> Dict[str, Any]:
        """Convert permissions to dictionary"""
        return {
            'username': self.username,
            **self.settings  # Unpack all settings
        }

    @classmethod
    def get_all_users_permissions(cls) -> List['Permission']:
        """Get permissions for all users"""
        conn = sqlite3.connect(get_database_path())
        c = conn.cursor()
        c.execute("""SELECT username, settings_json
                    FROM user_settings ORDER BY username""")
        rows = c.fetchall()
        conn.close()

        permissions = []
        for row in rows:
            try:
                settings = json.loads(row[1])
                permissions.append(cls(row[0], settings))
            except json.JSONDecodeError:
                # Skip corrupted entries or create defaults
                permissions.append(cls.create_default(row[0]))

        return permissions

    def __str__(self) -> str:
        return f"Permission(username='{self.username}', log_level='{self.log_level}', admin={self.can_admin})"

    def __repr__(self) -> str:
        return self.__str__()
