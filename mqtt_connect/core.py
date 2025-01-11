import json
import base64
import paho.mqtt.client as mqtt
from typing import Callable, Optional
from .database import DatabaseHandler
from paho.mqtt.client import Client, MQTTMessage
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
try:
    from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2
    from meshtastic import BROADCAST_NUM
except ImportError:
    from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2, BROADCAST_NUM

class MQTTHandler:
    """Handles MQTT operations and provides utility methods for database interactions."""

    def __init__(self, broker: str, port: int, username: Optional[str], password: Optional[str], db_file: str):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.db = DatabaseHandler(db_file)
        
        # Maps topics to shared keys
        self.keys = {} # default key is "AQ==" or "1PG7OiApB1nwvP+rz05pAQ=="
        
        # Initialize the MQTT client
        self.client = Client(mqtt.CallbackAPIVersion.VERSION2)
        # Assign callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.on_message_callback: Optional[Callable[[str, str], None]] = None
        self.on_connect_callback: Optional[Callable[[str], None]] = None

    def set_key(self, topic: str, shared_key: str):
        """Set a shared key for a specific topic."""
        self.keys[topic] = shared_key
    
    def set_message_callback(self, callback: Callable[[str, str], None]):
        """Set a callback to handle incoming messages."""
        self.on_message_callback = callback

    def set_connect_callback(self, callback: Callable[[str], None]):
        """Set a callback to handle successful connections."""
        self.on_connect_callback = callback

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

    def _on_message(self, client, userdata, msg: MQTTMessage):
        """Internal callback for when a message is received."""
        topic = msg.topic
        shared_key = self.keys.get(topic)
        try:
            service_envelope = mqtt_pb2.ServiceEnvelope()
            service_envelope.ParseFromString(msg.payload)

            packet = service_envelope.packet
            if packet.HasField("encrypted"):
                if not shared_key:
                    print(f"No key available for topic: {topic}")
                    return

                decrypted_message = self._decrypt_message(packet, shared_key)
                if decrypted_message:
                    self._process_decrypted_message(decrypted_message, service_envelope)
            else:
                self._process_decrypted_message(packet.decoded, service_envelope)

        except Exception as e:
            print(f"Failed to process message: {e}")

    def _decrypt_message(self, packet, key):
        """Decrypt the message using shared or public/private keys."""
        try:
            # Convert key to bytes
            key_bytes = base64.b64decode(key.encode('ascii'))

            # Calculate nonce
            nonce_packet_id = getattr(packet, "id").to_bytes(8, "little")
            nonce_from_node = getattr(packet, "from").to_bytes(8, "little")
            nonce = nonce_packet_id + nonce_from_node

            cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_bytes = decryptor.update(packet.encrypted) + decryptor.finalize()

            decoded_message = mesh_pb2.Data()
            decoded_message.ParseFromString(decrypted_bytes)
            return decoded_message
        
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None
    
    def _process_decrypted_message(self, decoded_message, envelope):
        """Process the decoded message."""
        portnum = decoded_message.portnum

        match portnum:

            case portnums_pb2.TEXT_MESSAGE_APP:
                msg_id = envelope.packet.id  # Unique message ID
                timestamp = envelope.packet.rx_time
                sender = getattr(envelope.packet, "from")
                content = decoded_message.payload.decode("utf-8")
                self.db.save_message(msg_id, timestamp, sender, content)
                
                # process_message(mp, text_payload, is_encrypted)
                if self.on_message_callback:
                    self.on_message_callback(sender, content)

            case portnums_pb2.NODEINFO_APP:
                node_info = mesh_pb2.User()
                node_info.ParseFromString(decoded_message.payload)

                node_id = node_info.id.decode("utf-8")
                short_name = node_info.short_name.decode("utf-8")
                long_name = node_info.long_name.decode("utf-8")

                # Save to database
                self.db.save_node_info(node_id, short_name, long_name)

                print(f"Node Info: {short_name} ({long_name})")

            case portnums_pb2.POSITION_APP:
                position = mesh_pb2.Position()
                position.ParseFromString(decoded_message.payload)

                latitude = position.latitude_i / 1e7
                longitude = position.longitude_i / 1e7
                altitude = position.altitude
                timestamp = position.time

                node_id = getattr(envelope.packet, "from")

                # Save to database
                self.db.save_position(node_id, latitude, longitude, altitude, timestamp)

                print(f"Position Report: Node {node_id} at ({latitude}, {longitude}, {altitude})")
            
            case portnums_pb2.TELEMETRY_APP:
                telemetry = mesh_pb2.Telemetry()
                telemetry.ParseFromString(decoded_message.payload)

                battery_level = telemetry.device_metrics.battery_level
                temperature = telemetry.environment_metrics.temperature
                humidity = telemetry.environment_metrics.relative_humidity
                pressure = telemetry.environment_metrics.barometric_pressure

                node_id = getattr(envelope.packet, "from")

                # Save to database
                self.db.save_telemetry(node_id, battery_level, temperature, humidity, pressure)

                print(f"Telemetry: Node {node_id}, Battery: {battery_level}%, Temp: {temperature}C")
            
            case portnums_pb2.TRACEROUTE_APP: 
                traceroute = mesh_pb2.RouteDiscovery()
                traceroute.ParseFromString(decoded_message.payload)

                route = [node.decode("utf-8") for node in traceroute.route]
                route_back = [node.decode("utf-8") for node in traceroute.route_back]

                # Save to database
                self.db.save_traceroute(getattr(envelope.packet, "from"), route, route_back)

                print(f"Traceroute: {route}, Route Back: {route_back}")
            
            case _:
                print(f"Unhandled portnum: {portnum}")

if __name__ == "__main__":
    # Example usage
    mqtt_handler = MQTTHandler(
        broker="mqtt.meshtastic.org",
        port=1883,
        username="user",
        password="pass",
        db_file="mqtt_data.db",
    )
    
    def on_message(topic, message):
        print(f"Received message on {topic}: {message}")

    mqtt_handler.set_message_callback(on_message)
    mqtt_handler.connect()
    mqtt_handler.subscribe("test/topic")

    try:
        while True:
            pass  # Keep the script running to process messages
    except KeyboardInterrupt:
        mqtt_handler.disconnect()

