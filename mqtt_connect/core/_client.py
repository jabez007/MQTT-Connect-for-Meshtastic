import random
from typing import Callable, Dict, Optional

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, PayloadType
from paho.mqtt.reasoncodes import ReasonCode

from .database import DatabaseHandler


class MeshQTTClient:
    """Handles MQTT operations and provides utility methods for database interactions."""

    def __init__(
        self,
        broker: str,
        port: Optional[int],
        username: Optional[str],
        password: Optional[str],
        root_topic: str = "msh/US",
        db_file: Optional[str] = None,
    ):
        self.broker = broker
        self.port = port if port is not None else 1883
        self.username = username
        self.password = password
        self.root_topic = root_topic
        self.db = DatabaseHandler(
            db_file
            if db_file is not None
            else (self.broker + "_" + self.root_topic.replace("/", ".") + ".db")
        )

        #
        self.node_id = "!" + hex(random.getrandbits(32)).lstrip("0x")

        # Maps channels to shared keys
        self.keys: Dict[str, Optional[str]] = (
            {}
        )  # default key is "AQ==" or "1PG7OiApB1nwvP+rz05pAQ=="

        # Initialize the MQTT client
        self.client = Client(mqtt.CallbackAPIVersion.VERSION2)
        # Assign callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe

        self.on_connect_callback: Optional[Callable[[str], None]] = None
        self.on_message_callback: Optional[Callable[[str, str, str, int], None]] = None
        self.on_nodeinfo_callback: Optional[Callable[[str, str, str], None]] = None
        self.on_position_callback: Optional[
            Callable[[str, float, float, int], None]
        ] = None
        self.on_telemetry_callback: Optional[
            Callable[[str, int | None, float | None, float | None, float | None], None]
        ] = None
        self.on_traceroute_callback: Optional[Callable[[list, list], None]] = None

    def set_key(self, channel_name: str, shared_key: Optional[str]):
        """Set a shared key for a specific channel."""
        self.keys[channel_name] = shared_key

    def get_key(self, channel_name: str) -> Optional[str]:
        """Get the shared key for a specific channel"""
        return self.keys.get(channel_name)

    def set_connect_callback(self, callback: Callable[[str], None]):
        """Set a callback to handle successful connections."""
        self.on_connect_callback = callback

    def set_message_callback(self, callback: Callable[[str, str, str, int], None]):
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

    def subscribe(self, channel_name: str, shared_key: Optional[str] = None):
        """Subscribe to a given channel."""
        self.set_key(channel_name, shared_key)
        topic = self.root_topic + "/2/e/" + channel_name + "/#"
        print(f"Subscribing to {topic}")
        self.client.subscribe(topic)

    def publish(self, channel_name: str, message: PayloadType):
        """Publish a message to a given channel."""
        topic = self.root_topic + "/2/e/" + channel_name + "/" + self.node_id
        self.client.publish(topic, message)

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Internal callback for when the MQTT client connects."""
        if reason_code == 0:
            print(f"Connected to {self.broker}")
            if self.on_connect_callback:
                self.on_connect_callback(self.broker)
        else:
            print(f"Failed to connect to {self.broker}, return code {reason_code}")

    def _on_subscribe(
        self, client, userdata, mid, reason_code_list: list[ReasonCode], properties=None
    ):
        """Internal callback for when the MQTT client subscribes to a topic"""
        if any(reason_code.is_failure for reason_code in reason_code_list):
            print(f"Failed to subscribe, return codes {reason_code_list}")
        else:
            print(f"Successfully subscribed")

    def _on_disconnect(
        self, client, userdata, disconnect_flags, reason_code, properties=None
    ):
        """Internal callback for when the MQTT client disconnects."""
        print(f"Disconnected from {self.broker} with return code {reason_code}")
