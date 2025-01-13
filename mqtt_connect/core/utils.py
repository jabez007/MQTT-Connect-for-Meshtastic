import base64


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
