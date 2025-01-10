import sqlite3
from typing import List, Tuple


class DatabaseHandler:
    """Handles database operations for MQTT Connect."""

    def __init__(self, db_file: str):
        self.db_file = db_file
        self._initialize_database()

    def _initialize_database(self):
        """Create necessary tables if they do not exist."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    short_name TEXT NOT NULL,
                    long_name TEXT NOT NULL
                )
                """
            )

    # Message Operations
    def save_message(self, timestamp: str, sender: str, content: str):
        """Save a received message."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                "INSERT INTO messages (timestamp, sender, content) VALUES (?, ?, ?)",
                (timestamp, sender, content),
            )

    def get_message_history(self) -> List[Tuple[str, str, str]]:
        """Retrieve all messages from the database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute(
                "SELECT timestamp, sender, content FROM messages ORDER BY timestamp DESC"
            )
            return cursor.fetchall()

    # Node Operations
    def save_node_info(self, node_id: str, short_name: str, long_name: str):
        """Save or update node information."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                "REPLACE INTO nodes (node_id, short_name, long_name) VALUES (?, ?, ?)",
                (node_id, short_name, long_name),
            )

    def get_node_list(self) -> List[Tuple[str, str, str]]:
        """Retrieve all nodes from the database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("SELECT node_id, short_name, long_name FROM nodes")
            return cursor.fetchall()

    def delete_message_history(self):
        """Delete all messages from the database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM messages")

    def delete_node_info(self):
        """Delete all nodes from the database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM nodes")

