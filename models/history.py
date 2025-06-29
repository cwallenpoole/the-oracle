import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import markdown
import json
import re
import hashlib

# Import Reading class from logic.iching
from logic.iching import Reading, IChingHexagram

class HistoryEntry:
    """Single history entry for an I Ching reading"""

    def __init__(self, username: str, question: str, hexagram: str, reading_data: Union[str, Reading], reading_dt: str = None, reading_id: str = None):
        self.username = username
        self.question = question
        self.hexagram = hexagram
        self._reading_string = None
        self._reading_object = None
        self.reading_dt = reading_dt or datetime.now().isoformat()
        self.reading_id = reading_id or self._generate_reading_id()
        self.db_file = "data/users.db"

        # Handle the reading_data parameter - could be string or Reading object
        if isinstance(reading_data, Reading):
            self._reading_object = reading_data
            self._reading_string = None  # Will be generated when needed
        else:
            self._reading_string = reading_data
            self._reading_object = None  # Will be parsed when needed

    def _generate_reading_id(self) -> str:
        """Generate a unique reading ID based on username, timestamp, and question"""
        # Create a hash from username, timestamp, and first 50 chars of question
        content = f"{self.username}-{self.reading_dt}-{self.question[:50]}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def get_reading_path(self) -> str:
        """Get the URL path for this reading"""
        date_part = self.reading_dt[:10] if self.reading_dt else "unknown"
        return f"{self.username}-{date_part}-{self.reading_id}"

    @property
    def reading(self) -> Reading:
        """Get the reading as a Reading object, parsing from string if necessary"""
        if self._reading_object is None:
            self._reading_object = self._parse_reading_from_string(self._reading_string)
        return self._reading_object

    @reading.setter
    def reading(self, value: Reading):
        """Set the reading as a Reading object"""
        self._reading_object = value
        self._reading_string = None  # Will be regenerated when needed

    def get_reading_string(self) -> str:
        """Get the reading as a string, converting from Reading object if necessary"""
        if self._reading_string is None:
            self._reading_string = self._convert_reading_to_string(self._reading_object)
        return self._reading_string

    def get_enhanced_reading_html(self) -> str:
        """Get the reading as HTML with hexagram links"""
        reading_text = self.get_reading_string()
        reading_html = markdown.markdown(reading_text)
        return self._enhance_reading_with_links(reading_html)

    def _enhance_reading_with_links(self, reading_text: str) -> str:
        """Enhance reading text by adding links to hexagrams"""
        if not reading_text:
            return reading_text

        # Import here to avoid circular imports
        from logic.iching import get_hexagram_section

        def create_hexagram_url_name(title):
            """Create URL-friendly name from hexagram title"""
            # Split by / and take the second part (English name)
            parts = title.split('/')
            if len(parts) > 1:
                english_name = parts[1].strip()
            else:
                english_name = parts[0].strip()

            # Remove parenthetical sections
            english_name = re.sub(r'\([^)]*\)', '', english_name).strip()

            # Convert to lowercase, replace spaces with underscores
            url_name = english_name.lower().replace(' ', '_')

            # Remove any remaining special characters except underscores
            url_name = re.sub(r'[^a-z0-9_]', '', url_name)

            return url_name

        # Pattern to match hexagram references like "Hexagram 20" or "20: Kuan"
        def replace_hexagram_ref(match):
            try:
                number = int(match.group(1))
                if 1 <= number <= 64:
                    hex_obj = get_hexagram_section(number)
                    if hex_obj:
                        url_name = create_hexagram_url_name(hex_obj.Title)
                        # Import url_for here to avoid circular imports
                        from flask import url_for
                        return f'<a href="{url_for("hexagram_detail", number=number, name=url_name)}" class="hexagram-link">{hex_obj.Number}: {hex_obj.Title}</a>'
            except Exception as e:
                print(f"Error creating hexagram link: {e}")
            return match.group(0)

        # Replace patterns like "Hexagram 20", "hexagram 20", "20: Title"
        enhanced = re.sub(r'[Hh]exagram (\d+)', replace_hexagram_ref, reading_text)
        enhanced = re.sub(r'(\d+):\s*[A-Za-z\']+', replace_hexagram_ref, enhanced)

        return enhanced

    def _parse_reading_from_string(self, reading_string: str) -> Reading:
        """Parse a Reading object from a string representation"""
        # For now, we'll create a simple Reading object with the string as content
        # This is a placeholder - you might want to implement more sophisticated parsing
        # based on how the reading strings are structured
        reading = Reading()

        # Try to extract hexagram information from the string if it follows a pattern
        # This is a basic implementation - you may need to adjust based on your string format
        try:
            # Look for patterns like "31 Influence" or "*31 Influence*"
            current_match = re.search(r'\*?(\d+)\s+([^*\n]+)\*?', reading_string)
            if current_match:
                from logic.iching import get_hexagram_section
                hexagram_num = int(current_match.group(1))
                reading.Current = get_hexagram_section(hexagram_num)

                # Look for transition pattern
                future_match = re.search(r'transitioning to[^\d]*(\d+)\s+([^*\n]+)', reading_string)
                if future_match:
                    future_num = int(future_match.group(1))
                    reading.Future = get_hexagram_section(future_num)
        except Exception as e:
            print(f"Error parsing reading from string: {e}")
            # If parsing fails, create a basic Reading object
            reading = Reading()

        return reading

    def _convert_reading_to_string(self, reading: Reading) -> str:
        """Convert a Reading object to string representation"""
        if reading is None:
            return ""
        return str(reading)

    def save(self) -> bool:
        """Save history entry to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("""INSERT INTO history (username, question, hexagram, reading, reading_dt, reading_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                     (self.username, self.question, self.hexagram, self.get_reading_string(), self.reading_dt, self.reading_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving history entry: {e}")
            return False

    def to_dict(self, render_markdown: bool = False, enhance_links: bool = False) -> Dict[str, Any]:
        """Convert history entry to dictionary"""
        result = {
            'username': self.username,
            'question': self.question,
            'hexagram': self.hexagram,
            'reading': self.get_reading_string(),
            'reading_dt': self.reading_dt,
            'reading_id': self.reading_id,
            'reading_path': self.get_reading_path(),
            'reading_object': self.reading  # Include the Reading object
        }

        if render_markdown:
            result['question_html'] = markdown.markdown(self.question)
            result['hexagram_html'] = markdown.markdown(self.hexagram)
            if enhance_links:
                result['reading_html'] = self.get_enhanced_reading_html()
            else:
                result['reading_html'] = markdown.markdown(self.get_reading_string())

        return result

    def __str__(self) -> str:
        return f"HistoryEntry(username='{self.username}', question='{self.question[:50]}...', hexagram='{self.hexagram}')"

    def __repr__(self) -> str:
        return self.__str__()






class History:
    """History manager for I Ching readings"""

    def __init__(self, username: str):
        self.username = username
        self.db_file = "data/users.db"

    def add_reading(self, question: str, hexagram: Union[str, Reading], reading: Union[str, Reading]) -> bool:
        """Add a new reading to history - accepts both string and Reading objects"""
        # Convert hexagram to string if it's a Reading object
        hexagram_str = str(hexagram) if not isinstance(hexagram, str) else hexagram

        entry = HistoryEntry(self.username, question, hexagram_str, reading)
        return entry.save()

    def get_recent(self, limit: int = 3) -> List[HistoryEntry]:
        """Get recent history entries for this user"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("""SELECT username, question, hexagram, reading, reading_dt, reading_id
                       FROM history
                       WHERE username = ?
                       ORDER BY rowid DESC
                       LIMIT ?""", (self.username, limit))
            rows = c.fetchall()
            conn.close()

            entries = []
            for row in rows:
                # Handle both old format (5 columns) and new format (6 columns)
                reading_id = row[5] if len(row) > 5 else None
                entry = HistoryEntry(row[0], row[1], row[2], row[3], row[4], reading_id)
                entries.append(entry)
            return entries
        except Exception as e:
            print(f"Error getting recent history: {e}")
            return []

    def get_all(self) -> List[HistoryEntry]:
        """Get all history entries for this user"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("""SELECT username, question, hexagram, reading, reading_dt, reading_id
                       FROM history
                       WHERE username = ?
                       ORDER BY rowid DESC""", (self.username,))
            rows = c.fetchall()
            conn.close()

            entries = []
            for row in rows:
                # Handle both old format (5 columns) and new format (6 columns)
                reading_id = row[5] if len(row) > 5 else None
                entry = HistoryEntry(row[0], row[1], row[2], row[3], row[4], reading_id)
                entries.append(entry)
            return entries
        except Exception as e:
            print(f"Error getting all history: {e}")
            return []

    def get_by_path(self, reading_path: str) -> Optional['HistoryEntry']:
        """Get a specific reading by its path (username-date-id)"""
        try:
            # Parse the path to extract username, date, and id
            parts = reading_path.split('-')
            if len(parts) < 3:
                return None

            username = parts[0]
            # The date part might have dashes, so we need to be careful
            # Format is username-YYYY-MM-DD-id, so we need to reconstruct
            if len(parts) >= 5:  # username-YYYY-MM-DD-id
                date_part = f"{parts[1]}-{parts[2]}-{parts[3]}"
                reading_id = parts[4]
            else:
                return None

            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("""SELECT username, question, hexagram, reading, reading_dt, reading_id
                       FROM history
                       WHERE username = ? AND reading_id = ?""", (username, reading_id))
            row = c.fetchone()
            conn.close()

            if row:
                reading_id = row[5] if len(row) > 5 else None
                return HistoryEntry(row[0], row[1], row[2], row[3], row[4], reading_id)
            return None
        except Exception as e:
            print(f"Error getting reading by path: {e}")
            return None

    def get_formatted_recent(self, limit: int = 3, render_markdown: bool = True, enhance_links: bool = False) -> List[Dict[str, Any]]:
        """Get recent history formatted for templates"""
        entries = self.get_recent(limit)
        return [entry.to_dict(render_markdown, enhance_links) for entry in entries]

    def get_history_text_for_prompt(self, limit: int = 3) -> str:
        """Get formatted history text for AI prompts"""
        entries = self.get_recent(limit)
        if not entries:
            return ""

        history_lines = []
        for entry in reversed(entries):  # Reverse to show chronological order
            history_lines.append(f"Q: {entry.question}")
            history_lines.append(f"Hex: {entry.hexagram}")
            history_lines.append(f"Reading: {entry.get_reading_string()}")
            history_lines.append("")  # Empty line for separation

        return "Here is the user's recent reading history:\n" + "\n".join(history_lines)

    def get_readings_as_objects(self, limit: int = 3) -> List[Reading]:
        """Get recent readings as Reading objects"""
        entries = self.get_recent(limit)
        return [entry.reading for entry in entries]

    def clear_all(self) -> bool:
        """Clear all history for this user"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("DELETE FROM history WHERE username = ?", (self.username,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False

    def get_count(self) -> int:
        """Get total number of history entries for this user"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM history WHERE username = ?", (self.username,))
            count = c.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"Error getting history count: {e}")
            return 0

    def __str__(self) -> str:
        return f"History(username='{self.username}', entries={self.get_count()})"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def get_reading_by_path(reading_path: str) -> Optional['HistoryEntry']:
        """Static method to get a reading by path without needing a History instance"""
        try:
            # Parse the path to extract username, date, and id
            parts = reading_path.split('-')
            if len(parts) < 3:
                return None

            username = parts[0]
            # The date part might have dashes, so we need to be careful
            # Format is username-YYYY-MM-DD-id, so we need to reconstruct
            if len(parts) >= 5:  # username-YYYY-MM-DD-id
                date_part = f"{parts[1]}-{parts[2]}-{parts[3]}"
                reading_id = parts[4]
            else:
                return None

            conn = sqlite3.connect("data/users.db")
            c = conn.cursor()
            c.execute("""SELECT username, question, hexagram, reading, reading_dt, reading_id
                       FROM history
                       WHERE username = ? AND reading_id = ?""", (username, reading_id))
            row = c.fetchone()
            conn.close()

            if row:
                reading_id_val = row[5] if len(row) > 5 else None
                return HistoryEntry(row[0], row[1], row[2], row[3], row[4], reading_id_val)
            return None
        except Exception as e:
            print(f"Error getting reading by path: {e}")
            return None
