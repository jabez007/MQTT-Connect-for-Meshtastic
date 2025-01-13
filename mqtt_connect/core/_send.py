import random

from .utils import generate_hash

try:
    from meshtastic import BROADCAST_NUM
    from meshtastic.protobuf import (mesh_pb2, mqtt_pb2, portnums_pb2,
                                     telemetry_pb2)
except ImportError:
    from meshtastic import (BROADCAST_NUM, mesh_pb2, mqtt_pb2, portnums_pb2,
                            telemetry_pb2)


def _send_ack(self, packet_id: int, sender_id: int, channel: str = "LongFast"):
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
        self._generate_mesh_packet(sender_id, ack_message, channel)
    )
    service_envelope.channel_id = channel
    service_envelope.gateway_id = self.node_id

    payload = service_envelope.SerializeToString()
    # set_topic()
    self.publish(publish_topic, payload)


def _generate_mesh_packet(
    self,
    destination_id: int,
    meshage,
    channel: str = "LongFast",
    key: str | None = None,
) -> mesh_pb2.MeshPacket:
    """Create a packet to send out over the mesh."""

    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = random.getrandbits(32)  # Generate randomized Id
    setattr(mesh_packet, "from", int(self.node_id.lstrip("!"), 16))
    mesh_packet.to = destination_id
    mesh_packet.want_ack = False
    mesh_packet.channel = generate_hash(channel, key)
    mesh_packet.hop_limit = 3

    if key and not key.isspace():
        mesh_packet.decoded.CopyFrom(meshage)
    else:
        mesh_packet.encrypted = encrypt_message(channel, key, mesh_packet, meshage)

    return mesh_packet
