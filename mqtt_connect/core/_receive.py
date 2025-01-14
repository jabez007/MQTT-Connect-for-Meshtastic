import re

from paho.mqtt.client import MQTTMessage

from ._client import MeshQTTClient
from ._send import _send_ack
from .utils import decrypt_message

try:
    from meshtastic import BROADCAST_NUM
    from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2
except ImportError:
    from meshtastic import (
        BROADCAST_NUM,
        mesh_pb2,
        mqtt_pb2,
        portnums_pb2,
        telemetry_pb2,
    )


def _get_channel(self: MeshQTTClient, topic: str) -> str | None:
    """Parse the channel name from the received topic"""
    match = re.search(self.root_topic + "/2/e/([0-9a-zA-Z_]+)/*", topic)
    if match:
        return match.group(1)


def _get_key(self: MeshQTTClient, topic: str) -> str | None:
    """Get the shared key for a specific topic"""
    channel_name = self._get_channel(topic)
    return self.get_key(channel_name if channel_name is not None else "")


def _on_message(self: MeshQTTClient, client, userdata, msg: MQTTMessage):
    """Internal callback for when a message is received."""
    channel_name = self._get_channel(msg.topic)
    shared_key = self._get_key(msg.topic)
    try:
        service_envelope = mqtt_pb2.ServiceEnvelope()
        service_envelope.ParseFromString(msg.payload)

        packet = service_envelope.packet
        if packet.HasField("encrypted"):
            if not shared_key:
                print(f"No key available for channel: {channel_name}")
                return

            decrypted_message = self._decrypt_message(packet, shared_key)
            if decrypted_message:
                self._process_decrypted_message(
                    decrypted_message, service_envelope, channel_name
                )
        else:
            self._process_decrypted_message(
                packet.decoded, service_envelope, channel_name
            )

    except Exception as e:
        print(f"Failed to process message: {e}")


def _decrypt_message(self: MeshQTTClient, packet: mesh_pb2.MeshPacket, key: str):
    return decrypt_message(packet, key)


def _process_decrypted_message(
    self: MeshQTTClient,
    decoded_message,
    envelope: mqtt_pb2.ServiceEnvelope,
    channel_name: str,
):
    """Process the decoded message."""
    portnum = decoded_message.portnum

    match portnum:

        case portnums_pb2.TEXT_MESSAGE_APP:
            msg_id = envelope.packet.id  # Unique message ID
            timestamp = envelope.packet.rx_time
            sender = getattr(envelope.packet, "from")
            content = decoded_message.payload.decode("utf-8")

            # Save to database
            self.db.save_message(channel_name, msg_id, timestamp, sender, content)

            # process_message(mp, text_payload, is_encrypted)
            if envelope.packet.want_ack:
                _send_ack(self, msg_id, sender, channel_name)
            if self.on_message_callback:
                self.on_message_callback(channel_name, sender, content, timestamp)

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
