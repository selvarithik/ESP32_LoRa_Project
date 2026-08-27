"""
chat_manager.py

PRIVATE USER-TO-USER CHAT

Important:
- Chat is completely independent from LoRa communication.
- Chat does NOT call communication_manager.
- Chat does NOT create LoRa packets.
- Chat does NOT enter the M2M communication queue.
- Chat messages are stored only in the server database.
- node_id is the permanent user identity.
- Node Management name is used as the display name.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from database import get_connection
from node_manager import get_node


# ============================================================
# STATUS
# ============================================================

STATUS_SENT = "SENT"
STATUS_DELIVERED = "DELIVERED"
STATUS_SEEN = "SEEN"
STATUS_FAILED = "FAILED"


# ============================================================
# HELPERS
# ============================================================

def _now():
    return datetime.now().isoformat()


def _conversation_id(node_a, node_b):
    """
    Generate one stable conversation ID for two nodes.

    Example:
        NODE01 + NODE02
        -> NODE01:NODE02

    Order does not matter.
    """

    nodes = sorted([
        str(node_a),
        str(node_b)
    ])

    return f"{nodes[0]}:{nodes[1]}"


def _message_to_dict(row):
    if row is None:
        return None

    return dict(row)


def _get_user(node_id):
    """
    Get user information from Node Management.

    node_id = permanent identity
    name    = display name
    """

    if not node_id:
        return None

    node = get_node(str(node_id))

    if node is None:
        return None

    return {
        "node_id": node["node_id"],
        "name": node.get("name") or str(node["node_id"]),
        "status": node.get("status") or "offline",
        "last_seen": node.get("last_seen"),
        "enabled": bool(node.get("enabled"))
    }


# ============================================================
# VALIDATE CHAT USERS
# ============================================================

def validate_chat_users(
    sender_node_id,
    receiver_node_id
):
    """
    Validate both users before allowing a private chat.

    Chat is allowed only between registered nodes.
    """

    sender_node_id = str(
        sender_node_id or ""
    ).strip()

    receiver_node_id = str(
        receiver_node_id or ""
    ).strip()

    if not sender_node_id:
        raise ValueError(
            "Sender node_id is required"
        )

    if not receiver_node_id:
        raise ValueError(
            "Receiver node_id is required"
        )

    if sender_node_id == receiver_node_id:
        raise ValueError(
            "Sender and receiver cannot be the same"
        )

    sender = _get_user(
        sender_node_id
    )

    receiver = _get_user(
        receiver_node_id
    )

    if sender is None:
        raise ValueError(
            f"Sender node not found: {sender_node_id}"
        )

    if receiver is None:
        raise ValueError(
            f"Receiver node not found: {receiver_node_id}"
        )

    if not sender["enabled"]:
        raise ValueError(
            f"Sender node is disabled: {sender_node_id}"
        )

    if not receiver["enabled"]:
        raise ValueError(
            f"Receiver node is disabled: {receiver_node_id}"
        )

    return sender, receiver


# ============================================================
# GET / CREATE CONVERSATION
# ============================================================

def get_or_create_conversation(
    node_a,
    node_b
):
    """
    Get an existing private conversation.

    If it does not exist, create it.

    This only creates a database conversation.
    No LoRa communication is performed.
    """

    node_a = str(node_a).strip()
    node_b = str(node_b).strip()

    validate_chat_users(
        node_a,
        node_b
    )

    conversation_id = _conversation_id(
        node_a,
        node_b
    )

    now = _now()

    connection = get_connection()
    cursor = connection.cursor()

    try:

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

        return dict(row)

    finally:
        connection.close()


# ============================================================
# SEND PRIVATE CHAT MESSAGE
# ============================================================

def send_message(
    sender_node_id,
    receiver_node_id,
    message_text
):
    """
    Store one private user-to-user message.

    IMPORTANT:
        This function DOES NOT call communication_manager.

    Therefore:
        No LoRa packet
        No M2M packet
        No communication queue
        No routing
        No E220 transmission
    """

    sender_node_id = str(
        sender_node_id or ""
    ).strip()

    receiver_node_id = str(
        receiver_node_id or ""
    ).strip()

    message_text = str(
        message_text or ""
    ).strip()

    # --------------------------------------------------------
    # Validate users
    # --------------------------------------------------------

    sender, receiver = validate_chat_users(
        sender_node_id,
        receiver_node_id
    )

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    if not message_text:
        raise ValueError(
            "Message cannot be empty"
        )

    if len(message_text) > 500:
        raise ValueError(
            "Message is too long. "
            "Maximum 500 characters."
        )

    # --------------------------------------------------------
    # Get/create conversation
    # --------------------------------------------------------

    conversation = get_or_create_conversation(
        sender_node_id,
        receiver_node_id
    )

    message_id = str(
        uuid.uuid4()
    )

    now = _now()

    # --------------------------------------------------------
    # Store message
    # --------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

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
                sent_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                conversation["conversation_id"],
                sender_node_id,
                receiver_node_id,
                message_text,
                STATUS_SENT,
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
                conversation["conversation_id"]
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    #
    # DO NOT DO THIS:
    #
    # communication_manager.create_message(...)
    #
    # communication_manager.send(...)
    #
    # Chat is server/database only.
    # --------------------------------------------------------

    return {
        "success": True,
        "message": get_message(message_id)
    }


# ============================================================
# GET ONE MESSAGE
# ============================================================

def get_message(
    message_id
):
    """
    Return one private chat message.
    """

    if not message_id:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM chat_messages
            WHERE message_id = ?
            """,
            (
                str(message_id),
            )
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return _message_to_dict(row)

    finally:
        connection.close()


# ============================================================
# MARK MESSAGE DELIVERED
# ============================================================

def mark_delivered(
    message_id
):
    """
    Change SENT -> DELIVERED.

    This is a server-side chat status only.
    """

    if not message_id:
        raise ValueError(
            "message_id is required"
        )

    now = _now()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE chat_messages
            SET
                status = ?,
                delivered_at = ?
            WHERE
                message_id = ?
            AND
                status = ?
            """,
            (
                STATUS_DELIVERED,
                now,
                str(message_id),
                STATUS_SENT
            )
        )

        connection.commit()

        changed = cursor.rowcount > 0

    finally:
        connection.close()

    return {
        "success": changed,
        "message": get_message(
            message_id
        )
    }


# ============================================================
# MARK MESSAGE SEEN
# ============================================================

def mark_seen(
    message_id,
    receiver_node_id
):
    """
    Mark a received private message as SEEN.

    Only the actual receiver can mark it as seen.
    """

    message_id = str(
        message_id or ""
    ).strip()

    receiver_node_id = str(
        receiver_node_id or ""
    ).strip()

    if not message_id:
        raise ValueError(
            "message_id is required"
        )

    if not receiver_node_id:
        raise ValueError(
            "receiver_node_id is required"
        )

    # Make sure receiver exists.
    receiver = _get_user(
        receiver_node_id
    )

    if receiver is None:
        raise ValueError(
            "Receiver node not found"
        )

    now = _now()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
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
            WHERE
                message_id = ?
            AND
                receiver_node_id = ?
            AND
                status != ?
            """,
            (
                STATUS_SEEN,
                now,
                now,
                message_id,
                receiver_node_id,
                STATUS_SEEN
            )
        )

        connection.commit()

        changed = cursor.rowcount > 0

    finally:
        connection.close()

    return {
        "success": changed,
        "message": get_message(
            message_id
        )
    }


# ============================================================
# GET CONVERSATIONS
# ============================================================

def get_conversations(
    node_id
):
    """
    Return all private conversations belonging to one user.
    """

    node_id = str(
        node_id or ""
    ).strip()

    if not node_id:
        raise ValueError(
            "node_id is required"
        )

    user = _get_user(node_id)

    if user is None:
        raise ValueError(
            "Node not found"
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT

                c.*,

                (
                    SELECT
                        message_text
                    FROM chat_messages m
                    WHERE
                        m.conversation_id =
                        c.conversation_id
                    ORDER BY
                        m.id DESC
                    LIMIT 1
                ) AS last_message,

                (
                    SELECT
                        created_at
                    FROM chat_messages m
                    WHERE
                        m.conversation_id =
                        c.conversation_id
                    ORDER BY
                        m.id DESC
                    LIMIT 1
                ) AS last_message_at,

                (
                    SELECT
                        COUNT(*)
                    FROM chat_messages m
                    WHERE
                        m.conversation_id =
                        c.conversation_id
                    AND
                        m.receiver_node_id = ?
                    AND
                        m.status != ?
                ) AS unread_count

            FROM chat_conversations c

            WHERE
                c.node_a = ?
            OR
                c.node_b = ?

            ORDER BY
                c.updated_at DESC
            """,
            (
                node_id,
                STATUS_SEEN,
                node_id,
                node_id
            )
        )

        rows = cursor.fetchall()

    finally:
        connection.close()

    result = []

    for row in rows:

        conversation = dict(row)

        if str(
            conversation["node_a"]
        ) == node_id:

            other_node_id = (
                conversation["node_b"]
            )

        else:

            other_node_id = (
                conversation["node_a"]
            )

        conversation["user"] = _get_user(
            other_node_id
        )

        result.append(
            conversation
        )

    return result


# ============================================================
# GET MESSAGES BETWEEN TWO USERS
# ============================================================

def get_messages(
    node_id,
    conversation_id,
    limit=100
):
    """
    Return messages belonging to a conversation.

    Only messages involving node_id are returned.
    """

    node_id = str(
        node_id or ""
    ).strip()

    conversation_id = str(
        conversation_id or ""
    ).strip()

    if not node_id:
        raise ValueError(
            "node_id is required"
        )

    if not conversation_id:
        raise ValueError(
            "conversation_id is required"
        )

    try:
        limit = int(limit)

    except (
        TypeError,
        ValueError
    ):
        limit = 100

    limit = max(
        1,
        min(
            limit,
            500
        )
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM chat_messages
            WHERE
                conversation_id = ?
            AND
                (
                    sender_node_id = ?
                    OR
                    receiver_node_id = ?
                )
            ORDER BY
                id DESC
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

    finally:
        connection.close()

    messages = [
        dict(row)
        for row in rows
    ]

    # Database returns newest first.
    # Frontend wants oldest -> newest.
    messages.reverse()

    for message in messages:

        message["sender"] = _get_user(
            message.get(
                "sender_node_id"
            )
        )

        message["receiver"] = _get_user(
            message.get(
                "receiver_node_id"
            )
        )

    return messages


# ============================================================
# GET MESSAGES BETWEEN TWO NODE IDs
# ============================================================

def get_messages_between_users(
    node_a,
    node_b,
    limit=100
):
    """
    Convenience function used by the server API.

    The current server endpoint receives:

        user_id
        with_user_id

    and needs to convert them into a conversation.
    """

    node_a = str(
        node_a or ""
    ).strip()

    node_b = str(
        node_b or ""
    ).strip()

    validate_chat_users(
        node_a,
        node_b
    )

    conversation_id = _conversation_id(
        node_a,
        node_b
    )

    return get_messages(
        node_a,
        conversation_id,
        limit
    )


# ============================================================
# GET AVAILABLE CHAT USERS
# ============================================================

def get_chat_users(
    exclude_node_id=None
):
    """
    Return all enabled Node Management users.

    Node name is used as the display name.

    The current user can optionally be excluded.
    """

    exclude_node_id = str(
        exclude_node_id or ""
    ).strip()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        if exclude_node_id:

            cursor.execute(
                """
                SELECT
                    node_id,
                    name,
                    status,
                    last_seen,
                    enabled
                FROM nodes
                WHERE
                    enabled = 1
                AND
                    node_id != ?
                ORDER BY
                    name COLLATE NOCASE
                """,
                (
                    exclude_node_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    node_id,
                    name,
                    status,
                    last_seen,
                    enabled
                FROM nodes
                WHERE
                    enabled = 1
                ORDER BY
                    name COLLATE NOCASE
                """
            )

        rows = cursor.fetchall()

    finally:
        connection.close()

    return [
        {
            "node_id": row["node_id"],
            "name": (
                row["name"]
                or row["node_id"]
            ),
            "status": (
                row["status"]
                or "offline"
            ),
            "last_seen": row["last_seen"],
            "enabled": bool(
                row["enabled"]
            )
        }
        for row in rows
    ]


# ============================================================
# ALIASES / SERVER COMPATIBILITY
# ============================================================

chat_send_message = send_message
chat_get_message = get_message
chat_mark_delivered = mark_delivered
chat_mark_seen = mark_seen
chat_get_conversations = get_conversations
chat_get_messages = get_messages