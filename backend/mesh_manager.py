"""
mesh_manager.py

Maintains the server-side LoRa mesh topology.

Responsibilities:
- Node role
- Master node
- Gateway-connected node
- Neighbor information
- Link quality
- Uplink/downlink success rates
- Primary/backup route information
"""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_UPLINK_THRESHOLD = 30.0
DEFAULT_DOWNLINK_THRESHOLD = 30.0

DEFAULT_MEASUREMENT_WINDOW = 20
DEFAULT_MAX_HOPS = 5

DEFAULT_RETRY_COUNT = 3
DEFAULT_ROUTE_TIMEOUT_SECONDS = 60


# ============================================================
# MESH MANAGER
# ============================================================

class MeshManager:

    def __init__(self):

        self._lock = threading.RLock()

        self._master_node_id: Optional[str] = None

        self._gateway_connection = {
            "type": "Wi-Fi",
            "enabled": True,
            "config": {}
        }

        self._settings = {
            "uplink_threshold": DEFAULT_UPLINK_THRESHOLD,
            "downlink_threshold": DEFAULT_DOWNLINK_THRESHOLD,
            "measurement_window": DEFAULT_MEASUREMENT_WINDOW,
            "max_hops": DEFAULT_MAX_HOPS,
            "retry_count": DEFAULT_RETRY_COUNT,
            "route_timeout_seconds":
                DEFAULT_ROUTE_TIMEOUT_SECONDS
        }

        self._nodes: Dict[str, Dict[str, Any]] = {}

        self._neighbors: Dict[
            str,
            Dict[str, Dict[str, Any]]
        ] = {}

        self._routes: Dict[
            str,
            Dict[str, Dict[str, Any]]
        ] = {}

    # ========================================================
    # MASTER
    # ========================================================

    def set_master(
        self,
        node_id: Optional[str]
    ) -> None:

        with self._lock:

            if node_id is not None:
                node_id = str(
                    node_id
                ).strip()

                if not node_id:
                    raise ValueError(
                        "Master node ID cannot be empty"
                    )

            self._master_node_id = node_id

            if node_id:
                self._ensure_node(
                    node_id
                )

                self._nodes[node_id][
                    "role"
                ] = "MASTER"

                for other_id in self._nodes:

                    if other_id != node_id:
                        self._nodes[
                            other_id
                        ]["role"] = "NODE"

    def get_master(self) -> Optional[str]:

        with self._lock:
            return self._master_node_id

    # ========================================================
    # GATEWAY CONNECTION
    # ========================================================

    def set_gateway_connection(
        self,
        connection_type: str,
        *,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None
    ) -> None:

        connection_type = str(
            connection_type
        ).strip()

        allowed = {
            "Wi-Fi",
            "Ethernet",
            "USB",
            "BLE"
        }

        if connection_type not in allowed:
            raise ValueError(
                "Unsupported gateway connection type"
            )

        with self._lock:

            self._gateway_connection = {
                "type": connection_type,
                "enabled": bool(enabled),
                "config": (
                    deepcopy(config)
                    if isinstance(
                        config,
                        dict
                    )
                    else {}
                )
            }

    def get_gateway_connection(
        self
    ) -> Dict[str, Any]:

        with self._lock:
            return deepcopy(
                self._gateway_connection
            )

    # ========================================================
    # SETTINGS
    # ========================================================

    def get_settings(
        self
    ) -> Dict[str, Any]:

        with self._lock:
            return deepcopy(
                self._settings
            )

    def update_settings(
        self,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not isinstance(
            values,
            dict
        ):
            raise ValueError(
                "Mesh settings must be an object"
            )

        with self._lock:

            if "uplink_threshold" in values:

                value = float(
                    values[
                        "uplink_threshold"
                    ]
                )

                if not 0 <= value <= 100:
                    raise ValueError(
                        "uplink_threshold must be 0-100"
                    )

                self._settings[
                    "uplink_threshold"
                ] = value

            if "downlink_threshold" in values:

                value = float(
                    values[
                        "downlink_threshold"
                    ]
                )

                if not 0 <= value <= 100:
                    raise ValueError(
                        "downlink_threshold must be 0-100"
                    )

                self._settings[
                    "downlink_threshold"
                ] = value

            if "measurement_window" in values:

                value = int(
                    values[
                        "measurement_window"
                    ]
                )

                if not 1 <= value <= 1000:
                    raise ValueError(
                        "measurement_window must be 1-1000"
                    )

                self._settings[
                    "measurement_window"
                ] = value

            if "max_hops" in values:

                value = int(
                    values["max_hops"]
                )

                if not 1 <= value <= 10:
                    raise ValueError(
                        "max_hops must be 1-10"
                    )

                self._settings[
                    "max_hops"
                ] = value

            if "retry_count" in values:

                value = int(
                    values["retry_count"]
                )

                if not 0 <= value <= 10:
                    raise ValueError(
                        "retry_count must be 0-10"
                    )

                self._settings[
                    "retry_count"
                ] = value

            if "route_timeout_seconds" in values:

                value = int(
                    values[
                        "route_timeout_seconds"
                    ]
                )

                if value < 1:
                    raise ValueError(
                        "route_timeout_seconds must be > 0"
                    )

                self._settings[
                    "route_timeout_seconds"
                ] = value

            return deepcopy(
                self._settings
            )

    # ========================================================
    # NODE REGISTRATION
    # ========================================================

    def register_node(
        self,
        node_id: str,
        role: str = "NODE"
    ) -> Dict[str, Any]:

        node_id = str(
            node_id
        ).strip()

        if not node_id:
            raise ValueError(
                "node_id is required"
            )

        role = str(
            role
        ).upper()

        if role not in {
            "NODE",
            "MASTER"
        }:
            role = "NODE"

        with self._lock:

            self._ensure_node(
                node_id
            )

            self._nodes[node_id][
                "role"
            ] = role

            if role == "MASTER":
                self.set_master(
                    node_id
                )

            return deepcopy(
                self._nodes[node_id]
            )

    def _ensure_node(
        self,
        node_id: str
    ) -> None:

        if node_id not in self._nodes:

            self._nodes[node_id] = {
                "node_id": node_id,
                "role": "NODE",
                "last_seen": None,
                "online": False
            }

        self._neighbors.setdefault(
            node_id,
            {}
        )

    def remove_node(
        self,
        node_id: str
    ) -> bool:

        with self._lock:

            existed = (
                node_id in self._nodes
            )

            self._nodes.pop(
                node_id,
                None
            )

            self._neighbors.pop(
                node_id,
                None
            )

            self._routes.pop(
                node_id,
                None
            )

            for neighbors in self._neighbors.values():
                neighbors.pop(
                    node_id,
                    None
                )

            if self._master_node_id == node_id:
                self._master_node_id = None

            return existed

    # ========================================================
    # NODE STATUS
    # ========================================================

    def mark_seen(
        self,
        node_id: str
    ) -> None:

        with self._lock:

            self._ensure_node(
                node_id
            )

            self._nodes[node_id][
                "last_seen"
            ] = time.time()

            self._nodes[node_id][
                "online"
            ] = True

    # ========================================================
    # NEIGHBORS
    # ========================================================

    def update_link(
        self,
        node_id: str,
        neighbor_id: str,
        *,
        rssi: Optional[float] = None,
        snr: Optional[float] = None,
        success_rate: Optional[float] = None,
        packet_loss: Optional[float] = None,
        latency_ms: Optional[float] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:

        node_id = str(
            node_id
        ).strip()

        neighbor_id = str(
            neighbor_id
        ).strip()

        if not node_id or not neighbor_id:
            raise ValueError(
                "node_id and neighbor_id are required"
            )

        with self._lock:

            self._ensure_node(
                node_id
            )

            self._ensure_node(
                neighbor_id
            )

            existing = self._neighbors[
                node_id
            ].get(
                neighbor_id,
                {}
            )

            if rssi is not None:
                existing["rssi"] = float(rssi)

            if snr is not None:
                existing["snr"] = float(snr)

            if success_rate is not None:

                existing[
                    "success_rate"
                ] = max(
                    0.0,
                    min(
                        100.0,
                        float(
                            success_rate
                        )
                    )
                )

            if packet_loss is not None:
                existing[
                    "packet_loss"
                ] = max(
                    0.0,
                    min(
                        100.0,
                        float(
                            packet_loss
                        )
                    )
                )

            if latency_ms is not None:
                existing[
                    "latency_ms"
                ] = max(
                    0.0,
                    float(latency_ms)
                )

            if retries is not None:
                existing[
                    "retries"
                ] = max(
                    0,
                    int(retries)
                )

            existing[
                "last_update"
            ] = time.time()

            self._neighbors[
                node_id
            ][neighbor_id] = existing

            return deepcopy(
                existing
            )

    # ========================================================
    # GET NEIGHBORS
    # ========================================================

    def get_neighbors(
        self,
        node_id: str
    ) -> List[Dict[str, Any]]:

        with self._lock:

            result = []

            for neighbor_id, data in (
                self._neighbors
                .get(node_id, {})
                .items()
            ):

                item = deepcopy(data)

                item[
                    "node_id"
                ] = node_id

                item[
                    "neighbor_id"
                ] = neighbor_id

                result.append(
                    item
                )

            return result

    # ========================================================
    # GET TOPOLOGY
    # ========================================================

    def get_topology(
        self
    ) -> Dict[str, Any]:

        with self._lock:

            return {
                "master_node_id":
                    self._master_node_id,

                "gateway_connection":
                    deepcopy(
                        self._gateway_connection
                    ),

                "settings":
                    deepcopy(
                        self._settings
                    ),

                "nodes":
                    deepcopy(
                        self._nodes
                    ),

                "neighbors":
                    deepcopy(
                        self._neighbors
                    ),

                "routes":
                    deepcopy(
                        self._routes
                    )
            }

    # ========================================================
    # ROUTE STORAGE
    # ========================================================

    def set_route(
        self,
        source: str,
        destination: str,
        next_hop: str,
        *,
        hop_count: int = 1,
        score: float = 0.0,
        direction: str = "downlink",
        backup: Optional[str] = None
    ) -> Dict[str, Any]:

        with self._lock:

            self._routes.setdefault(
                source,
                {}
            )

            route = {
                "source": source,
                "destination": destination,
                "next_hop": next_hop,
                "hop_count": int(
                    hop_count
                ),
                "score": float(
                    score
                ),
                "direction": direction,
                "backup": backup,
                "updated_at": time.time()
            }

            self._routes[source][
                destination
            ] = route

            return deepcopy(
                route
            )

    def get_route(
        self,
        source: str,
        destination: str
    ) -> Optional[Dict[str, Any]]:

        with self._lock:

            route = (
                self._routes
                .get(source, {})
                .get(destination)
            )

            return (
                deepcopy(route)
                if route
                else None
            )

    # ========================================================
    # OFFLINE CHECK
    # ========================================================

    def mark_offline_nodes(
        self,
        timeout_seconds: int = 60
    ) -> List[str]:

        now = time.time()
        offline = []

        with self._lock:

            for node_id, node in (
                self._nodes.items()
            ):

                last_seen = node.get(
                    "last_seen"
                )

                if last_seen is None:
                    continue

                if (
                    now - last_seen
                    > timeout_seconds
                ):

                    if node.get(
                        "online"
                    ):

                        node[
                            "online"
                        ] = False

                        offline.append(
                            node_id
                        )

        return offline


# ============================================================
# GLOBAL INSTANCE
# ============================================================

mesh_manager = MeshManager()