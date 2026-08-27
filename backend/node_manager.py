import json
from datetime import datetime, timedelta

from database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

SUPPORTED_MCU = [
    "ESP32-WROOM-32",
    "ESP32-S3",
    "ESP32-C3",
    "ESP8266",
    "Arduino UNO",
    "Arduino Nano",
    "Other"
]


SUPPORTED_COMMUNICATIONS = [
    "LoRa",
    "IP/TCP",
    "Wi-Fi",
    "ESP-NOW",
    "BLE"
]


# Node is considered offline when no telemetry is received
# within this amount of time.
NODE_OFFLINE_TIMEOUT_SECONDS = 60


# ============================================================
# ADD NODE
# ============================================================

def add_node(
    node_id,
    name,
    mcu_family,
    mcu_model,
    hardware_revision,
    firmware_version,
    communication_type,
    communication_config,
    node_address,
    enabled=True
):

    if communication_type not in SUPPORTED_COMMUNICATIONS:

        raise ValueError(
            f"Unsupported communication type: {communication_type}"
        )


    now = datetime.now().isoformat()

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO nodes (
            node_id,
            name,
            mcu_family,
            mcu_model,
            hardware_revision,
            firmware_version,
            communication_type,
            communication_config,
            node_address,
            enabled,
            status,
            last_seen,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        node_id,
        name,
        mcu_family,
        mcu_model,
        hardware_revision,
        firmware_version,
        communication_type,
        json.dumps(communication_config),
        node_address,
        1 if enabled else 0,
        "offline" if enabled else "disabled",
        None,
        now,
        now
    ))


    connection.commit()
    connection.close()


# ============================================================
# UPDATE NODE
# ============================================================

def update_node(
    node_id,
    name,
    mcu_family,
    mcu_model,
    hardware_revision,
    firmware_version,
    communication_type,
    communication_config,
    node_address,
    enabled=True
):

    if communication_type not in SUPPORTED_COMMUNICATIONS:

        raise ValueError(
            f"Unsupported communication type: {communication_type}"
        )


    now = datetime.now().isoformat()

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        UPDATE nodes
        SET
            name = ?,
            mcu_family = ?,
            mcu_model = ?,
            hardware_revision = ?,
            firmware_version = ?,
            communication_type = ?,
            communication_config = ?,
            node_address = ?,
            enabled = ?,
            status = CASE
                WHEN ? = 0 THEN 'disabled'
                WHEN status = 'disabled' THEN 'offline'
                ELSE status
            END,
            updated_at = ?
        WHERE node_id = ?
    """, (
        name,
        mcu_family,
        mcu_model,
        hardware_revision,
        firmware_version,
        communication_type,
        json.dumps(communication_config),
        node_address,
        1 if enabled else 0,
        1 if enabled else 0,
        now,
        node_id
    ))


    connection.commit()
    connection.close()


# ============================================================
# GET ALL NODES
# ============================================================

def get_all_nodes():

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM nodes
        ORDER BY node_id
    """)


    rows = cursor.fetchall()

    connection.close()


    result = []


    for row in rows:

        node = dict(row)


        try:

            node["communication_config"] = json.loads(
                node["communication_config"]
            )

        except Exception:

            node["communication_config"] = {}


        result.append(node)


    return result


# ============================================================
# GET NODE
# ============================================================

def get_node(node_id):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM nodes
        WHERE node_id = ?
    """, (node_id,))


    row = cursor.fetchone()

    connection.close()


    if row is None:

        return None


    node = dict(row)


    try:

        node["communication_config"] = json.loads(
            node["communication_config"]
        )

    except Exception:

        node["communication_config"] = {}


    return node


# ============================================================
# DELETE NODE
# ============================================================

def delete_node(node_id):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        DELETE FROM nodes
        WHERE node_id = ?
    """, (node_id,))


    connection.commit()
    connection.close()


# ============================================================
# ENABLE / DISABLE NODE
# ============================================================

def set_node_enabled(node_id, enabled):

    connection = get_connection()
    cursor = connection.cursor()


    status = (
        "offline"
        if enabled
        else "disabled"
    )


    cursor.execute("""
        UPDATE nodes
        SET
            enabled = ?,
            status = ?,
            updated_at = ?
        WHERE node_id = ?
    """, (
        1 if enabled else 0,
        status,
        datetime.now().isoformat(),
        node_id
    ))


    connection.commit()
    connection.close()


# ============================================================
# UPDATE NODE STATUS
# ============================================================

def update_node_status(
    node_id,
    status,
    last_seen=None
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        UPDATE nodes
        SET
            status = ?,
            last_seen = ?,
            updated_at = ?
        WHERE node_id = ?
    """, (
        status,
        last_seen,
        datetime.now().isoformat(),
        node_id
    ))


    connection.commit()
    connection.close()


# ============================================================
# CHECK OFFLINE NODES
# ============================================================

def check_offline_nodes(
    timeout_seconds=NODE_OFFLINE_TIMEOUT_SECONDS
):

    now = datetime.now()

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            node_id,
            name,
            status,
            last_seen,
            enabled
        FROM nodes
        WHERE enabled = 1
    """)


    rows = cursor.fetchall()


    offline_nodes = []


    for row in rows:

        node = dict(row)


        # Already offline
        if node["status"] == "offline":

            continue


        # No telemetry received yet
        if not node["last_seen"]:

            continue


        try:

            last_seen = datetime.fromisoformat(
                    node["last_seen"]
                )

        except Exception:

            continue


        elapsed = (
            now - last_seen).total_seconds()


        if elapsed > timeout_seconds:

            cursor.execute("""
                UPDATE nodes
                SET
                    status = ?,
                    updated_at = ?
                WHERE node_id = ?
            """, (
                "offline",
                now.isoformat(),
                node["node_id"]
            ))


            offline_nodes.append({
                "node_id": node["node_id"],
                "name": node["name"],
                "previous_status": node["status"],
                "last_seen": node["last_seen"],
                "elapsed_seconds": elapsed
            })


    connection.commit()
    connection.close()


    return offline_nodes
