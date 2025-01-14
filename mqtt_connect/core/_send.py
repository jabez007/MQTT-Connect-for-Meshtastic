import random

from ._client import MeshQTTClient
from .utils import encrypt_message, generate_hash

try:
    from meshtastic import BROADCAST_NUM
    from meshtastic.protobuf import (mesh_pb2, mqtt_pb2, portnums_pb2,
                                     telemetry_pb2)
except ImportError:
    from meshtastic import (BROADCAST_NUM, mesh_pb2, mqtt_pb2, portnums_pb2,
                            telemetry_pb2)


def _send_ack(
    self: MeshQTTClient, packet_id: int, sender_id: int, channel_name: str = "LongFast"
):
    """
    Send an acknowledgment (ACK) for a received message.
    Args:
        packet_id: The ID of the received packet.
        sender_id: The ID of the sender (node).
    """
    ack_message = mesh_pb2.Data()
    ack_message.portnum = portnums_pb2.ROUTING_APP
    ack_message.request_id = packet_id
    ack_message.payload = b"\030\000"

    service_envelope = mqtt_pb2.ServiceEnvelope()
    service_envelope.packet.CopyFrom(
        _generate_mesh_packet(self, sender_id, ack_message, channel_name)
    )
    service_envelope.channel_id = channel_name
    service_envelope.gateway_id = self.node_id

    payload = service_envelope.SerializeToString()
    self.publish(channel_name, payload)


def _generate_mesh_packet(
    self: MeshQTTClient, destination_id: int, meshage, channel_name: str = "LongFast"
) -> mesh_pb2.MeshPacket:
    """Create a packet to send out over the mesh."""
    key = self.get_key(channel_name)

    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = random.getrandbits(32)  # Generate randomized Id
    setattr(mesh_packet, "from", int(self.node_id.lstrip("!"), 16))
    mesh_packet.to = destination_id
    mesh_packet.want_ack = False
    mesh_packet.channel = generate_hash(channel_name, key if key is not None else "")
    mesh_packet.hop_limit = 3

    if key and not key.isspace():
        mesh_packet.encrypted = _encrypt_message(self, mesh_packet, key, meshage)
    else:
        mesh_packet.decoded.CopyFrom(meshage)

    return mesh_packet


def _encrypt_message(
    self: MeshQTTClient, packet: mesh_pb2.MeshPacket, key: str, meshage
):
    return encrypt_message(packet, key, meshage)
