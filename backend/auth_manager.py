"""Authentication helpers for the SELVARITHIK'S LoRa Gateway web app.

Deprecated read-only legacy helper; server sessions use account_settings.
No credential file is automatically created or repaired. Historical defaults:
    user id: admin
    password: admin

Credentials are stored as a Werkzeug password hash in data/auth.json.
Set GATEWAY_ADMIN_USER and GATEWAY_ADMIN_PASSWORD before first run if the
default credentials should be replaced for a deployment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUTH_FILE = DATA_DIR / "auth.json"

DEFAULT_USER = os.environ.get("GATEWAY_ADMIN_USER", "admin")
DEFAULT_PASSWORD = os.environ.get("GATEWAY_ADMIN_PASSWORD", "admin")


def _read() -> dict:
    # Read-only legacy migration support. Never recreate or repair credentials.
    if not AUTH_FILE.exists():
        raise RuntimeError("Legacy authentication is unavailable; use Account Settings/local recovery.")
    data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    if not data.get("username") or not data.get("password_hash"):
        raise RuntimeError("Legacy authentication data is invalid; explicit recovery required.")
    return data


def authenticate(username: str, password: str) -> bool:
    raise RuntimeError("Legacy authentication is retired; use canonical Account Settings sessions.")


def get_username() -> str:
    return str(_read()["username"])


def set_credentials(username: str, password: str) -> None:
    raise RuntimeError("Legacy credential writes are disabled; use canonical Account Settings/local recovery.")


def is_default_credentials() -> bool:
    data = _read()
    return (
        data["username"] == "admin"
        and check_password_hash(
            data["password_hash"],
            "admin",
        )
    )
