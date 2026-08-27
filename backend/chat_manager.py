"""
Private Chat Manager

IMPORTANT:
Private Chat is an application/database feature.

It does NOT use:
- communication_manager
- LoRa packets
- mesh routing
- ESP32 <-> ESP32 M2M communication

The gateway is the chat operator.
Registered node names come from Node Management.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from database import get_connection
from node_manager import get_node


GATEWAY_ID = "GATEWAY"
GATEWAY_NAME = "Gateway Control Center"

STATUS_SENT = "SENT"
STATUS_DELIVERED = "DELIVERED"
STATUS_SEEN = "SEEN"
STATUS_FAILED = "FAILED"


def _now():
    return datetime.now().isoformat()


def _conversation_id(node_a, node_b):

    nodes = sorted(
        [
            str(node_a),
            str(node_b)
        ]
    )

    return (
        f"{nodes[0]}:"
        f"{nodes[1]}"
    )


def _get_user(node_id):

    node_id = str(node_id)

    if node_id == GATEWAY_ID:

        return {
            "node_id": GATEWAY_ID,
            "user_id": GATEWAY_ID,
            "name": GATEWAY_NAME,
            "status": "online",
            "last_seen": None,
            "enabled": True
        }

    node = get_node(node_id)

    if node is None:
        return None

    return {
        "node_id":
            node["node_id"],

        "user_id":
            node["node_id"],

        "name":
            node["name"],

        "status":
            node.get("status"),

        "last_seen":
            node.get("last_seen"),

        "enabled":
            bool(node.get("enabled"))
    }


def validate_chat_users(
    sender_node_id,
    receiver_node_id
):

    if not sender_node_id:
        raise ValueError(
            "Sender is required"
        )

    if not receiver_node_id:
        raise ValueError(
            "Receiver is required"
        )

    if (
        sender_node_id ==
        receiver_node_id
    ):
        raise ValueError(
            "Sender and receiver cannot be the same"
        )

    sender =_get_user(
            sender_node_id
        )

    receiver =_get_user(
            receiver_node_id
        )

    if sender is None:
        raise ValueError(
            "Sender not found"
        )

    if receiver is None:
        raise ValueError(
            "Receiver not found"
        )

    # Private Chat is Gateway -> Node.
    if (
        sender_node_id !=
        GATEWAY_ID
    ):
        raise ValueError(
            "Private Chat sender must be the gateway"
        )

    return sender, receiver


def get_or_create_conversation(
    node_a,
    node_b
):

    validate_chat_users(
        node_a,
        node_b
    )

    conversation_id =_conversation_id(
            node_a,
            node_b
        )

    now = _now()

    connection = get_connection()

    cursor =  connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM chat_conversations
        WHERE conversation_id = ?
        """,
        (
            conversation_id,
        )
    )

    row = cursor.fetchone()

    if row is None:

        cursor.execute(
            """
            INSERT INTO chat_conversations
            (
                conversation_id,
                node_a,
                node_b,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                min(node_a, node_b),
                max(node_a, node_b),
                now,
                now
            )
        )

        connection.commit()

        cursor.execute(
            """
            SELECT *
            FROM chat_conversations
            WHERE conversation_id = ?
            """,
            (
                conversation_id,
            )
        )

        row = cursor.fetchone()

    connection.close()

    return dict(row)


def send_message(
    sender_node_id,
    receiver_node_id,
    message_text
):

    validate_chat_users(
        sender_node_id,
        receiver_node_id
    )

    message_text = str(
            message_text or ""
        ).strip()

    if not message_text:
        raise ValueError(
            "Message cannot be empty"
        )

    if len(message_text) > 500:
        raise ValueError(
            "Message is too long. Maximum 500 characters."
        )

    conversation = get_or_create_conversation(
            sender_node_id,
            receiver_node_id
        )

    message_id =  str(uuid.uuid4())

    now = _now()

    connection =  get_connection()

    cursor = connection.cursor()

    # DELIVERED means the gateway accepted and stored it.
    # No LoRa/M2M packet is created.
    status =    STATUS_DELIVERED

    cursor.execute(
        """
        INSERT INTO chat_messages
        (
            message_id,
            conversation_id,
            sender_node_id,
            receiver_node_id,
            message_text,
            status,
            created_at,
            sent_at,
            delivered_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            conversation[
                "conversation_id"
            ],
            sender_node_id,
            receiver_node_id,
            message_text,
            status,
            now,
            now,
            now
        )
    )

    cursor.execute(
        """
        UPDATE chat_conversations
        SET updated_at = ?
        WHERE conversation_id = ?
        """,
        (
            now,
            conversation[
                "conversation_id"
            ]
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message":
            get_message(message_id)
    }


def get_message(message_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM chat_messages
        WHERE message_id = ?
        """,
        (
            message_id,
        )
    )

    row =  cursor.fetchone()

    connection.close()

    return (
        dict(row)
        if row is not None
        else None
    )


def mark_delivered(message_id):

    message =  get_message(
            message_id
        )

    if message is None:
        raise ValueError(
            "Message not found"
        )

    if message["status"] == STATUS_SEEN:
        return {
            "success": True,
            "message": message
        }

    now = _now()

    connection =      get_connection()

    connection.execute(
        """
        UPDATE chat_messages
        SET
            status = ?,
            delivered_at =
                COALESCE(
                    delivered_at,
                    ?
                )
        WHERE message_id = ?
        """,
        (
            STATUS_DELIVERED,
            now,
            message_id
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message":
            get_message(
                message_id
            )
    }


def mark_seen(
    message_id,
    receiver_node_id
):

    message = get_message(
            message_id
        )

    if message is None:
        raise ValueError(
            "Message not found"
        )

    if (
        message["receiver_node_id"]
        != receiver_node_id
    ):
        raise ValueError(
            "Receiver does not own this message"
        )

    now = _now()

    connection = get_connection()

    connection.execute(
        """
        UPDATE chat_messages
        SET
            status = ?,
            delivered_at =
                COALESCE(
                    delivered_at,
                    ?
                ),
            seen_at = ?
        WHERE message_id = ?
        """,
        (
            STATUS_SEEN,
            now,
            now,
            message_id
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message":
            get_message(
                message_id
            )
    }


def get_conversations(node_id):

    connection =    get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM chat_conversations
        WHERE node_a = ?
           OR node_b = ?
        ORDER BY updated_at DESC
        """,
        (
            node_id,
            node_id
        )
    )

    rows =        cursor.fetchall()

    connection.close()

    result = []

    for row in rows:

        conversation = dict(row)

        other = (
                conversation["node_b"]
                if conversation["node_a"] == node_id
                else conversation["node_a"]
                )

        conversation["user"] = _get_user(other)

        result.append(
            conversation
        )

    return result


def get_messages(
    node_id,
    conversation_id,
    limit=100
):

    limit = max(
            1,
            min(
                int(limit),
                200
            )
         )

    connection = get_connection()

    cursor =      connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM chat_messages
        WHERE conversation_id = ?
        AND (
            sender_node_id = ?
            OR receiver_node_id = ?
        )
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            conversation_id,
            node_id,
            node_id,
            limit
        )
    )

    rows = cursor.fetchall()

    connection.close()

    messages = [
            dict(row)
            for row in rows
           ]

    messages.reverse()

    for message in messages:

        message["sender"] =_get_user(
                message[
                    "sender_node_id"
                ]
            )

        message["receiver"] =_get_user(
                message[
                    "receiver_node_id"
                ]
            )

    return messages


def get_chat_users(
    exclude_node_id=None
):

    connection = get_connection()

    cursor =        connection.cursor()

    cursor.execute(
        """
        SELECT
            node_id,
            name,
            status,
            last_seen,
            enabled
        FROM nodes
        WHERE enabled = 1
        ORDER BY name
        """
    )

    rows =     cursor.fetchall()

    connection.close()

    result = []

    for row in rows:

        node_id = row["node_id"]

        if (
            exclude_node_id and
            node_id == exclude_node_id
        ):
            continue

        result.append(
            {
                "node_id":
                    node_id,

                "user_id":
                    node_id,

                "name":
                    row["name"],

                "status":
                    row["status"],

                "last_seen":
                    row["last_seen"],

                "enabled":
                    bool(
                        row["enabled"]
                    )
            }
        )

    return result