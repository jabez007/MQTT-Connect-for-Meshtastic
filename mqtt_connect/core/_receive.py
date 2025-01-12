import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from paho.mqtt.client import MQTTMessage

try:
    from meshtastic import BROADCAST_NUM
    from meshtastic.protobuf import (mesh_pb2, mqtt_pb2, portnums_pb2,
                                     telemetry_pb2)
except ImportError:
    from meshtastic import (BROADCAST_NUM, mesh_pb2, mqtt_pb2, portnums_pb2,
                            telemetry_pb2)


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
        key_bytes = base64.b64decode(key.encode("ascii"))

        # Calculate nonce
        nonce_packet_id = getattr(packet, "id").to_bytes(8, "little")
        nonce_from_node = getattr(packet, "from").to_bytes(8, "little")
        nonce = nonce_packet_id + nonce_from_node

        cipher = Cipher(
            algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend()
        )
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

            # Save to database
            self.db.save_message(msg_id, timestamp, sender, content)

            # process_message(mp, text_payload, is_encrypted)
            if self.on_message_callback:
                self.on_message_callback(sender, content, timestamp)

        case portnums_pb2.NODEINFO_APP:
            node_info = mesh_pb2.User()
            node_info.ParseFromString(decoded_message.payload)

            node_id = node_info.id
            short_name = node_info.short_name
            long_name = node_info.long_name

            # Save to database
            self.db.save_node_info(node_id, short_name, long_name)

            if self.on_nodeinfo_callback:
                self.on_nodeinfo_callback(node_id, short_name, long_name)

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

            # Trigger the position callback
            if self.on_position_callback:
                self.on_position_callback(node_id, latitude, longitude, altitude)

        case portnums_pb2.TELEMETRY_APP:
            # Device Metrics
            battery_level = None
            # Environment Metrics
            temperature = None
            humidity = None
            pressure = None

            telemetry = telemetry_pb2.Telemetry()
            telemetry.ParseFromString(decoded_message.payload)

            telemetrytype = telemetry.WhichOneof("variant")

            match telemetrytype:
                case "device_metrics":
                    battery_level = telemetry.device_metrics.battery_level
                case "environment_metrics":
                    temperature = telemetry.environment_metrics.temperature
                    humidity = telemetry.environment_metrics.relative_humidity
                    pressure = telemetry.environment_metrics.barometric_pressure
                case _:
                    print(f"Unhandled telemetry: {telemetrytype}")

            node_id = getattr(envelope.packet, "from")

            # Save to database
            self.db.save_telemetry(
                node_id, battery_level, temperature, humidity, pressure
            )

            # Trigger the telemetry callback
            if self.on_telemetry_callback:
                self.on_telemetry_callback(
                    node_id, battery_level, temperature, humidity, pressure
                )

        case portnums_pb2.TRACEROUTE_APP:
            traceroute = mesh_pb2.RouteDiscovery()
            traceroute.ParseFromString(decoded_message.payload)

            route = [
                (node, snr)
                for node, snr in zip(traceroute.route, traceroute.snr_towards)
            ]
            route_back = [
                (node, snr)
                for node, snr in zip(traceroute.route_back, traceroute.snr_back)
            ]

            # Save to database
            self.db.save_traceroute(getattr(envelope.packet, "from"), route, route_back)

            # Trigger the traceroute callback
            if self.on_traceroute_callback:
                self.on_traceroute_callback(route, route_back)

        case _:
            print(f"Unhandled portnum: {portnum}")
