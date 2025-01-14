import json
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
                    channel_name TEXT NOT NULL,
                    msg_id INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    PRIMARY KEY (channel_name, msg_id)
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    altitude INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL,
                    FOREIGN KEY(node_id) REFERENCES nodes(node_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    battery INTEGER,
                    temperature REAL,
                    humidity REAL,
                    pressure REAL,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(node_id) REFERENCES nodes(node_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS traceroutes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    route TEXT NOT NULL,
                    route_back TEXT,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(node_id) REFERENCES nodes(node_id)
                )
                """
            )

    # Message Operations
    def save_message(
        self, channel_name: str, msg_id: int, timestamp: int, sender: str, content: str
    ):
        """Save a received message."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO messages (channel_name, msg_id, timestamp, sender, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                (channel_name, msg_id, timestamp, sender, content),
            )

    def get_message_history(self) -> List[Tuple[str, int, int, str, str]]:
        """Retrieve all messages from the database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute(
                "SELECT channel_name, msg_id, timestamp, sender, content FROM messages ORDER BY timestamp DESC"
            )
            return cursor.fetchall()

    def delete_message_history(self):
        """Delete all messages from the database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM messages")

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

    def delete_node_info(self):
        """Delete all nodes from the database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM nodes")

    # Position Operations
    def save_position(
        self,
        node_id: str,
        latitude: float,
        longitude: float,
        altitude: int,
        timestamp: int,
    ):
        """Save a node's position report."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                "INSERT INTO positions (node_id, latitude, longitude, altitude, timestamp) VALUES (?, ?, ?, ?, ?)",
                (node_id, latitude, longitude, altitude, timestamp),
            )

    def get_positions(self, node_id: str) -> List[Tuple[float, float, int, int]]:
        """Retrieve position reports for a specific node."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute(
                "SELECT latitude, longitude, altitude, timestamp FROM positions WHERE node_id = ? ORDER BY timestamp DESC",
                (node_id,),
            )
            return cursor.fetchall()

    # Telemetry Operations
    def save_telemetry(
        self,
        node_id: str,
        battery: int | None,
        temperature: float | None,
        humidity: float | None,
        pressure: float | None,
    ):
        """Save telemetry data for a node."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                "INSERT INTO telemetry (node_id, battery, temperature, humidity, pressure) VALUES (?, ?, ?, ?, ?)",
                (node_id, battery, temperature, humidity, pressure),
            )

    def get_telemetry(
        self, node_id: str
    ) -> List[Tuple[int | None, float | None, float | None, float | None, str]]:
        """Retrieve telemetry data for a specific node."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute(
                "SELECT battery, temperature, humidity, pressure, timestamp FROM telemetry WHERE node_id = ? ORDER BY timestamp DESC",
                (node_id,),
            )
            return cursor.fetchall()

    # Traceroute Operations
    def save_traceroute(self, node_id: str, route: list, route_back: list):
        """Save traceroute data for a node."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                "INSERT INTO traceroutes (node_id, route, route_back) VALUES (?, ?, ?)",
                (node_id, json.dumps(route), json.dumps(route_back)),
            )

    def get_traceroutes(self, node_id: str) -> List[Tuple[any, any, str]]:
        """Retrieve traceroute data for a specific node."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute(
                "SELECT route, route_back, timestamp FROM traceroutes WHERE node_id = ? ORDER BY timestamp DESC",
                (node_id,),
            )
            return [
                (json.loads(row[0]), json.loads(row[1]) if row[1] else None, row[2])
                for row in cursor.fetchall()
            ]
