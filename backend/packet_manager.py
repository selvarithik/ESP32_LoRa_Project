"""
packet_manager.py

Standard packet creation, validation, encoding and decoding
for the SELVARITHIK'S LoRa Gateway communication system.

Transport independent:
- LoRa / E220
- Wi-Fi
- Ethernet
- USB
- BLE

The packet format is intentionally compact and simple.

Application packet types:
01 TELEMETRY
02 CHAT
03 CONTROL
04 ACK
05 NACK
06 DIAGNOSTICS
07 ERROR
08 CONFIG
09 DISCOVERY
10 ROUTING
"""

from __future__ import annotations

import json
import time
import uuid
import zlib
from typing import Any, Dict, Optional


# ============================================================
# PROTOCOL CONSTANTS
# ============================================================

PROTOCOL_VERSION = 1

PACKET_TYPES = {
    "TELEMETRY": 1,
    "CHAT": 2,
    "CONTROL": 3,
    "ACK": 4,
    "NACK": 5,
    "DIAGNOSTICS": 6,
    "ERROR": 7,
    "CONFIG": 8,
    "DISCOVERY": 9,
    "ROUTING": 10,
}

PACKET_TYPE_NAMES = {
    value: key
    for key, value in PACKET_TYPES.items()
}


# ============================================================
# LIMITS
# ============================================================

MAX_NODE_ID_LENGTH = 32
MAX_PACKET_ID_LENGTH = 32

# Keep application packet comfortably below E220 limits.
#
# This is NOT the E220 radio maximum.
# It is our application safety limit.
MAX_ENCODED_PACKET_BYTES = 180

DEFAULT_TTL = 5
MAX_TTL = 10


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean_text(
    value: Any,
    maximum: int,
    field_name: str
) -> str:

    if value is None:
        raise ValueError(
            f"{field_name} is required"
        )

    value = str(value).strip()

    if not value:
        raise ValueError(
            f"{field_name} cannot be empty"
        )

    if len(value) > maximum:
        raise ValueError(
            f"{field_name} is too long"
        )

    return value


def generate_packet_id() -> str:
    """
    Generate a short unique packet ID.
    """

    return uuid.uuid4().hex[:16]


def current_timestamp_ms() -> int:
    return int(time.time() * 1000)


# ============================================================
# CRC
# ============================================================

def calculate_crc(packet_without_crc: Dict[str, Any]) -> int:
    """
    Calculate CRC32 over canonical JSON.

    CRC is used to detect corrupted application data.
    """

    canonical = json.dumps(
        packet_without_crc,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

    return zlib.crc32(canonical) & 0xFFFFFFFF


# ============================================================
# CREATE PACKET
# ============================================================

def create_packet(
    packet_type: str,
    source: str,
    destination: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    next_hop: Optional[str] = None,
    ttl: int = DEFAULT_TTL,
    priority: int = 0,
    message_id: Optional[str] = None,
    flags: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standard communication packet.
    """

    packet_type = str(
        packet_type
    ).strip().upper()

    if packet_type not in PACKET_TYPES:
        raise ValueError(
            f"Unsupported packet type: {packet_type}"
        )

    source = _clean_text(
        source,
        MAX_NODE_ID_LENGTH,
        "source"
    )

    destination = _clean_text(
        destination,
        MAX_NODE_ID_LENGTH,
        "destination"
    )

    if next_hop is not None:
        next_hop = _clean_text(
            next_hop,
            MAX_NODE_ID_LENGTH,
            "next_hop"
        )

    ttl = int(ttl)

    if ttl < 0:
        raise ValueError(
            "TTL cannot be negative"
        )

    if ttl > MAX_TTL:
        ttl = MAX_TTL

    priority = int(priority)

    if priority < 0:
        priority = 0

    if priority > 10:
        priority = 10

    if payload is None:
        payload = {}

    if not isinstance(payload, dict):
        raise ValueError(
            "payload must be a dictionary"
        )

    packet = {
        "v": PROTOCOL_VERSION,
        "id": (
            message_id
            or generate_packet_id()
        ),
        "type": PACKET_TYPES[packet_type],
        "source": source,
        "destination": destination,
        "next_hop": next_hop,
        "ttl": ttl,
        "priority": priority,
        "flags": flags or {},
        "ts": current_timestamp_ms(),
        "payload": payload,
    }

    packet["crc"] = calculate_crc(
        packet
    )

    # Verify size before returning.
    encode_packet(packet)

    return packet


# ============================================================
# ENCODE
# ============================================================

def encode_packet(
    packet: Dict[str, Any]
) -> bytes:
    """
    Convert packet dictionary into compact UTF-8 JSON bytes.

    Later this byte payload can be passed to the E220 UART layer.
    """

    if not isinstance(packet, dict):
        raise ValueError(
            "Packet must be a dictionary"
        )

    encoded = json.dumps(
        packet,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

    if len(encoded) > MAX_ENCODED_PACKET_BYTES:
        raise ValueError(
            f"Packet too large: "
            f"{len(encoded)} bytes "
            f"(maximum "
            f"{MAX_ENCODED_PACKET_BYTES})"
        )

    return encoded


# ============================================================
# DECODE
# ============================================================

def decode_packet(
    raw_data: bytes | bytearray | str
) -> Dict[str, Any]:
    """
    Decode incoming packet bytes and validate CRC.
    """

    if isinstance(raw_data, bytearray):
        raw_data = bytes(raw_data)

    if isinstance(raw_data, bytes):
        try:
            text = raw_data.decode(
                "utf-8"
            )
        except UnicodeDecodeError as error:
            raise ValueError(
                "Packet is not valid UTF-8"
            ) from error

    elif isinstance(raw_data, str):
        text = raw_data

    else:
        raise ValueError(
            "Packet data must be bytes or string"
        )

    try:
        packet = json.loads(text)

    except json.JSONDecodeError as error:
        raise ValueError(
            "Invalid packet JSON"
        ) from error

    validate_packet(packet)

    received_crc = packet.get(
        "crc"
    )

    packet_for_crc = dict(packet)

    packet_for_crc.pop(
        "crc",
        None
    )

    calculated_crc = calculate_crc(
        packet_for_crc
    )

    if int(received_crc) != int(
        calculated_crc
    ):
        raise ValueError(
            "Packet CRC validation failed"
        )

    return packet


# ============================================================
# VALIDATE PACKET
# ============================================================

def validate_packet(
    packet: Dict[str, Any]
) -> bool:

    if not isinstance(packet, dict):
        raise ValueError(
            "Packet must be a dictionary"
        )

    if int(
        packet.get("v", -1)
    ) != PROTOCOL_VERSION:

        raise ValueError(
            "Unsupported protocol version"
        )

    packet_id = packet.get("id")

    if not packet_id:
        raise ValueError(
            "Packet ID missing"
        )

    source = packet.get(
        "source"
    )

    destination = packet.get(
        "destination"
    )

    if not source:
        raise ValueError(
            "Packet source missing"
        )

    if not destination:
        raise ValueError(
            "Packet destination missing"
        )

    packet_type = int(
        packet.get("type", 0)
    )

    if packet_type not in PACKET_TYPE_NAMES:
        raise ValueError(
            "Unknown packet type"
        )

    ttl = int(
        packet.get("ttl", -1)
    )

    if ttl < 0 or ttl > MAX_TTL:
        raise ValueError(
            "Invalid TTL"
        )

    if not isinstance(
        packet.get("payload", {}),
        dict
    ):
        raise ValueError(
            "Packet payload must be an object"
        )

    return True


# ============================================================
# PACKET TYPE HELPERS
# ============================================================

def packet_type_name(
    packet: Dict[str, Any]
) -> str:

    packet_type = int(
        packet.get("type", 0)
    )

    return PACKET_TYPE_NAMES.get(
        packet_type,
        "UNKNOWN"
    )


def packet_type_code(
    packet_type: str
) -> int:

    packet_type = str(
        packet_type
    ).strip().upper()

    if packet_type not in PACKET_TYPES:
        raise ValueError(
            f"Unknown packet type: {packet_type}"
        )

    return PACKET_TYPES[
        packet_type
    ]


# ============================================================
# ROUTING HELPERS
# ============================================================

def decrement_ttl(
    packet: Dict[str, Any]
) -> Dict[str, Any]:

    new_packet = dict(packet)

    ttl = int(
        new_packet.get(
            "ttl",
            0
        )
    )

    if ttl <= 0:
        raise ValueError(
            "Packet TTL expired"
        )

    new_packet["ttl"] = ttl - 1

    new_packet.pop(
        "crc",
        None
    )

    new_packet["crc"] = calculate_crc(
        new_packet
    )

    return new_packet


def set_next_hop(
    packet: Dict[str, Any],
    next_hop: str
) -> Dict[str, Any]:

    new_packet = dict(packet)

    new_packet["next_hop"] = _clean_text(
        next_hop,
        MAX_NODE_ID_LENGTH,
        "next_hop"
    )

    new_packet.pop(
        "crc",
        None
    )

    new_packet["crc"] = calculate_crc(
        new_packet
    )

    return new_packet


# ============================================================
# ACK / NACK
# ============================================================

def create_ack(
    source: str,
    destination: str,
    message_id: str,
    *,
    next_hop: Optional[str] = None
) -> Dict[str, Any]:

    return create_packet(
        "ACK",
        source=source,
        destination=destination,
        next_hop=next_hop,
        ttl=DEFAULT_TTL,
        payload={
            "ack_id": message_id,
            "status": "received"
        }
    )


def create_nack(
    source: str,
    destination: str,
    message_id: str,
    reason: str,
    *,
    next_hop: Optional[str] = None
) -> Dict[str, Any]:

    return create_packet(
        "NACK",
        source=source,
        destination=destination,
        next_hop=next_hop,
        ttl=DEFAULT_TTL,
        payload={
            "message_id": message_id,
            "status": "failed",
            "reason": str(reason)[:100]
        }
    )