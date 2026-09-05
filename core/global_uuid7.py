"""global_uuidv7.py — Pure-Python UUIDv7 generator (time-ordered, zero deps)."""
import time
import secrets


def uuid7() -> str:
    """Generate a UUIDv7 string (e.g. 019c2d41-7b32-7a56-8c91-3f48b719e642)."""
    timestamp_ms = int(time.time() * 1000)
    time_bytes = timestamp_ms.to_bytes(6, byteorder="big")
    rand_bytes = secrets.token_bytes(10)

    uuid_bytes = bytearray(16)
    uuid_bytes[0:6] = time_bytes
    uuid_bytes[6] = 0x70 | (rand_bytes[0] & 0x0F)   # version 7
    uuid_bytes[7] = rand_bytes[1]
    uuid_bytes[8] = 0x80 | (rand_bytes[2] & 0x3F)   # variant 10
    uuid_bytes[9] = rand_bytes[3]
    uuid_bytes[10:16] = rand_bytes[4:10]

    h = uuid_bytes.hex()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"