"""
Command Manager (Phase 1 & Phase 2 — Command Core & ACK/Response System)

Server-side command lifecycle management, state machine, ACK protocol,
ESP32 response processing, retry preparation, timeout tracking, and persistence.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from database import get_connection


# ============================================================
# CONSTANTS & STATE MACHINE
# ============================================================

COMMAND_STATES = (
    "QUEUED",
    "SENT",
    "WAITING_ACK",
    "ACK_RECEIVED",
    "EXECUTING",
    "RESPONSE_RECEIVED",
    "TIMEOUT",
    "FAILED",
    "CANCELLED",
    "COMPLETED"
)

TERMINAL_STATES = (
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "TIMEOUT"
)

VALID_TRANSITIONS: Dict[str, tuple[str, ...]] = {
    "QUEUED": ("SENT", "WAITING_ACK", "ACK_RECEIVED", "CANCELLED", "FAILED", "TIMEOUT"),
    "SENT": ("WAITING_ACK", "ACK_RECEIVED", "CANCELLED", "FAILED", "TIMEOUT"),
    "WAITING_ACK": ("ACK_RECEIVED", "TIMEOUT", "FAILED", "CANCELLED", "COMPLETED"),
    "ACK_RECEIVED": ("EXECUTING", "RESPONSE_RECEIVED", "COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"),
    "EXECUTING": ("RESPONSE_RECEIVED", "COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"),
    "RESPONSE_RECEIVED": ("COMPLETED", "FAILED"),
    "TIMEOUT": ("QUEUED",),    # Allowed only via explicit retry
    "FAILED": ("QUEUED",),     # Allowed only via explicit retry
    "CANCELLED": (),
    "COMPLETED": ()
}

DEFAULT_TIMEOUT_SECONDS = 30
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 3600

DEFAULT_MAX_RETRIES = 3
MIN_RETRIES = 0
MAX_RETRIES_LIMIT = 10

DEFAULT_PRIORITY = 1
MIN_PRIORITY = 1
MAX_PRIORITY = 10

SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")
SAFE_COMMAND_TYPE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


# ============================================================
# HELPER FUNCTIONS & ID GENERATION
# ============================================================

def make_command_id() -> str:
    """Generate a unique command ID in format CMD-XXXXXXXXXXXX."""
    return f"CMD-{uuid.uuid4().hex[:12].upper()}"


def make_event_id() -> str:
    """Generate a unique event ID in format EVT-XXXXXXXXXXXX."""
    return f"EVT-{uuid.uuid4().hex[:12].upper()}"


def validate_safe_id(value: Any, field_name: str = "identifier") -> str:
    """Validate that an identifier contains only safe characters."""
    text = str(value or "").strip()
    if not text or not SAFE_ID_PATTERN.match(text):
        raise ValueError(f"Invalid {field_name}")
    return text


def validate_node_id(node_id: Any) -> str:
    """Validate target node ID."""
    return validate_safe_id(node_id, "node_id")


def validate_command_type(command_type: Any) -> str:
    """Validate command type string."""
    text = str(command_type or "").strip()
    if not text:
        raise ValueError("command_type is required")
    if len(text) > 64:
        raise ValueError("command_type is too long (maximum 64 characters)")
    if not SAFE_COMMAND_TYPE_PATTERN.match(text):
        raise ValueError("command_type contains invalid characters")
    return text


def validate_payload(payload: Any) -> Dict[str, Any]:
    """Validate and sanitize command payload."""
    if payload is None:
        return {}

    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except (ValueError, json.JSONDecodeError) as err:
            raise ValueError(f"Invalid JSON payload: {err}") from err
        if not isinstance(parsed, dict):
            raise ValueError("Payload must be a JSON object (dictionary)")
        return parsed

    if isinstance(payload, dict):
        try:
            json.dumps(payload)
        except (TypeError, ValueError) as err:
            raise ValueError(f"Payload is not JSON serializable: {err}") from err
        return payload

    raise ValueError("Payload must be a dictionary or a valid JSON string")


def validate_priority(priority: Any) -> int:
    """Validate command priority."""
    try:
        val = int(priority)
    except (TypeError, ValueError) as err:
        raise ValueError("priority must be an integer") from err

    if not MIN_PRIORITY <= val <= MAX_PRIORITY:
        raise ValueError(
            f"priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}"
        )
    return val


def validate_retries(max_retries: Any) -> int:
    """Validate max retries."""
    try:
        val = int(max_retries)
    except (TypeError, ValueError) as err:
        raise ValueError("max_retries must be an integer") from err

    if not MIN_RETRIES <= val <= MAX_RETRIES_LIMIT:
        raise ValueError(
            f"max_retries must be between {MIN_RETRIES} and {MAX_RETRIES_LIMIT}"
        )
    return val


def validate_timeout(timeout_seconds: Any) -> int:
    """Validate command timeout in seconds."""
    try:
        val = int(timeout_seconds)
    except (TypeError, ValueError) as err:
        raise ValueError("timeout_seconds must be an integer") from err

    if not MIN_TIMEOUT_SECONDS <= val <= MAX_TIMEOUT_SECONDS:
        raise ValueError(
            f"timeout_seconds must be between {MIN_TIMEOUT_SECONDS} and {MAX_TIMEOUT_SECONDS}"
        )
    return val


def validate_state(state: Any) -> str:
    """Validate that state string is a valid command state."""
    text = str(state or "").strip().upper()
    if text not in COMMAND_STATES:
        raise ValueError(f"Invalid command state: {state}")
    return text


def _calculate_timeout_at(start_time_iso: str, timeout_seconds: int) -> str:
    """Compute ISO timeout timestamp from start time and timeout seconds."""
    start_dt = datetime.fromisoformat(start_time_iso)
    timeout_dt = start_dt + timedelta(seconds=timeout_seconds)
    return timeout_dt.isoformat()


def normalize_command(row: Any) -> Dict[str, Any]:
    """Convert SQLite Row object into a clean normalized command dict."""
    if row is None:
        return {}

    data = dict(row)

    # Deserialize payload
    payload_raw = data.get("payload")
    if isinstance(payload_raw, str) and payload_raw.strip():
        try:
            data["payload"] = json.loads(payload_raw)
        except Exception:
            data["payload"] = payload_raw
    elif payload_raw is None:
        data["payload"] = {}

    # Deserialize result
    result_raw = data.get("result")
    if isinstance(result_raw, str) and result_raw.strip():
        try:
            data["result"] = json.loads(result_raw)
        except Exception:
            data["result"] = result_raw

    # Ensure numeric types
    data["id"] = int(data.get("id") or 0)
    data["priority"] = int(data.get("priority") or 1)
    data["retry_count"] = int(data.get("retry_count") or 0)
    data["max_retries"] = int(data.get("max_retries") or 0)
    data["timeout_seconds"] = int(data.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS)

    # Ensure Phase 2 fields exist in dictionary
    data["ack_at"] = data.get("ack_at")
    data["executing_at"] = data.get("executing_at")
    data["response_at"] = data.get("response_at")
    data["ack_status"] = data.get("ack_status")
    data["ack_message"] = data.get("ack_message")

    return data


# ============================================================
# COMMAND EVENT LOGGING & AUDIT
# ============================================================

def record_command_event(
    command_id: str,
    node_id: str,
    event_type: str,
    state: str,
    details: Optional[Union[Dict[str, Any], str]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Record an immutable lifecycle event in the command_events audit table."""
    command_id = validate_safe_id(command_id, "command_id")
    node_id = validate_node_id(node_id)
    event_id = make_event_id()
    now = datetime.now().isoformat()

    details_json = None
    if details is not None:
        if isinstance(details, (dict, list)):
            details_json = json.dumps(details)
        else:
            details_json = str(details)

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO command_events (
                event_id,
                command_id,
                node_id,
                event_type,
                state,
                details,
                error,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            command_id,
            node_id,
            event_type,
            state,
            details_json,
            error,
            now
        ))
        connection.commit()
    finally:
        connection.close()

    return {
        "event_id": event_id,
        "command_id": command_id,
        "node_id": node_id,
        "event_type": event_type,
        "state": state,
        "details": details,
        "error": error,
        "created_at": now
    }


def get_command_events(command_id: str) -> List[Dict[str, Any]]:
    """Retrieve full chronological audit history for a command."""
    command_id = validate_safe_id(command_id, "command_id")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM command_events
            WHERE command_id = ?
            ORDER BY id ASC
        """, (command_id,))
        rows = cursor.fetchall()
    finally:
        connection.close()

    events = []
    for row in rows:
        evt = dict(row)
        if evt.get("details"):
            try:
                evt["details"] = json.loads(evt["details"])
            except Exception:
                pass
        events.append(evt)

    return events


# ============================================================
# COMMAND OPERATIONS (PHASE 1 CORE)
# ============================================================

def create_command(
    node_id: str,
    command_type: str,
    payload: Optional[Union[Dict[str, Any], str]] = None,
    priority: int = DEFAULT_PRIORITY,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    command_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new command in the QUEUED state."""
    node_id = validate_node_id(node_id)
    command_type = validate_command_type(command_type)
    payload_dict = validate_payload(payload)
    priority = validate_priority(priority)
    max_retries = validate_retries(max_retries)
    timeout_seconds = validate_timeout(timeout_seconds)

    if command_id:
        command_id = validate_safe_id(command_id, "command_id")
    else:
        command_id = make_command_id()

    now = datetime.now().isoformat()
    timeout_at = _calculate_timeout_at(now, timeout_seconds)
    payload_json = json.dumps(payload_dict)

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO commands (
                command_id,
                node_id,
                command_type,
                payload,
                state,
                priority,
                retry_count,
                max_retries,
                timeout_seconds,
                created_at,
                sent_at,
                ack_at,
                executing_at,
                response_at,
                ack_status,
                ack_message,
                timeout_at,
                completed_at,
                cancelled_at,
                error,
                result,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            command_id,
            node_id,
            command_type,
            payload_json,
            "QUEUED",
            priority,
            0,
            max_retries,
            timeout_seconds,
            now,
            None,
            None,
            None,
            None,
            None,
            None,
            timeout_at,
            None,
            None,
            None,
            None,
            now
        ))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    # Record event
    record_command_event(
        command_id=command_id,
        node_id=node_id,
        event_type="COMMAND_CREATED",
        state="QUEUED",
        details={"command_type": command_type, "payload": payload_dict}
    )

    command = get_command(command_id)
    if command is None:
        raise RuntimeError("Failed to retrieve created command")
    return command


def get_command(command_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a command by its unique command_id."""
    command_id = validate_safe_id(command_id, "command_id")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM commands
            WHERE command_id = ?
            LIMIT 1
        """, (command_id,))
        row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return normalize_command(row)


def list_commands(
    node_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List commands with optional filtering by node_id and state."""
    query = "SELECT * FROM commands"
    conditions = []
    params = []

    if node_id:
        safe_node_id = validate_node_id(node_id)
        conditions.append("node_id = ?")
        params.append(safe_node_id)

    if state:
        safe_state = validate_state(state)
        conditions.append("state = ?")
        params.append(safe_state)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([max(1, min(int(limit), 500)), max(0, int(offset))])

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    finally:
        connection.close()

    return [normalize_command(row) for row in rows]


def get_node_commands(
    node_id: str,
    limit: int = 50,
    state: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get command history for a specific node."""
    return list_commands(node_id=node_id, state=state, limit=limit)


def update_command_state(
    command_id: str,
    new_state: str,
    error: Optional[str] = None,
    result: Optional[Union[Dict[str, Any], str]] = None
) -> Dict[str, Any]:
    """
    Update a command's state according to the state machine rules.
    Validates state transitions and updates corresponding timestamp fields.
    """
    command_id = validate_safe_id(command_id, "command_id")
    new_state = validate_state(new_state)

    command = get_command(command_id)
    if command is None:
        raise ValueError(f"Command not found: {command_id}")

    current_state = command["state"]

    if new_state != current_state:
        allowed = VALID_TRANSITIONS.get(current_state, ())
        if new_state not in allowed:
            raise ValueError(
                f"Cannot transition command from {current_state} to {new_state}"
            )

    now = datetime.now().isoformat()
    sent_at = command.get("sent_at")
    timeout_at = command.get("timeout_at")
    completed_at = command.get("completed_at")
    cancelled_at = command.get("cancelled_at")
    err_text = error if error is not None else command.get("error")

    # Handle state-specific timestamps
    if new_state == "SENT":
        if not sent_at:
            sent_at = now
        timeout_at = _calculate_timeout_at(now, command["timeout_seconds"])
    elif new_state == "COMPLETED":
        completed_at = now
    elif new_state == "CANCELLED":
        cancelled_at = now
    elif new_state == "TIMEOUT":
        if not err_text:
            err_text = "Command timed out"
    elif new_state == "FAILED":
        if not err_text:
            err_text = "Command execution failed"

    result_json = None
    if result is not None:
        if isinstance(result, (dict, list)):
            result_json = json.dumps(result)
        else:
            result_json = str(result)
    else:
        existing_res = command.get("result")
        result_json = json.dumps(existing_res) if isinstance(existing_res, (dict, list)) else existing_res

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE commands
            SET state = ?,
                sent_at = ?,
                timeout_at = ?,
                completed_at = ?,
                cancelled_at = ?,
                error = ?,
                result = ?,
                updated_at = ?
            WHERE command_id = ?
        """, (
            new_state,
            sent_at,
            timeout_at,
            completed_at,
            cancelled_at,
            err_text,
            result_json,
            now,
            command_id
        ))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    updated = get_command(command_id)
    if updated is None:
        raise RuntimeError("Failed to retrieve updated command")
    return updated


def mark_command_sent(command_id: str) -> Dict[str, Any]:
    """Mark a queued command as SENT."""
    cmd = update_command_state(command_id, "SENT")
    record_command_event(
        command_id=command_id,
        node_id=cmd["node_id"],
        event_type="COMMAND_SENT",
        state="SENT"
    )
    return cmd


def mark_command_waiting_ack(command_id: str) -> Dict[str, Any]:
    """Mark a sent command as WAITING_ACK."""
    return update_command_state(command_id, "WAITING_ACK")


def cancel_command(command_id: str, reason: str = "User cancelled") -> Dict[str, Any]:
    """Cancel a command."""
    cmd = update_command_state(command_id, "CANCELLED", error=reason)
    record_command_event(
        command_id=command_id,
        node_id=cmd["node_id"],
        event_type="CANCELLED",
        state="CANCELLED",
        error=reason
    )
    return cmd


def handle_command_timeout(command_id: str) -> Dict[str, Any]:
    """
    Handle timeout for a single command.
    Transitions active non-terminal commands to TIMEOUT state.
    """
    command = get_command(command_id)
    if command is None:
        raise ValueError(f"Command not found: {command_id}")

    if command["state"] in TERMINAL_STATES:
        raise ValueError(
            f"Cannot time out command in terminal state '{command['state']}'"
        )

    cmd = update_command_state(
        command_id,
        "TIMEOUT",
        error="Command timed out"
    )
    record_command_event(
        command_id=command_id,
        node_id=cmd["node_id"],
        event_type="TIMEOUT",
        state="TIMEOUT",
        error="Command timed out"
    )
    return cmd


def check_timeouts() -> List[Dict[str, Any]]:
    """
    Check for active commands that have exceeded their timeout timestamp.
    Returns list of commands transitioned to TIMEOUT.
    """
    now = datetime.now().isoformat()
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT command_id
            FROM commands
            WHERE state IN ('QUEUED', 'SENT', 'WAITING_ACK', 'ACK_RECEIVED', 'EXECUTING')
              AND timeout_at IS NOT NULL
              AND timeout_at <= ?
        """, (now,))
        rows = cursor.fetchall()
    finally:
        connection.close()

    timed_out_commands = []
    for row in rows:
        cid = row["command_id"]
        try:
            updated = handle_command_timeout(cid)
            timed_out_commands.append(updated)
        except Exception:
            pass

    return timed_out_commands


def delete_command(command_id: str) -> bool:
    """Delete a command record (for cleanup or administrative purposes)."""
    command_id = validate_safe_id(command_id, "command_id")
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM command_events WHERE command_id = ?", (command_id,))
        cursor.execute("DELETE FROM commands WHERE command_id = ?", (command_id,))
        connection.commit()
        deleted = cursor.rowcount > 0
    finally:
        connection.close()

    return deleted


# ============================================================
# PHASE 2 — ACK PROTOCOL & HANDLING
# ============================================================

def _update_ack_fields(
    command_id: str,
    ack_time: str,
    status: str,
    message: Optional[str] = None
) -> None:
    """Internal helper to set ACK timestamp and metadata."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE commands
            SET ack_at = ?,
                ack_status = ?,
                ack_message = ?,
                updated_at = ?
            WHERE command_id = ?
        """, (ack_time, status, message, datetime.now().isoformat(), command_id))
        connection.commit()
    finally:
        connection.close()


def process_command_ack(
    command_id: str,
    node_id: str,
    status: str = "RECEIVED",
    message: Optional[str] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an incoming ACK from a node for a command.
    Includes verification, cross-node validation, duplicate ACK idempotency,
    and state transition handling.
    """
    command_id = validate_safe_id(command_id, "command_id")
    node_id = validate_node_id(node_id)
    status = str(status or "RECEIVED").strip().upper()

    command = get_command(command_id)
    if command is None:
        raise ValueError(f"Command not found: {command_id}")

    if command["node_id"] != node_id:
        raise ValueError(
            f"Command {command_id} belongs to node '{command['node_id']}', not '{node_id}'"
        )

    current_state = command["state"]

    # Duplicate ACK protection
    if current_state in ("ACK_RECEIVED", "EXECUTING", "RESPONSE_RECEIVED", "COMPLETED"):
        return {
            "success": True,
            "command_id": command_id,
            "state": current_state,
            "duplicate": True,
            "message": "ACK already processed",
            "command": command
        }

    # Reject ACK for terminal states (CANCELLED, TIMEOUT, or terminal FAILED)
    if current_state in ("CANCELLED", "TIMEOUT", "FAILED"):
        raise ValueError(
            f"Cannot accept ACK for command in state '{current_state}'"
        )

    now = datetime.now().isoformat()
    ack_time = timestamp if timestamp else now

    # Check for negative ACK / rejection
    if status in ("NACK", "REJECTED", "ERROR", "FAILED"):
        err_msg = message or f"Command rejected by node with status {status}"
        _update_ack_fields(command_id, ack_time, status, message)
        updated = update_command_state(
            command_id,
            "FAILED",
            error=err_msg
        )
        record_command_event(
            command_id=command_id,
            node_id=node_id,
            event_type="FAILED",
            state="FAILED",
            details={"ack_status": status, "message": message},
            error=err_msg
        )
        final_cmd = get_command(command_id)
        return {
            "success": True,
            "command_id": command_id,
            "state": "FAILED",
            "duplicate": False,
            "command": final_cmd
        }

    # Affirmative ACK (RECEIVED, ACCEPTED, OK, etc.)
    _update_ack_fields(command_id, ack_time, status, message)
    updated = update_command_state(command_id, "ACK_RECEIVED")
    record_command_event(
        command_id=command_id,
        node_id=node_id,
        event_type="ACK_RECEIVED",
        state="ACK_RECEIVED",
        details={"ack_status": status, "message": message}
    )
    final_cmd = get_command(command_id)
    return {
        "success": True,
        "command_id": command_id,
        "state": "ACK_RECEIVED",
        "duplicate": False,
        "command": final_cmd
    }


# ============================================================
# PHASE 2 — EXECUTION STATE HANDLING
# ============================================================

def mark_command_executing(
    command_id: str,
    node_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transition a command to EXECUTING state.
    """
    command_id = validate_safe_id(command_id, "command_id")
    command = get_command(command_id)
    if command is None:
        raise ValueError(f"Command not found: {command_id}")

    if node_id and command["node_id"] != node_id:
        raise ValueError(
            f"Command {command_id} belongs to node '{command['node_id']}', not '{node_id}'"
        )

    current_state = command["state"]
    if current_state == "EXECUTING":
        return {
            "success": True,
            "command_id": command_id,
            "state": "EXECUTING",
            "duplicate": True,
            "command": command
        }

    now = datetime.now().isoformat()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE commands
            SET executing_at = ?,
                updated_at = ?
            WHERE command_id = ?
        """, (now, now, command_id))
        connection.commit()
    finally:
        connection.close()

    updated = update_command_state(command_id, "EXECUTING")
    record_command_event(
        command_id=command_id,
        node_id=command["node_id"],
        event_type="EXECUTING",
        state="EXECUTING"
    )
    final_cmd = get_command(command_id)
    return {
        "success": True,
        "command_id": command_id,
        "state": "EXECUTING",
        "duplicate": False,
        "command": final_cmd
    }


# ============================================================
# PHASE 2 — ESP32 RESPONSE PROTOCOL & HANDLING
# ============================================================

def process_command_response(
    command_id: str,
    node_id: str,
    status: str = "SUCCESS",
    data: Optional[Any] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an incoming execution response from a node.
    Stores structured result data, records execution timestamps,
    and transitions state to COMPLETED or FAILED.
    """
    command_id = validate_safe_id(command_id, "command_id")
    node_id = validate_node_id(node_id)
    status = str(status or "SUCCESS").strip().upper()

    command = get_command(command_id)
    if command is None:
        raise ValueError(f"Command not found: {command_id}")

    if command["node_id"] != node_id:
        raise ValueError(
            f"Command {command_id} belongs to node '{command['node_id']}', not '{node_id}'"
        )

    current_state = command["state"]

    # Duplicate response protection
    if current_state in ("COMPLETED", "FAILED"):
        return {
            "success": True,
            "command_id": command_id,
            "state": current_state,
            "duplicate": True,
            "message": "Response already processed",
            "result": command.get("result"),
            "error": command.get("error"),
            "command": command
        }

    if current_state in ("CANCELLED", "TIMEOUT"):
        raise ValueError(
            f"Cannot accept response for command in state '{current_state}'"
        )

    now = datetime.now().isoformat()
    resp_time = timestamp if timestamp else now

    # Prepare structured result
    result_data = data if data is not None else ({"message": message} if message else None)

    # Set response_at in database
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE commands
            SET response_at = ?,
                updated_at = ?
            WHERE command_id = ?
        """, (resp_time, now, command_id))
        connection.commit()
    finally:
        connection.close()

    if status in ("SUCCESS", "OK", "COMPLETED"):
        updated = update_command_state(
            command_id,
            "COMPLETED",
            result=result_data
        )
        record_command_event(
            command_id=command_id,
            node_id=node_id,
            event_type="COMPLETED",
            state="COMPLETED",
            details={"status": status, "data": data, "message": message}
        )
        final_cmd = get_command(command_id)
        return {
            "success": True,
            "command_id": command_id,
            "state": "COMPLETED",
            "result": final_cmd.get("result"),
            "duplicate": False,
            "command": final_cmd
        }
    else:
        err_msg = error or message or f"Command execution failed with status {status}"
        updated = update_command_state(
            command_id,
            "FAILED",
            error=err_msg,
            result=result_data
        )
        record_command_event(
            command_id=command_id,
            node_id=node_id,
            event_type="FAILED",
            state="FAILED",
            details={"status": status, "data": data, "message": message},
            error=err_msg
        )
        final_cmd = get_command(command_id)
        return {
            "success": True,
            "command_id": command_id,
            "state": "FAILED",
            "error": err_msg,
            "result": final_cmd.get("result"),
            "duplicate": False,
            "command": final_cmd
        }


# ============================================================
# PHASE 2 — RETRY SUPPORT
# ============================================================

def prepare_command_retry(command_id: str) -> Dict[str, Any]:
    """
    Prepare an eligible timed-out or failed command for retry.
    Validates retry limit, increments retry_count, and resets state to QUEUED.
    Does NOT automatically transmit anything to network.
    """
    command_id = validate_safe_id(command_id, "command_id")
    command = get_command(command_id)
    if command is None:
        raise ValueError(f"Command not found: {command_id}")

    if command["state"] not in ("TIMEOUT", "FAILED"):
        raise ValueError(
            f"Cannot retry command in state '{command['state']}'. Only TIMEOUT or FAILED commands can be retried."
        )

    if command["retry_count"] >= command["max_retries"]:
        raise ValueError(
            f"Command has reached maximum retries ({command['retry_count']}/{command['max_retries']})"
        )

    new_retry_count = command["retry_count"] + 1
    now = datetime.now().isoformat()
    new_timeout_at = _calculate_timeout_at(now, command["timeout_seconds"])

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE commands
            SET state = 'QUEUED',
                retry_count = ?,
                sent_at = NULL,
                ack_at = NULL,
                executing_at = NULL,
                response_at = NULL,
                ack_status = NULL,
                ack_message = NULL,
                timeout_at = ?,
                completed_at = NULL,
                cancelled_at = NULL,
                error = NULL,
                updated_at = ?
            WHERE command_id = ?
        """, (new_retry_count, new_timeout_at, now, command_id))
        connection.commit()
    finally:
        connection.close()

    record_command_event(
        command_id=command_id,
        node_id=command["node_id"],
        event_type="COMMAND_RETRY",
        state="QUEUED",
        details={"retry_count": new_retry_count, "max_retries": command["max_retries"]}
    )

    return get_command(command_id)
