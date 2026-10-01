"""Authentication helpers for the SELVARITHIK'S LoRa Gateway web app.

The local gateway boots with the documented development credentials:
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
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not AUTH_FILE.exists():
        data = {
            "username": DEFAULT_USER,
            "password_hash": generate_password_hash(DEFAULT_PASSWORD),
        }
        AUTH_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        return data

    try:
        data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        if not data.get("username") or not data.get("password_hash"):
            raise ValueError("Invalid authentication settings")
        return data
    except Exception:
        # Repair a corrupted local auth file instead of making the gateway
        # impossible to enter.
        data = {
            "username": DEFAULT_USER,
            "password_hash": generate_password_hash(DEFAULT_PASSWORD),
        }
        AUTH_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        return data


def authenticate(username: str, password: str) -> bool:
    data = _read()
    return (
        username == data["username"]
        and check_password_hash(data["password_hash"], password)
    )


def get_username() -> str:
    return str(_read()["username"])


def set_credentials(username: str, password: str) -> None:
    username = (username or "").strip()
    if not username:
        raise ValueError("User ID is required")
    if len(password or "") < 4:
        raise ValueError("Password must contain at least 4 characters")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(
        json.dumps(
            {
                "username": username,
                "password_hash": generate_password_hash(password),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def is_default_credentials() -> bool:
    data = _read()
    return (
        data["username"] == "admin"
        and check_password_hash(
            data["password_hash"],
            "admin",
        )
    )
