import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

class LLMRequest:
    """Model for storing LLM requests associated with divination readings"""

    def __init__(self, reading_id: str, request_data: str, response_data: str = None,
                 model_used: str = "gpt-4", request_dt: str = None, request_type: str = "initial"):
        self.reading_id = reading_id  # Foreign key to history.reading_id
        self.request_data = request_data  # The actual prompt/request sent to LLM
        self.response_data = response_data  # The response from LLM
        self.model_used = model_used
        self.request_dt = request_dt or datetime.now().isoformat()
        self.request_type = request_type  # "initial" or "followup"
        self.db_file = "data/users.db"

    def save(self) -> bool:
        """Save LLM request to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("""INSERT INTO llm_requests (reading_id, request_data, response_data,
                                                  model_used, request_dt, request_type)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                     (self.reading_id, self.request_data, self.response_data,
                      self.model_used, self.request_dt, self.request_type))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving LLM request: {e}")
            return False

    @classmethod
    def get_by_reading_id(cls, reading_id: str) -> List['LLMRequest']:
        """Get all LLM requests for a specific reading_id"""
        conn = sqlite3.connect("data/users.db")
        c = conn.cursor()
        c.execute("""SELECT reading_id, request_data, response_data, model_used, request_dt, request_type
                    FROM llm_requests WHERE reading_id = ? ORDER BY request_dt""", (reading_id,))
        rows = c.fetchall()
        conn.close()

        return [cls(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows]

    @classmethod
    def get_initial_request(cls, reading_id: str) -> Optional['LLMRequest']:
        """Get the initial LLM request for a specific reading"""
        conn = sqlite3.connect("data/users.db")
        c = conn.cursor()
        c.execute("""SELECT reading_id, request_data, response_data, model_used, request_dt, request_type
                    FROM llm_requests WHERE reading_id = ? AND request_type = 'initial'
                    ORDER BY request_dt LIMIT 1""", (reading_id,))
        row = c.fetchone()
        conn.close()

        if row:
            return cls(row[0], row[1], row[2], row[3], row[4], row[5])
        return None

    @classmethod
    def get_followups(cls, reading_id: str) -> List['LLMRequest']:
        """Get all follow-up requests for a specific reading"""
        conn = sqlite3.connect("data/users.db")
        c = conn.cursor()
        c.execute("""SELECT reading_id, request_data, response_data, model_used, request_dt, request_type
                    FROM llm_requests WHERE reading_id = ? AND request_type = 'followup'
                    ORDER BY request_dt""", (reading_id,))
        rows = c.fetchall()
        conn.close()

        return [cls(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'reading_id': self.reading_id,
            'request_data': self.request_data,
            'response_data': self.response_data,
            'model_used': self.model_used,
            'request_dt': self.request_dt,
            'request_type': self.request_type
        }

    def __str__(self) -> str:
        return f"LLMRequest(reading_id='{self.reading_id}', type='{self.request_type}', dt='{self.request_dt}')"

    def __repr__(self) -> str:
        return self.__str__()
