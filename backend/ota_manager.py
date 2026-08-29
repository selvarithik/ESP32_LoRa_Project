import json
import uuid
from datetime import datetime
import firmware_manager
from database import get_connection


OTA_STATES = (
    "IDLE",
    "CHECKING",
    "UPDATE_AVAILABLE",
    "APPROVED",
    "DOWNLOADING",
    "VERIFYING",
    "READY_TO_BOOT",
    "REBOOTING",
    "VALIDATING",
    "SUCCESS",
    "FAILED",
    "ROLLBACK",
    "CANCELLED"
)

TERMINAL_STATES = (
    "SUCCESS",
    "FAILED",
    "ROLLBACK",
    "CANCELLED"
)

ALLOWED_JOB_TRANSITIONS = {
    "IDLE": ("CHECKING", "UPDATE_AVAILABLE"),
    "CHECKING": ("IDLE", "UPDATE_AVAILABLE", "FAILED"),
    "UPDATE_AVAILABLE": ("APPROVED", "CANCELLED", "FAILED"),
    "APPROVED": ("DOWNLOADING", "CANCELLED", "FAILED"),
    "DOWNLOADING": ("VERIFYING", "FAILED", "CANCELLED"),
    "VERIFYING": ("READY_TO_BOOT", "FAILED", "CANCELLED"),
    "READY_TO_BOOT": ("REBOOTING", "FAILED", "CANCELLED"),
    "REBOOTING": ("VALIDATING", "FAILED", "ROLLBACK"),
    "VALIDATING": ("SUCCESS", "FAILED", "ROLLBACK"),
    "SUCCESS": (),
    "FAILED": ("ROLLBACK",),
    "ROLLBACK": (),
    "CANCELLED": ()
}

DEFAULT_OTA_CONFIG = {
    "ota_enabled": True,
    "update_channel": "stable",
    "automatic_updates": False,
    "check_interval_hours": 6,
    "manual_approval": True,
    "rollback_enabled": True,
    "allow_downgrade": False,
    "require_https": True
}

OTA_CONFIG_PATH = firmware_manager.FIRMWARE_DIR / "ota_config.json"


def get_ota_config():
    firmware_manager.ensure_storage()
    if not OTA_CONFIG_PATH.exists():
        save_ota_config(DEFAULT_OTA_CONFIG)
    try:
        data = json.loads(OTA_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    config = dict(DEFAULT_OTA_CONFIG)
    config.update(data if isinstance(data, dict) else {})
    return config


def save_ota_config(payload):
    if not isinstance(payload, dict):
        raise ValueError("OTA configuration must be an object")

    config = dict(DEFAULT_OTA_CONFIG)
    config.update(payload)

    config["ota_enabled"] = bool(config["ota_enabled"])
    config["automatic_updates"] = bool(config["automatic_updates"])
    config["manual_approval"] = bool(config["manual_approval"])
    config["rollback_enabled"] = bool(config["rollback_enabled"])
    config["allow_downgrade"] = bool(config["allow_downgrade"])
    config["require_https"] = bool(config["require_https"])
    config["update_channel"] = str(config["update_channel"] or "stable").lower()
    if config["update_channel"] not in firmware_manager.CHANNELS:
        raise ValueError("update_channel must be stable, beta, or dev")

    config["check_interval_hours"] = int(config["check_interval_hours"])
    if not 1 <= config["check_interval_hours"] <= 168:
        raise ValueError("check_interval_hours must be between 1 and 168")

    firmware_manager.ensure_storage()
    temp_path = OTA_CONFIG_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    temp_path.replace(OTA_CONFIG_PATH)
    return config


def make_job_id():
    return f"OTA-{uuid.uuid4().hex[:12].upper()}"


def make_event_id():
    return f"FW-EVT-{uuid.uuid4().hex[:12].upper()}"


def normalize_device(row):
    device = dict(row)
    device["current_build"] = int(
        device.get("current_build") or 0
    )
    device["target_build"] = (
        int(device["target_build"])
        if device.get("target_build") is not None
        else None
    )
    device["failure_count"] = int(
        device.get("failure_count") or 0
    )
    return device


def normalize_job(row):
    job = dict(row)
    job["from_build"] = (
        int(job["from_build"])
        if job.get("from_build") is not None
        else None
    )
    job["target_build"] = int(
        job.get("target_build") or 0
    )
    job["progress"] = int(
        job.get("progress") or 0
    )
    job["authorized"] = bool(
        job.get("authorized")
    )
    return job


def normalize_event(row):
    event = dict(row)
    event["progress"] = (
        int(event["progress"])
        if event.get("progress") is not None
        else None
    )
    return event


def record_event(
    job_id=None,
    node_id=None,
    release_id=None,
    event_type="INFO",
    state=None,
    progress=None,
    message="",
    error=None
):
    connection = get_connection()
    cursor = connection.cursor()
    now = datetime.now().isoformat()
    event_id = make_event_id()

    cursor.execute("""
        INSERT INTO firmware_update_events (
            event_id,
            job_id,
            node_id,
            release_id,
            event_type,
            state,
            progress,
            message,
            error,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        job_id,
        node_id,
        release_id,
        event_type,
        state,
        progress,
        message,
        error,
        now
    ))

    connection.commit()
    connection.close()

    return event_id


def upsert_device_state(
    node_id,
    hardware_family,
    hardware_model,
    hardware_revision,
    current_version,
    current_build=0,
    channel="stable",
    ota_state="IDLE",
    target_release=None
):
    node_id = firmware_manager.validate_safe_id(
        node_id,
        "node_id"
    )

    if ota_state not in OTA_STATES:
        raise ValueError(
            "Invalid OTA state"
        )

    now = datetime.now().isoformat()
    target_release_id = None
    target_version = None
    target_build = None

    if target_release:
        target_release_id = target_release["release_id"]
        target_version = target_release["version"]
        target_build = target_release["build"]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO device_firmware (
            node_id,
            hardware_family,
            hardware_model,
            hardware_revision,
            current_version,
            current_build,
            target_release_id,
            target_version,
            target_build,
            ota_state,
            channel,
            last_check_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            hardware_family = excluded.hardware_family,
            hardware_model = excluded.hardware_model,
            hardware_revision = excluded.hardware_revision,
            current_version = excluded.current_version,
            current_build = excluded.current_build,
            target_release_id = excluded.target_release_id,
            target_version = excluded.target_version,
            target_build = excluded.target_build,
            ota_state = excluded.ota_state,
            channel = excluded.channel,
            last_check_at = excluded.last_check_at,
            updated_at = excluded.updated_at
    """, (
        node_id,
        hardware_family,
        hardware_model,
        hardware_revision,
        current_version,
        int(current_build or 0),
        target_release_id,
        target_version,
        target_build,
        ota_state,
        channel or "stable",
        now,
        now
    ))

    connection.commit()
    connection.close()

    return get_device_state(
        node_id
    )


def get_device_state(node_id):
    node_id = firmware_manager.validate_safe_id(
        node_id,
        "node_id"
    )
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM device_firmware
        WHERE node_id = ?
    """, (
        node_id,
    ))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return normalize_device(row)


def list_device_states():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM device_firmware
        ORDER BY node_id
    """)

    rows = cursor.fetchall()
    connection.close()

    return [
        normalize_device(row)
        for row in rows
    ]


def check_for_update(payload):
    required = (
        "node_id",
        "hardware_family",
        "hardware_model",
        "hardware_revision",
        "firmware_version"
    )

    for field in required:
        if not str(payload.get(field, "")).strip():
            raise ValueError(
                f"{field} is required"
            )

    protocol_version = int(
        payload.get("ota_protocol_version") or 1
    )

    if protocol_version < 1:
        raise ValueError(
            "Unsupported OTA protocol version"
        )

    node_id = firmware_manager.validate_safe_id(
        payload["node_id"],
        "node_id"
    )
    config = get_ota_config()

    if not config["ota_enabled"]:
        raise ValueError("OTA updates are disabled by server policy")

    current_build = int(
        payload.get("build") or 0
    )
    channel = str(
        payload.get("channel") or config["update_channel"]
    ).lower()

    if channel not in firmware_manager.CHANNELS:
        raise ValueError("Unsupported firmware channel")

    upsert_device_state(
        node_id=node_id,
        hardware_family=payload["hardware_family"],
        hardware_model=payload["hardware_model"],
        hardware_revision=payload["hardware_revision"],
        current_version=payload["firmware_version"],
        current_build=current_build,
        channel=channel,
        ota_state="CHECKING"
    )

    release = firmware_manager.find_update(
        hardware_family=payload["hardware_family"],
        hardware_model=payload["hardware_model"],
        hardware_revision=payload["hardware_revision"],
        firmware_version=payload["firmware_version"],
        build=current_build,
        channel=channel,
        allow_downgrade=(
            bool(payload.get("allow_downgrade", False))
            and bool(config["allow_downgrade"])
        )
    )

    state = (
        "UPDATE_AVAILABLE"
        if release
        else "IDLE"
    )

    device = upsert_device_state(
        node_id=node_id,
        hardware_family=payload["hardware_family"],
        hardware_model=payload["hardware_model"],
        hardware_revision=payload["hardware_revision"],
        current_version=payload["firmware_version"],
        current_build=current_build,
        channel=channel,
        ota_state=state,
        target_release=release
    )

    record_event(
        node_id=node_id,
        release_id=release["release_id"] if release else None,
        event_type="CHECK",
        state=state,
        message=(
            "Update available"
            if release
            else "No update available"
        )
    )

    return {
        "device": device,
        "release": release
    }


def create_update_job(node_id, release_id, authorized=True):
    node_id = firmware_manager.validate_safe_id(
        node_id,
        "node_id"
    )
    release = firmware_manager.get_release(
        release_id
    )

    if release is None:
        raise ValueError(
            "Release not found"
        )

    if release["status"] != "ACTIVE":
        raise ValueError(
            "Only ACTIVE releases can be used for OTA jobs"
        )

    device = get_device_state(
        node_id
    )

    if device is None:
        raise ValueError(
            "Device firmware state is unknown"
        )

    if not firmware_manager.is_hardware_compatible(
        release,
        device
    ):
        raise ValueError(
            "Release is not compatible with device hardware"
        )

    now = datetime.now().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT job_id, state
        FROM firmware_update_jobs
        WHERE node_id = ?
          AND state NOT IN ('SUCCESS', 'FAILED', 'ROLLBACK', 'CANCELLED')
        ORDER BY created_at DESC
        LIMIT 1
    """, (node_id,))
    existing_job = cursor.fetchone()
    if existing_job is not None:
        connection.close()
        raise ValueError(
            f"Device already has active OTA job {existing_job['job_id']} ({existing_job['state']})"
        )

    job_id = make_job_id()

    cursor.execute("""
        INSERT INTO firmware_update_jobs (
            job_id,
            node_id,
            release_id,
            from_version,
            from_build,
            target_version,
            target_build,
            state,
            progress,
            authorized,
            started_at,
            completed_at,
            result,
            error,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        node_id,
        release["release_id"],
        device.get("current_version"),
        device.get("current_build"),
        release["version"],
        release["build"],
        "APPROVED" if authorized else "UPDATE_AVAILABLE",
        0,
        1 if authorized else 0,
        now if authorized else None,
        None,
        None,
        None,
        now,
        now
    ))

    cursor.execute("""
        UPDATE device_firmware
        SET
            target_release_id = ?,
            target_version = ?,
            target_build = ?,
            ota_state = ?,
            last_update_at = ?,
            updated_at = ?
        WHERE node_id = ?
    """, (
        release["release_id"],
        release["version"],
        release["build"],
        "APPROVED" if authorized else "UPDATE_AVAILABLE",
        now,
        now,
        node_id
    ))

    connection.commit()
    connection.close()

    record_event(
        job_id=job_id,
        node_id=node_id,
        release_id=release["release_id"],
        event_type="JOB_CREATED",
        state="APPROVED" if authorized else "UPDATE_AVAILABLE",
        progress=0,
        message="OTA update job created"
    )

    return get_job(
        job_id
    )


def update_job_state(
    job_id,
    state,
    progress=None,
    result=None,
    error=None
):
    job_id = firmware_manager.validate_safe_id(
        job_id,
        "job_id"
    )
    state = str(state or "").upper()

    if state not in OTA_STATES:
        raise ValueError(
            "Invalid OTA state"
        )

    job = get_job(job_id)

    if job is None:
        return None

    old_state = str(job.get("state") or "IDLE").upper()

    if state != old_state and state not in ALLOWED_JOB_TRANSITIONS.get(old_state, ()):
        raise ValueError(
            f"Cannot move OTA job from {old_state} to {state}"
        )

    if progress is None:
        progress = 100 if state == "SUCCESS" else int(job.get("progress") or 0)

    progress = max(
        0,
        min(100, int(progress))
    )

    now = datetime.now().isoformat()
    started_at = job.get("started_at")
    if started_at is None and state in (
        "APPROVED",
        "DOWNLOADING",
        "VERIFYING",
        "READY_TO_BOOT",
        "REBOOTING",
        "VALIDATING"
    ):
        started_at = now

    completed_at = (
        now
        if state in TERMINAL_STATES
        else job.get("completed_at")
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE firmware_update_jobs
        SET
            state = ?,
            progress = ?,
            started_at = ?,
            completed_at = ?,
            result = ?,
            error = ?,
            updated_at = ?
        WHERE job_id = ?
    """, (
        state,
        progress,
        started_at,
        completed_at,
        result,
        error,
        now,
        job_id
    ))

    if state == "SUCCESS":
        cursor.execute("""
            UPDATE device_firmware
            SET
                current_version = ?,
                current_build = ?,
                target_release_id = NULL,
                target_version = NULL,
                target_build = NULL,
                ota_state = 'SUCCESS',
                last_error = NULL,
                last_update_at = ?,
                updated_at = ?
            WHERE node_id = ?
        """, (
            job["target_version"],
            job["target_build"],
            now,
            now,
            job["node_id"]
        ))

    elif state == "ROLLBACK":
        cursor.execute("""
            UPDATE device_firmware
            SET
                ota_state = 'ROLLBACK',
                target_release_id = NULL,
                target_version = NULL,
                target_build = NULL,
                rollback_release_id = ?,
                last_error = ?,
                last_update_at = ?,
                updated_at = ?
            WHERE node_id = ?
        """, (
            job["release_id"],
            error,
            now,
            now,
            job["node_id"]
        ))

    elif state in ("FAILED", "CANCELLED"):
        cursor.execute("""
            UPDATE device_firmware
            SET
                ota_state = ?,
                target_release_id = CASE WHEN ? = 'FAILED' THEN target_release_id ELSE NULL END,
                target_version = CASE WHEN ? = 'FAILED' THEN target_version ELSE NULL END,
                target_build = CASE WHEN ? = 'FAILED' THEN target_build ELSE NULL END,
                failure_count = CASE
                    WHEN ? = 'FAILED' THEN failure_count + 1
                    ELSE failure_count
                END,
                last_error = ?,
                last_update_at = ?,
                updated_at = ?
            WHERE node_id = ?
        """, (
            state,
            state,
            state,
            state,
            state,
            error,
            now,
            now,
            job["node_id"]
        ))

    else:
        cursor.execute("""
            UPDATE device_firmware
            SET
                ota_state = ?,
                last_error = ?,
                updated_at = ?
            WHERE node_id = ?
        """, (
            state,
            error,
            now,
            job["node_id"]
        ))

    connection.commit()
    connection.close()

    record_event(
        job_id=job_id,
        node_id=job["node_id"],
        release_id=job["release_id"],
        event_type="STATE",
        state=state,
        progress=progress,
        message=result or f"OTA state changed to {state}",
        error=error
    )

    return get_job(job_id)


def list_jobs():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM firmware_update_jobs
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    return [
        normalize_job(row)
        for row in rows
    ]


def get_job(job_id):
    job_id = firmware_manager.validate_safe_id(
        job_id,
        "job_id"
    )
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM firmware_update_jobs
        WHERE job_id = ?
    """, (
        job_id,
    ))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return normalize_job(row)


def list_events(limit=100):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM firmware_update_events
        ORDER BY created_at DESC
        LIMIT ?
    """, (
        int(limit),
    ))

    rows = cursor.fetchall()
    connection.close()

    return [
        normalize_event(row)
        for row in rows
    ]
