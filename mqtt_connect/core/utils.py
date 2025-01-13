import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

try:
    from meshtastic.protobuf import mesh_pb2
except ImportError:
    from meshtastic import mesh_pb2


def generate_hash(name: str, key: str) -> int:
    """?"""

    replaced_key = key.replace("-", "+").replace("_", "/")
    key_bytes = base64.b64decode(replaced_key.encode("utf-8"))
    h_name = xor_hash(bytes(name, "utf-8"))
    h_key = xor_hash(key_bytes)
    result: int = h_name ^ h_key
    return result


def xor_hash(data: bytes) -> int:
    """Return XOR hash of all bytes in the provided string."""

    result = 0
    for char in data:
        result ^= char
    return result


def calculate_nonce(packet: mesh_pb2.MeshPacket):
    """Calculate nonce from Meshtastic packet"""
    nonce_packet_id = packet.id.to_bytes(8, "little")
    nonce_from_node = getattr(packet, "from").to_bytes(8, "little")
    return nonce_packet_id + nonce_from_node


def decrypt_message(packet: mesh_pb2.MeshPacket, key: str):
    """Decrypt the message using shared or public/private keys."""
    if key == "AQ==":
        key = "1PG7OiApB1nwvP+rz05pAQ=="

    try:
        # Convert key to bytes
        key_bytes = base64.b64decode(key.encode("ascii"))

        # Calculate nonce
        nonce = calculate_nonce(packet)

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


def encrypt_message(packet: mesh_pb2.MeshPacket, key: str, meshage):
    """Encrypt a message."""
    if key == "AQ==":
        key = "1PG7OiApB1nwvP+rz05pAQ=="

    key_bytes = base64.b64decode(key.encode("ascii"))

    # Calculate Nonce
    nonce = calculate_nonce(packet)

    cipher = Cipher(
        algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    encrypted_bytes = (
        encryptor.update(meshage.SerializeToString()) + encryptor.finalize()
    )

    return encrypted_bytes
