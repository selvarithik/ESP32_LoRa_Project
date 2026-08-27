"""
communication_manager.py

Main server-side communication coordinator.

This module does NOT directly talk to the E220 yet.

It provides the common communication layer for:
- LoRa
- Wi-Fi
- Ethernet
- USB
- BLE

Current responsibility:
- Create packets
- Validate packets
- Route packets
- ACK/NACK
- Retry tracking
- Duplicate protection
- Communication statistics
"""

from __future__ import annotations

import threading
import time
from collections import deque
from copy import deepcopy
from typing import Any, Dict, Optional

from packet_manager import (
    create_packet,
    create_ack,
    create_nack,
    decode_packet,
    encode_packet,
    decrement_ttl,
    packet_type_name,
)

from mesh_manager import (
    mesh_manager
)

from routing_manager import (
    routing_manager
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_ACK_TIMEOUT = 5.0
DEFAULT_RETRY_COUNT = 3

MAX_RECENT_MESSAGE_IDS = 1000
MAX_QUEUE_SIZE = 500


# ============================================================
# COMMUNICATION MANAGER
# ============================================================

class CommunicationManager:

    def __init__(self):

        self._lock = threading.RLock()

        # ----------------------------------------------------
        # Transport callback
        #
        # Later server/LoRa adapter can register a function:
        #
        # send_callback(raw_bytes, next_hop)
        # ----------------------------------------------------

        self._send_callback = None

        # ----------------------------------------------------
        # Queues
        # ----------------------------------------------------

        self._outgoing_queue = deque(
            maxlen=MAX_QUEUE_SIZE
        )

        self._incoming_queue = deque(
            maxlen=MAX_QUEUE_SIZE
        )

        # ----------------------------------------------------
        # ACK tracking
        # ----------------------------------------------------

        self._pending_ack = {}

        # ----------------------------------------------------
        # Duplicate protection
        # ----------------------------------------------------

        self._recent_message_ids = deque(
            maxlen=MAX_RECENT_MESSAGE_IDS
        )

        self._recent_message_set = set()

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        self._statistics = {
            "packets_created": 0,
            "packets_sent": 0,
            "packets_received": 0,
            "packets_failed": 0,
            "ack_received": 0,
            "nack_received": 0,
            "duplicates_dropped": 0,
            "crc_errors": 0,
            "decode_errors": 0,
            "route_failures": 0,
            "retries": 0
        }

    # ========================================================
    # TRANSPORT
    # ========================================================

    def set_send_callback(
        self,
        callback
    ) -> None:
        """
        Register physical transport.

        Example later:

            communication_manager.set_send_callback(
                lora_send
            )

        callback signature:

            callback(raw_bytes, next_hop)
        """

        if callback is not None and not callable(
            callback
        ):
            raise ValueError(
                "callback must be callable"
            )

        with self._lock:
            self._send_callback = callback

    # ========================================================
    # CREATE
    # ========================================================

    def create_message(
        self,
        packet_type: str,
        source: str,
        destination: str,
        payload: Optional[
            Dict[str, Any]
        ] = None,
        *,
        direction: Optional[str] = None,
        priority: int = 0,
        ttl: int = 5
    ) -> Dict[str, Any]:

        packet = create_packet(
            packet_type=packet_type,
            source=source,
            destination=destination,
            payload=payload,
            priority=priority,
            ttl=ttl
        )

        with self._lock:

            self._statistics[
                "packets_created"
            ] += 1

        return packet

    # ========================================================
    # SEND
    # ========================================================

    def send(
        self,
        packet: Dict[str, Any],
        *,
        direction: Optional[str] = None,
        require_ack: bool = True
    ) -> Dict[str, Any]:
        """
        Route and send a packet.

        If no physical transport callback exists,
        the packet is queued and can be inspected
        by the simulator/API.
        """

        if not isinstance(
            packet,
            dict
        ):
            raise ValueError(
                "packet must be a dictionary"
            )

        destination = packet.get(
            "destination"
        )

        source = packet.get(
            "source"
        )

        if not source or not destination:
            raise ValueError(
                "source and destination are required"
            )

        # ----------------------------------------------------
        # Determine direction automatically when possible
        # ----------------------------------------------------

        if direction is None:

            master = (
                mesh_manager.get_master()
            )

            if master:

                if source == master:
                    direction = "uplink"

                elif destination == master:
                    direction = "downlink"

                else:
                    direction = "downlink"

            else:
                direction = "downlink"

        # ----------------------------------------------------
        # Select route
        # ----------------------------------------------------

        route = routing_manager.select_route(
            source,
            destination,
            direction
        )

        if not route.get(
            "success"
        ):

            with self._lock:

                self._statistics[
                    "route_failures"
                ] += 1

                self._statistics[
                    "packets_failed"
                ] += 1

            return {
                "success": False,
                "error": "No route available",
                "packet_id":
                    packet.get("id"),
                "route": route
            }

        # ----------------------------------------------------
        # Apply next hop
        # ----------------------------------------------------

        next_hop = route.get(
            "next_hop"
        )

        packet = dict(packet)

        packet["next_hop"] = next_hop

        # ----------------------------------------------------
        # Encode
        # ----------------------------------------------------

        try:
            raw_data = encode_packet(
                packet
            )

        except Exception as error:

            with self._lock:

                self._statistics[
                    "packets_failed"
                ] += 1

            return {
                "success": False,
                "error": str(error),
                "packet_id":
                    packet.get("id")
            }

        # ----------------------------------------------------
        # ACK registration
        # ----------------------------------------------------

        packet_id = packet.get(
            "id"
        )

        if require_ack:

            with self._lock:

                self._pending_ack[
                    packet_id
                ] = {
                    "packet":
                        deepcopy(packet),

                    "created_at":
                        time.time(),

                    "attempts": 0,

                    "direction":
                        direction
                }

        # ----------------------------------------------------
        # Queue/send
        # ----------------------------------------------------

        result = self._send_raw(
            raw_data,
            next_hop
        )

        if result:

            with self._lock:

                self._statistics[
                    "packets_sent"
                ] += 1

        else:

            with self._lock:

                self._statistics[
                    "packets_failed"
                ] += 1

        return {
            "success": result,
            "packet_id": packet_id,
            "next_hop": next_hop,
            "route": route
        }

    # ========================================================
    # RAW SEND
    # ========================================================

    def _send_raw(
        self,
        raw_data: bytes,
        next_hop: Optional[str]
    ) -> bool:

        callback = None

        with self._lock:
            callback = self._send_callback

        # ----------------------------------------------------
        # No physical transport yet.
        #
        # Keep packet in queue for simulator/testing.
        # ----------------------------------------------------

        if callback is None:

            with self._lock:

                self._outgoing_queue.append({
                    "data": bytes(raw_data),
                    "next_hop": next_hop,
                    "queued_at": time.time()
                })

            return True

        try:

            result = callback(
                raw_data,
                next_hop
            )

            return (
                True
                if result is None
                else bool(result)
            )

        except Exception as error:

            print(
                "[COMMUNICATION] "
                f"Transport send error: {error}"
            )

            return False

    # ========================================================
    # RECEIVE
    # ========================================================

    def receive(
        self,
        raw_data: bytes | bytearray | str
    ) -> Dict[str, Any]:
        """
        Receive and process a packet from any transport.
        """

        try:

            packet = decode_packet(
                raw_data
            )

        except ValueError as error:

            message = str(error)

            with self._lock:

                if "CRC" in message:
                    self._statistics[
                        "crc_errors"
                    ] += 1

                else:
                    self._statistics[
                        "decode_errors"
                    ] += 1

            return {
                "success": False,
                "error": message
            }

        packet_id = packet.get(
            "id"
        )

        # ----------------------------------------------------
        # Duplicate protection
        # ----------------------------------------------------

        if self._is_duplicate(
            packet_id
        ):

            with self._lock:

                self._statistics[
                    "duplicates_dropped"
                ] += 1

            return {
                "success": False,
                "duplicate": True,
                "packet_id": packet_id
            }

        self._remember_message_id(
            packet_id
        )

        with self._lock:

            self._statistics[
                "packets_received"
            ] += 1

        # ----------------------------------------------------
        # ACK
        # ----------------------------------------------------

        packet_name = packet_type_name(
            packet
        )

        if packet_name == "ACK":

            self._handle_ack(
                packet
            )

            return {
                "success": True,
                "handled": "ACK",
                "packet": packet
            }

        # ----------------------------------------------------
        # NACK
        # ----------------------------------------------------

        if packet_name == "NACK":

            self._handle_nack(
                packet
            )

            return {
                "success": True,
                "handled": "NACK",
                "packet": packet
            }

        # ----------------------------------------------------
        # Check destination
        # ----------------------------------------------------

        destination = packet.get(
            "destination"
        )

        master = (
            mesh_manager.get_master()
        )

        is_for_us = (
            destination == master
            or destination == "GATEWAY"
        )

        # ----------------------------------------------------
        # If packet is not for us,
        # forward it.
        # ----------------------------------------------------

        if not is_for_us:

            return self._forward_packet(
                packet
            )

        # ----------------------------------------------------
        # Local packet
        # ----------------------------------------------------

        with self._lock:

            self._incoming_queue.append(
                packet
            )

        # ----------------------------------------------------
        # Send ACK
        # ----------------------------------------------------

        if packet.get(
            "flags",
            {}
        ).get(
            "ack_required",
            True
        ):

            self._send_ack_for_packet(
                packet
            )

        return {
            "success": True,
            "handled": "LOCAL",
            "packet": packet
        }

    # ========================================================
    # FORWARD
    # ========================================================

    def _forward_packet(
        self,
        packet: Dict[str, Any]
    ) -> Dict[str, Any]:

        ttl = int(
            packet.get(
                "ttl",
                0
            )
        )

        if ttl <= 0:

            with self._lock:

                self._statistics[
                    "packets_failed"
                ] += 1

            return {
                "success": False,
                "error": "TTL expired",
                "packet_id":
                    packet.get("id")
            }

        source = packet.get(
            "source"
        )

        destination = packet.get(
            "destination"
        )

        master = (
            mesh_manager.get_master()
        )

        if source == master:

            direction = "uplink"

        elif destination == master:

            direction = "downlink"

        else:

            direction = "downlink"

        # ----------------------------------------------------
        # Decrease TTL
        # ----------------------------------------------------

        try:

            forwarded = decrement_ttl(
                packet
            )

        except ValueError as error:

            return {
                "success": False,
                "error": str(error)
            }

        # ----------------------------------------------------
        # Find route from current node/master.
        #
        # In the real ESP32 implementation the current node
        # will be known by the radio transport.
        # ----------------------------------------------------

        current_node = (
            packet.get(
                "next_hop"
            )
            or master
        )

        route = routing_manager.select_route(
            current_node,
            destination,
            direction
        )

        if not route.get(
            "success"
        ):

            with self._lock:

                self._statistics[
                    "route_failures"
                ] += 1

            return {
                "success": False,
                "error": "Forward route unavailable"
            }

        forwarded[
            "next_hop"
        ] = route[
            "next_hop"
        ]

        raw_data = encode_packet(
            forwarded
        )

        success = self._send_raw(
            raw_data,
            forwarded[
                "next_hop"
            ]
        )

        if success:

            with self._lock:

                self._statistics[
                    "packets_sent"
                ] += 1

        return {
            "success": success,
            "forwarded": True,
            "next_hop":
                forwarded[
                    "next_hop"
                ],
            "packet_id":
                forwarded.get("id")
        }

    # ========================================================
    # ACK
    # ========================================================

    def _send_ack_for_packet(
        self,
        packet: Dict[str, Any]
    ) -> None:

        source = packet.get(
            "source"
        )

        destination = packet.get(
            "destination"
        )

        if not source:
            return

        # ACK returns to original source.
        ack = create_ack(
            source=destination,
            destination=source,
            message_id=packet.get(
                "id"
            )
        )

        # ACK should not recursively require ACK.
        ack.setdefault(
            "flags",
            {}
        )[
            "ack_required"
        ] = False

        self.send(
            ack,
            require_ack=False
        )

    # ========================================================
    # HANDLE ACK
    # ========================================================

    def _handle_ack(
        self,
        packet: Dict[str, Any]
    ) -> None:

        payload = packet.get(
            "payload",
            {}
        )

        ack_id = payload.get(
            "ack_id"
        )

        if not ack_id:
            return

        with self._lock:

            if ack_id in self._pending_ack:

                self._pending_ack.pop(
                    ack_id,
                    None
                )

                self._statistics[
                    "ack_received"
                ] += 1

    # ========================================================
    # HANDLE NACK
    # ========================================================

    def _handle_nack(
        self,
        packet: Dict[str, Any]
    ) -> None:

        payload = packet.get(
            "payload",
            {}
        )

        message_id = (
            payload.get(
                "message_id"
            )
            or payload.get(
                "ack_id"
            )
        )

        with self._lock:

            if message_id in self._pending_ack:

                self._pending_ack.pop(
                    message_id,
                    None
                )

                self._statistics[
                    "nack_received"
                ] += 1

    # ========================================================
    # DUPLICATE PROTECTION
    # ========================================================

    def _is_duplicate(
        self,
        message_id: Optional[str]
    ) -> bool:

        if not message_id:
            return False

        with self._lock:

            return (
                message_id
                in self._recent_message_set
            )

    def _remember_message_id(
        self,
        message_id: Optional[str]
    ) -> None:

        if not message_id:
            return

        with self._lock:

            if (
                message_id
                in self._recent_message_set
            ):
                return

            if len(
                self._recent_message_ids
            ) >= MAX_RECENT_MESSAGE_IDS:

                old_id = (
                    self._recent_message_ids.popleft()
                )

                self._recent_message_set.discard(
                    old_id
                )

            self._recent_message_ids.append(
                message_id
            )

            self._recent_message_set.add(
                message_id
            )

    # ========================================================
    # RETRY CHECK
    # ========================================================

    def process_retries(
        self
    ) -> int:
        """
        Check packets waiting for ACK.

        This does not create an infinite retry loop.
        """

        now = time.time()

        settings = (
            mesh_manager.get_settings()
        )

        timeout = float(
            settings.get(
                "route_timeout_seconds",
                DEFAULT_ACK_TIMEOUT
            )
        )

        retry_limit = int(
            settings.get(
                "retry_count",
                DEFAULT_RETRY_COUNT
            )
        )

        retry_count = 0

        with self._lock:

            pending = list(
                self._pending_ack.items()
            )

        for message_id, item in pending:

            age = (
                now
                - item["created_at"]
            )

            if age < timeout:
                continue

            attempts = int(
                item.get(
                    "attempts",
                    0
                )
            )

            if attempts >= retry_limit:

                with self._lock:

                    self._pending_ack.pop(
                        message_id,
                        None
                    )

                    self._statistics[
                        "packets_failed"
                    ] += 1

                continue

            packet = deepcopy(
                item["packet"]
            )

            item["attempts"] = (
                attempts + 1
            )

            item["created_at"] = now

            try:

                raw_data = encode_packet(
                    packet
                )

                success = self._send_raw(
                    raw_data,
                    packet.get(
                        "next_hop"
                    )
                )

                if success:

                    retry_count += 1

                    with self._lock:

                        self._statistics[
                            "retries"
                        ] += 1

            except Exception:

                with self._lock:

                    self._statistics[
                        "packets_failed"
                    ] += 1

        return retry_count

    # ========================================================
    # QUEUE ACCESS
    # ========================================================

    def get_outgoing_queue(
        self
    ) -> list:

        with self._lock:

            return list(
                deepcopy(
                    self._outgoing_queue
                )
            )

    def get_incoming_queue(
        self
    ) -> list:

        with self._lock:

            return list(
                deepcopy(
                    self._incoming_queue
                )
            )

    def clear_queues(
        self
    ) -> None:

        with self._lock:

            self._outgoing_queue.clear()
            self._incoming_queue.clear()

    # ========================================================
    # STATISTICS
    # ========================================================

    def get_statistics(
        self
    ) -> Dict[str, Any]:

        with self._lock:

            data = deepcopy(
                self._statistics
            )

            data[
                "pending_ack"
            ] = len(
                self._pending_ack
            )

            data[
                "outgoing_queue"
            ] = len(
                self._outgoing_queue
            )

            data[
                "incoming_queue"
            ] = len(
                self._incoming_queue
            )

            return data


# ============================================================
# GLOBAL INSTANCE
# ============================================================

communication_manager = (
    CommunicationManager()
)