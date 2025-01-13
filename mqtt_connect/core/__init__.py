import random
from typing import Callable, Optional

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client

from .database import DatabaseHandler


class MeshQTTHandler:
    """Handles MQTT operations and provides utility methods for database interactions."""

    def __init__(
        self,
        broker: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
        db_file: str,
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.db = DatabaseHandler(db_file)

        #
        self.node_id = "!" + hex(random.getrandbits(32)).lstrip("0x")

        # Maps topics to shared keys
        self.keys = {}  # default key is "AQ==" or "1PG7OiApB1nwvP+rz05pAQ=="

        # Initialize the MQTT client
        self.client = Client(mqtt.CallbackAPIVersion.VERSION2)
        # Assign callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.on_connect_callback: Optional[Callable[[str], None]] = None
        self.on_message_callback: Optional[Callable[[str, str, int], None]] = None
        self.on_nodeinfo_callback: Optional[Callable[[str, str, str], None]] = None
        self.on_position_callback: Optional[
            Callable[[str, float, float, int], None]
        ] = None
        self.on_telemetry_callback: Optional[
            Callable[[str, int | None, float | None, float | None, float | None], None]
        ] = None
        self.on_traceroute_callback: Optional[Callable[[list, list], None]] = None

    def set_key(self, topic: str, shared_key: str):
        """Set a shared key for a specific topic."""
        self.keys[topic] = shared_key

    def set_connect_callback(self, callback: Callable[[str], None]):
        """Set a callback to handle successful connections."""
        self.on_connect_callback = callback

    def set_message_callback(self, callback: Callable[[str, str, int], None]):
        """Set a callback to handle incoming text message."""
        self.on_message_callback = callback

    def set_nodeinfo_callback(self, callback: Callable[[str, str, str], None]):
        """Set a callback to handle incoming node info."""
        self.on_nodeinfo_callback = callback

    def set_position_callback(self, callback: Callable[[str, float, float, int], None]):
        """Set a callback to handle incoming position."""
        self.on_position_callback = callback

    def set_telemetry_callback(
        self,
        callback: Callable[
            [str, int | None, float | None, float | None, float | None], None
        ],
    ):
        """Set a callback to handle incoming telemetry."""
        self.on_telemetry_callback = callback

    def set_traceroute_callback(self, callback: Callable[[list, list], None]):
        """Set a callback to handle incoming traceroute."""
        self.on_traceroute_callback = callback

    def connect(self):
        """Connect to the MQTT broker and start the loop."""
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str):
        """Subscribe to a given topic."""
        self.client.subscribe(topic)

    def publish(self, topic: str, message: str):
        """Publish a message to a given topic."""
        self.client.publish(topic, message)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Internal callback for when the MQTT client connects."""
        if rc == 0:
            if self.on_connect_callback:
                self.on_connect_callback(self.broker)
        else:
            print(f"Failed to connect to {self.broker}, return code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Internal callback for when the MQTT client disconnects."""
        print(f"Disconnected from {self.broker} with return code {rc}")

    from ._receive import (_decrypt_message, _on_message,
                           _process_decrypted_message)


if __name__ == "__main__":
    # Example usage
    mqtt_handler = MeshQTTHandler(
        broker="mqtt.meshtastic.org",
        port=1883,
        username="meshdev",
        password="large4cats",
        db_file="mqtt_data.db",
    )

    def on_message(sender, content, timestamp):
        print(f"[{timestamp}]Received message from {sender}: {content}")

    mqtt_handler.set_message_callback(on_message)
    mqtt_handler.connect()
    mqtt_handler.subscribe("msh/US")

    try:
        while True:
            pass  # Keep the script running to process messages
    except KeyboardInterrupt:
        mqtt_handler.disconnect()
