"""
Database utility functions for The Oracle application.
"""
import sqlite3
import os


DB_FILE = "data/users.db"


def init_db():
    """Initialize the SQLite database with all required tables"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT,
                    birthdate TEXT,
                    about_me TEXT,
                    birth_time TEXT,
                    birth_latitude TEXT,
                    birth_longitude TEXT
                 )''')

    # Check if we need to migrate the history table to make reading_id the primary key
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='history'")
    result = c.fetchone()

    if result and 'reading_id TEXT PRIMARY KEY' not in result[0]:
        print("Migrating history table to make reading_id the primary key...")

        # Create the new table with reading_id as primary key
        c.execute('''CREATE TABLE IF NOT EXISTS history_new (
                        reading_id TEXT PRIMARY KEY,
                        username TEXT,
                        question TEXT,
                        hexagram TEXT,
                        reading TEXT,
                        reading_dt TEXT,
                        divination_type TEXT DEFAULT 'iching'
                     )''')

        # Copy data from old table to new table (only if reading_id is not null and unique)
        c.execute('''INSERT OR IGNORE INTO history_new
                     (reading_id, username, question, hexagram, reading, reading_dt, divination_type)
                     SELECT reading_id, username, question, hexagram, reading, reading_dt, divination_type
                     FROM history
                     WHERE reading_id IS NOT NULL AND reading_id != ''
                     ORDER BY reading_dt''')

        # Drop the old table
        c.execute('DROP TABLE IF EXISTS history')

        # Rename the new table
        c.execute('ALTER TABLE history_new RENAME TO history')

        print("History table migration completed.")
    else:
        # Create the table with the correct structure if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS history (
                        reading_id TEXT PRIMARY KEY,
                        username TEXT,
                        question TEXT,
                        hexagram TEXT,
                        reading TEXT,
                        reading_dt TEXT,
                        divination_type TEXT DEFAULT 'iching'
                     )''')

    # Create user_settings table
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                    username TEXT PRIMARY KEY,
                    settings_json TEXT DEFAULT '{"log_level": "warn", "can_admin": false, "can_debug": false, "can_export": true, "can_share": true}',
                    FOREIGN KEY (username) REFERENCES users (username)
                 )''')

    # Create llm_requests table
    c.execute('''CREATE TABLE IF NOT EXISTS llm_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reading_id TEXT NOT NULL,
                    request_data TEXT NOT NULL,
                    response_data TEXT,
                    model_used TEXT DEFAULT 'gpt-4',
                    request_dt TEXT NOT NULL,
                    request_type TEXT DEFAULT 'initial',
                    FOREIGN KEY (reading_id) REFERENCES history (reading_id)
                 )''')

    # Add new columns to existing users table if they don't exist
    _add_column_if_not_exists(c, "users", "birthdate", "TEXT")
    _add_column_if_not_exists(c, "users", "about_me", "TEXT")
    _add_column_if_not_exists(c, "users", "birth_time", "TEXT")
    _add_column_if_not_exists(c, "users", "birth_latitude", "TEXT")
    _add_column_if_not_exists(c, "users", "birth_longitude", "TEXT")

    # Add new columns to existing history table if they don't exist
    _add_column_if_not_exists(c, "history", "reading_id", "TEXT")
    _add_column_if_not_exists(c, "history", "divination_type", "TEXT DEFAULT 'iching'")

    conn.commit()
    conn.close()


def _add_column_if_not_exists(cursor, table_name, column_name, column_type):
    """Add a column to a table if it doesn't already exist"""
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
    except sqlite3.OperationalError:
        pass  # Column already exists
