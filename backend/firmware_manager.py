import hashlib
import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from database import BASE_DIR, get_connection


FIRMWARE_DIR = BASE_DIR / "data" / "firmware"
RELEASES_DIR = FIRMWARE_DIR / "releases"
STAGING_DIR = FIRMWARE_DIR / "staging"

RELEASE_STATES = (
    "DRAFT",
    "TESTING",
    "APPROVED",
    "ACTIVE",
    "RETIRED",
    "REVOKED"
)

VALID_TRANSITIONS = {
    "DRAFT": ("TESTING", "REVOKED"),
    "TESTING": ("APPROVED", "DRAFT", "REVOKED"),
    "APPROVED": ("ACTIVE", "RETIRED", "REVOKED"),
    "ACTIVE": ("RETIRED", "REVOKED"),
    "RETIRED": ("REVOKED",),
    "REVOKED": ()
}

CHANNELS = (
    "stable",
    "beta",
    "dev"
)

MAX_FIRMWARE_SIZE = 16 * 1024 * 1024
MIN_FIRMWARE_SIZE = 1
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?$")


def ensure_storage():
    RELEASES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )
    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def make_release_id():
    return f"REL-{uuid.uuid4().hex[:12].upper()}"


def validate_safe_id(value, field_name="identifier"):
    text = str(value or "").strip()

    if not text or not SAFE_ID_PATTERN.match(text):
        raise ValueError(
            f"Invalid {field_name}"
        )

    return text


def validate_text(value, field_name, required=True, max_length=160):
    text = str(value or "").strip()

    if required and not text:
        raise ValueError(
            f"{field_name} is required"
        )

    if len(text) > max_length:
        raise ValueError(
            f"{field_name} is too long"
        )

    return text


def validate_version(version):
    text = validate_text(
        version,
        "version",
        max_length=40
    )

    if not VERSION_PATTERN.match(text):
        raise ValueError(
            "version must use semantic format like 1.2.3"
        )

    return text


def parse_version(version):
    text = str(version or "0.0.0").strip()
    core = re.split(r"[-+]", text, maxsplit=1)[0]
    parts = core.split(".")

    if len(parts) != 3:
        raise ValueError(
            "version must use semantic format like 1.2.3"
        )

    return tuple(
        int(part)
        for part in parts
    )


def compare_versions(left, right):
    left_parts = parse_version(left)
    right_parts = parse_version(right)

    if left_parts > right_parts:
        return 1

    if left_parts < right_parts:
        return -1

    return 0


def calculate_sha256(path):
    digest = hashlib.sha256()

    with open(path, "rb") as firmware_file:
        for chunk in iter(
            lambda: firmware_file.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def safe_release_dir(release_id):
    safe_id = validate_safe_id(
        release_id,
        "release_id"
    )

    base = RELEASES_DIR.resolve()
    target = (RELEASES_DIR / safe_id).resolve()

    if base not in target.parents:
        raise ValueError(
            "Invalid release path"
        )

    return target


def validate_firmware_file(path):
    resolved = Path(path).resolve()

    if not resolved.exists() or not resolved.is_file():
        raise ValueError(
            "Firmware file is missing"
        )

    size = resolved.stat().st_size

    if size < MIN_FIRMWARE_SIZE:
        raise ValueError(
            "Firmware file is empty"
        )

    if size > MAX_FIRMWARE_SIZE:
        raise ValueError(
            "Firmware file exceeds maximum allowed size"
        )

    return size


def normalize_release(row):
    release = dict(row)
    release["mandatory"] = bool(
        release.get("mandatory")
    )
    release["file_size"] = int(
        release.get("file_size") or 0
    )
    release["build"] = int(
        release.get("build") or 0
    )
    release["security_version"] = int(
        release.get("security_version") or 0
    )
    release["download_url"] = (
        f"/api/firmware/download/{release['release_id']}"
    )
    return release


def create_manifest(release):
    return {
        "release_id": release["release_id"],
        "version": release["version"],
        "build": release["build"],
        "hardware_family": release["hardware_family"],
        "hardware_model": release["hardware_model"],
        "hardware_revision": release["hardware_revision"],
        "filename": "firmware.bin",
        "file_size": release["file_size"],
        "sha256": release["sha256"],
        "signature": release.get("signature"),
        "channel": release["channel"],
        "release_notes": release.get("release_notes", ""),
        "minimum_bootloader": release.get("minimum_bootloader"),
        "security_version": release["security_version"],
        "mandatory": bool(release["mandatory"]),
        "status": release["status"],
        "created_at": release["created_at"],
        "download_url": release["download_url"]
    }


def write_manifest(release):
    release_dir = safe_release_dir(
        release["release_id"]
    )
    manifest_path = release_dir / "manifest.json"

    with open(
        manifest_path,
        "w",
        encoding="utf-8"
    ) as manifest_file:
        json.dump(
            create_manifest(release),
            manifest_file,
            indent=2
        )


def create_release(
    source_path,
    original_filename,
    version,
    build,
    hardware_family,
    hardware_model,
    hardware_revision,
    channel="stable",
    release_notes="",
    mandatory=False,
    minimum_bootloader=None,
    security_version=0,
    signature=None
):
    ensure_storage()

    version = validate_version(version)
    build = int(build)

    if build < 0:
        raise ValueError(
            "build must be zero or greater"
        )

    hardware_family = validate_text(
        hardware_family,
        "hardware_family",
        max_length=80
    )
    hardware_model = validate_text(
        hardware_model,
        "hardware_model",
        max_length=100
    )
    hardware_revision = validate_text(
        hardware_revision,
        "hardware_revision",
        max_length=80
    )
    channel = validate_text(
        channel or "stable",
        "channel",
        max_length=30
    ).lower()

    minimum_bootloader = (
        validate_version(minimum_bootloader)
        if str(minimum_bootloader or "").strip()
        else None
    )

    security_version = int(security_version or 0)
    if security_version < 0:
        raise ValueError("security_version must be zero or greater")

    if channel not in CHANNELS:
        raise ValueError(
            "channel must be stable, beta, or dev"
        )

    filename = Path(
        original_filename or "firmware.bin"
    ).name

    if not filename or filename in (".", ".."):
        raise ValueError(
            "Invalid firmware filename"
        )

    if Path(filename).suffix.lower() != ".bin":
        raise ValueError(
            "Firmware file must use a .bin extension"
        )

    file_size = validate_firmware_file(
        source_path
    )
    sha256 = calculate_sha256(
        source_path
    )
    release_id = make_release_id()
    release_dir = safe_release_dir(
        release_id
    )
    release_dir.mkdir(
        parents=True,
        exist_ok=False
    )

    firmware_path = release_dir / "firmware.bin"

    shutil.copyfile(
        source_path,
        firmware_path
    )

    now = datetime.now().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM firmware_releases
        WHERE hardware_family = ?
          AND hardware_model = ?
          AND hardware_revision = ?
          AND channel = ?
          AND version = ?
          AND build = ?
          AND release_id <> ?
        LIMIT 1
    """, (
        hardware_family,
        hardware_model,
        hardware_revision,
        channel,
        version,
        build,
        release_id
    ))
    duplicate = cursor.fetchone()
    if duplicate is not None:
        connection.close()
        shutil.rmtree(release_dir, ignore_errors=True)
        raise ValueError(
            "A firmware release with the same version/build/hardware/channel already exists"
        )

    try:
        cursor.execute("""
            INSERT INTO firmware_releases (
                release_id, version, build, hardware_family,
                hardware_model, hardware_revision, filename,
                file_size, sha256, signature, channel, release_notes,
                minimum_bootloader, security_version, mandatory,
                status, created_at, approved_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            release_id, version, build, hardware_family, hardware_model,
            hardware_revision, filename, file_size, sha256, signature,
            channel, str(release_notes or "").strip(), minimum_bootloader,
            security_version, 1 if mandatory else 0,
            "DRAFT", now, None
        ))
        connection.commit()
    except Exception:
        connection.rollback()
        shutil.rmtree(release_dir, ignore_errors=True)
        raise
    finally:
        connection.close()

    release = get_release(release_id)
    try:
        write_manifest(release)
    except Exception:
        connection = get_connection()
        try:
            connection.execute(
                "DELETE FROM firmware_releases WHERE release_id = ?",
                (release_id,)
            )
            connection.commit()
        finally:
            connection.close()
        shutil.rmtree(release_dir, ignore_errors=True)
        raise

    return release


def list_releases():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM firmware_releases
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    return [
        normalize_release(row)
        for row in rows
    ]


def get_release(release_id):
    release_id = validate_safe_id(
        release_id,
        "release_id"
    )
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM firmware_releases
        WHERE release_id = ?
    """, (
        release_id,
    ))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return normalize_release(row)


def firmware_path_for_release(release_id):
    release = get_release(
        release_id
    )

    if release is None:
        return None

    firmware_path = safe_release_dir(
        release_id
    ) / "firmware.bin"

    base = RELEASES_DIR.resolve()
    resolved = firmware_path.resolve()

    if base not in resolved.parents:
        raise ValueError(
            "Invalid firmware path"
        )

    if not resolved.exists():
        raise FileNotFoundError(
            "Firmware binary is missing"
        )

    return resolved


def update_release_status(release_id, new_status):
    release_id = validate_safe_id(
        release_id,
        "release_id"
    )
    new_status = validate_text(
        new_status,
        "status",
        max_length=20
    ).upper()

    if new_status not in RELEASE_STATES:
        raise ValueError(
            "Invalid release status"
        )

    release = get_release(
        release_id
    )

    if release is None:
        return None

    old_status = release["status"]

    if new_status != old_status and new_status not in VALID_TRANSITIONS[old_status]:
        raise ValueError(
            f"Cannot move release from {old_status} to {new_status}"
        )

    now = datetime.now().isoformat()
    approved_at = (
        now
        if new_status == "APPROVED" and not release.get("approved_at")
        else release.get("approved_at")
    )

    connection = get_connection()
    cursor = connection.cursor()

    if new_status == "ACTIVE":
        cursor.execute("""
            UPDATE firmware_releases
            SET status = 'RETIRED',
                retired_at = ?
            WHERE status = 'ACTIVE'
              AND hardware_family = ?
              AND hardware_model = ?
              AND hardware_revision = ?
              AND channel = ?
              AND release_id <> ?
        """, (
            now,
            release["hardware_family"],
            release["hardware_model"],
            release["hardware_revision"],
            release["channel"],
            release_id
        ))

    cursor.execute("""
        UPDATE firmware_releases
        SET status = ?,
            approved_at = ?,
            retired_at = CASE
                WHEN ? = 'RETIRED' THEN ?
                ELSE retired_at
            END,
            revoked_at = CASE
                WHEN ? = 'REVOKED' THEN ?
                ELSE revoked_at
            END
        WHERE release_id = ?
    """, (
        new_status,
        approved_at,
        new_status,
        now,
        new_status,
        now,
        release_id
    ))

    connection.commit()
    connection.close()

    updated = get_release(
        release_id
    )
    write_manifest(
        updated
    )

    return updated


def is_hardware_compatible(release, device):
    return (
        str(release.get("hardware_family", "")).lower()
        == str(device.get("hardware_family", "")).lower()
        and str(release.get("hardware_model", "")).lower()
        == str(device.get("hardware_model", "")).lower()
        and str(release.get("hardware_revision", "")).lower()
        == str(device.get("hardware_revision", "")).lower()
    )


def find_update(
    hardware_family,
    hardware_model,
    hardware_revision,
    firmware_version,
    build=0,
    channel="stable",
    allow_downgrade=False
):
    device = {
        "hardware_family": hardware_family,
        "hardware_model": hardware_model,
        "hardware_revision": hardware_revision
    }
    build = int(build or 0)
    channel = str(channel or "stable").lower()

    releases = [
        release
        for release in list_releases()
        if release["status"] == "ACTIVE"
        and release["channel"] == channel
        and is_hardware_compatible(release, device)
    ]

    releases.sort(
        key=lambda release: (
            release["build"],
            parse_version(release["version"])
        ),
        reverse=True
    )

    for release in releases:
        release_build = int(release["build"] or 0)
        version_comparison = compare_versions(
            release["version"],
            firmware_version
        )

        newer = (
            release_build > build
            or (release_build == build and version_comparison > 0)
        )

        if allow_downgrade or newer:
            return release

    return None
