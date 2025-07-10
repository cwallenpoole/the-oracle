# Models package for The Oracle I Ching App

import os
from typing import Optional

# Global database configuration
_database_path: Optional[str] = None

def get_database_path() -> str:
    """Get the current database path"""
    global _database_path
    if _database_path is None:
        # Default path based on environment
        if os.getenv('TESTING', 'False').lower() == 'true':
            return "data/test_users.db"
        else:
            return "data/users.db"
    return _database_path

def set_database_path(path: str) -> None:
    """Set the database path for testing or configuration"""
    global _database_path
    _database_path = path

def reset_database_path() -> None:
    """Reset database path to default"""
    global _database_path
    _database_path = None
