"""Persistent node settings used by the System page and configuration API."""
import copy
import json
from datetime import datetime

from database import get_connection
from node_manager import get_node

DEFAULT_CONFIG = {
    "time": {"timezone": "Asia/Kolkata", "sync_enabled": True},
    "watchdog": {"enabled": True, "timeout_s": 60},
}


def _merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_node_config(node_id):
    if get_node(node_id) is None:
        return None
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT config_json FROM node_configs WHERE node_id = ?", (node_id,)
        ).fetchone()
        return json.loads(row["config_json"]) if row else {}
    finally:
        connection.close()


def get_node_config_with_defaults(node_id):
    config = load_node_config(node_id)
    return None if config is None else _merge(DEFAULT_CONFIG, config)


def save_node_config(node_id, config):
    if get_node(node_id) is None:
        return False
    if not isinstance(config, dict):
        raise ValueError("config must be an object")
    merged = _merge(get_node_config_with_defaults(node_id), config)
    for section in ("time", "watchdog"):
        if not isinstance(merged.get(section), dict):
            raise ValueError(f"{section} must be an object")
    timeout = merged["watchdog"].get("timeout_s", 60)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 1 <= timeout <= 86400:
        raise ValueError("Watchdog timeout must be between 1 and 86400 seconds")
    for section, key in (("time", "sync_enabled"), ("watchdog", "enabled")):
        if not isinstance(merged[section].get(key), bool):
            raise ValueError(f"{key} must be a boolean")
    timezone = merged["time"].get("timezone")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("Timezone is required")
    connection = get_connection()
    try:
        connection.execute(
            """INSERT INTO node_configs(node_id, config_json, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(node_id) DO UPDATE SET
               config_json = excluded.config_json, updated_at = excluded.updated_at""",
            (node_id, json.dumps(merged), datetime.now().isoformat()),
        )
        connection.commit()
        return True
    finally:
        connection.close()


def reset_node_config(node_id):
    if get_node(node_id) is None:
        return False
    connection = get_connection()
    try:
        connection.execute("DELETE FROM node_configs WHERE node_id = ?", (node_id,))
        connection.commit()
    finally:
        connection.close()
    return save_node_config(node_id, DEFAULT_CONFIG)
