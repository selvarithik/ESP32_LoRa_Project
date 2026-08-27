"""
routing_manager.py

Practical adaptive routing for the LoRa mesh.

Rules:
- Default direct-link threshold = 30%
- Uplink and downlink are separate
- Prefer direct route when link is healthy
- Otherwise select the best neighbor
- Avoid loops
- Respect maximum hop count
- Keep primary and backup route
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mesh_manager import mesh_manager


# ============================================================
# CONSTANTS
# ============================================================

DIRECTION_UPLINK = "uplink"
DIRECTION_DOWNLINK = "downlink"

DEFAULT_SUCCESS_THRESHOLD = 30.0


# ============================================================
# ROUTING MANAGER
# ============================================================

class RoutingManager:

    def __init__(self):

        self.mesh = mesh_manager

    # ========================================================
    # THRESHOLD
    # ========================================================

    def get_threshold(
        self,
        direction: str
    ) -> float:

        direction = str(
            direction
        ).lower()

        settings = (
            self.mesh.get_settings()
        )

        if direction == DIRECTION_UPLINK:
            return float(
                settings[
                    "uplink_threshold"
                ]
            )

        if direction == DIRECTION_DOWNLINK:
            return float(
                settings[
                    "downlink_threshold"
                ]
            )

        raise ValueError(
            "Invalid routing direction"
        )

    # ========================================================
    # LINK SCORE
    # ========================================================

    @staticmethod
    def link_score(
        link: Dict[str, Any]
    ) -> float:
        """
        Calculate a practical link score.

        Success rate has the strongest influence.
        RSSI/SNR provide supporting information.
        """

        success = float(
            link.get(
                "success_rate",
                0
            )
        )

        rssi = float(
            link.get(
                "rssi",
                -120
            )
        )

        snr = float(
            link.get(
                "snr",
                -20
            )
        )

        retries = float(
            link.get(
                "retries",
                0
            )
        )

        # Success component
        score = success * 0.70

        # RSSI component
        #
        # -40 dBm is excellent.
        # -120 dBm is very poor.
        rssi_score = max(
            0.0,
            min(
                100.0,
                (rssi + 120) * 1.25
            )
        )

        score += (
            rssi_score * 0.15
        )

        # SNR component
        snr_score = max(
            0.0,
            min(
                100.0,
                (snr + 20) * 2.5
            )
        )

        score += (
            snr_score * 0.10
        )

        # Retry penalty
        score -= min(
            5.0,
            retries * 0.5
        )

        return max(
            0.0,
            min(
                100.0,
                score
            )
        )

    # ========================================================
    # FIND DIRECT LINK
    # ========================================================

    def direct_link(
        self,
        source: str,
        destination: str
    ) -> Optional[Dict[str, Any]]:

        links = (
            self.mesh.get_neighbors(
                source
            )
        )

        for link in links:

            if (
                link.get(
                    "neighbor_id"
                )
                == destination
            ):

                return link

        return None

    # ========================================================
    # DIRECT LINK IS GOOD?
    # ========================================================

    def direct_is_good(
        self,
        source: str,
        destination: str,
        direction: str
    ) -> bool:

        link = self.direct_link(
            source,
            destination
        )

        if not link:
            return False

        success_rate = float(
            link.get(
                "success_rate",
                0
            )
        )

        threshold = self.get_threshold(
            direction
        )

        return (
            success_rate >= threshold
        )

    # ========================================================
    # FIND RELAYS
    # ========================================================

    def find_relay_candidates(
        self,
        source: str,
        destination: str,
        direction: str
    ) -> List[Dict[str, Any]]:

        candidates = []

        links = (
            self.mesh.get_neighbors(
                source
            )
        )

        threshold = self.get_threshold(
            direction
        )

        for link in links:

            neighbor = link.get(
                "neighbor_id"
            )

            if not neighbor:
                continue

            if neighbor == destination:
                continue

            success = float(
                link.get(
                    "success_rate",
                    0
                )
            )

            if success < threshold:
                continue

            score = self.link_score(
                link
            )

            # Check whether relay has a
            # usable path to destination.
            second_link = (
                self.direct_link(
                    neighbor,
                    destination
                )
            )

            if second_link:

                second_success = float(
                    second_link.get(
                        "success_rate",
                        0
                    )
                )

                if second_success < threshold:
                    continue

                second_score = (
                    self.link_score(
                        second_link
                    )
                )

                total_score = (
                    score * 0.55
                    +
                    second_score * 0.45
                )

                candidates.append({
                    "relay": neighbor,
                    "score": total_score,
                    "first_link":
                        link,
                    "second_link":
                        second_link
                })

        candidates.sort(
            key=lambda item:
                item["score"],
            reverse=True
        )

        return candidates

    # ========================================================
    # SELECT ROUTE
    # ========================================================

    def select_route(
        self,
        source: str,
        destination: str,
        direction: str
    ) -> Dict[str, Any]:

        source = str(
            source
        ).strip()

        destination = str(
            destination
        ).strip()

        direction = str(
            direction
        ).lower()

        if source == destination:

            return {
                "success": True,
                "mode": "local",
                "next_hop": destination,
                "hop_count": 0,
                "score": 100.0,
                "backup": None
            }

        threshold = self.get_threshold(
            direction
        )

        # ----------------------------------------------------
        # DIRECT
        # ----------------------------------------------------

        direct = self.direct_link(
            source,
            destination
        )

        if direct:

            direct_success = float(
                direct.get(
                    "success_rate",
                    0
                )
            )

            if direct_success >= threshold:

                score = self.link_score(
                    direct
                )

                route = {
                    "success": True,
                    "mode": "direct",
                    "next_hop": destination,
                    "hop_count": 1,
                    "score": score,
                    "backup": None,
                    "success_rate":
                        direct_success
                }

                self.mesh.set_route(
                    source,
                    destination,
                    destination,
                    hop_count=1,
                    score=score,
                    direction=direction
                )

                return route

        # ----------------------------------------------------
        # RELAY
        # ----------------------------------------------------

        candidates = (
            self.find_relay_candidates(
                source,
                destination,
                direction
            )
        )

        if not candidates:

            return {
                "success": False,
                "mode": "unavailable",
                "next_hop": None,
                "hop_count": None,
                "score": 0.0,
                "backup": None,
                "threshold": threshold
            }

        best = candidates[0]

        backup = None

        if len(candidates) > 1:
            backup = candidates[1][
                "relay"
            ]

        route = {
            "success": True,
            "mode": "relay",
            "next_hop": best["relay"],
            "hop_count": 2,
            "score": best["score"],
            "backup": backup,
            "threshold": threshold
        }

        self.mesh.set_route(
            source,
            destination,
            best["relay"],
            hop_count=2,
            score=best["score"],
            direction=direction,
            backup=backup
        )

        return route

    # ========================================================
    # GET EXISTING ROUTE
    # ========================================================

    def get_route(
        self,
        source: str,
        destination: str
    ) -> Optional[Dict[str, Any]]:

        return self.mesh.get_route(
            source,
            destination
        )


# ============================================================
# GLOBAL INSTANCE
# ============================================================

routing_manager = RoutingManager()