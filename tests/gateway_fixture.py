"""Isolated sample gateway. Never uses the real data directory."""
import sys
import tempfile
import os
import atexit
import gc
import sqlite3
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
TEMP = tempfile.TemporaryDirectory(prefix="gateway-ui-test-")
import database
import account_settings
account_settings.DB = Path(TEMP.name) / "data" / "accounts.sqlite3"

database.BASE_DIR = Path(TEMP.name)
database.DATA_DIR = Path(TEMP.name) / "data"
database.DATABASE = database.DATA_DIR / "gateway.db"
import server
server.app.config["TEMPLATES_AUTO_RELOAD"] = True

def cleanup_fixture():
    # sqlite3 context managers commit but do not close connections. Release only
    # this isolated fixture's handles before Windows removes its temporary files.
    import local_ip, mqtt_api
    local_ip.service.stop()
    if mqtt_api._service:mqtt_api._service.stop()
    gc.collect()
    for obj in gc.get_objects():
        if not isinstance(obj,sqlite3.Connection):continue
        try:
            paths=[row[2] for row in obj.execute('PRAGMA database_list')]
            if any(path and Path(path).resolve().is_relative_to(Path(TEMP.name).resolve()) for path in paths):obj.close()
        except sqlite3.ProgrammingError:pass
    TEMP.cleanup()

atexit.register(cleanup_fixture)


def seed():
    # Each suite starts from an independent logical fixture, even in one discovery process.
    assert Path(database.DATABASE).resolve().is_relative_to(Path(TEMP.name).resolve())
    fixture_db = database.get_connection()
    try:
        for row in fixture_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
            fixture_db.execute('DELETE FROM "' + row[0].replace('"', '""') + '"')
        fixture_db.commit()
    finally:
        fixture_db.close()
    import mqtt_api
    import local_ip
    local_ip.service.stop()
    local_ip.service.migrate()
    if mqtt_api._service:
        mqtt_api._service.stop()
        mqtt_api._service=None
    server.nodes.clear()
    client = server.app.test_client()
    with patch.dict(os.environ, {"GATEWAY_ADMIN_PASSWORD": "fixture-only-admin-123"}):
        auth_db = account_settings.connect()
    actor = auth_db.execute("SELECT * FROM accounts LIMIT 1").fetchone()
    auth_db.close()
    with client.session_transaction() as session:
        account_settings.establish(actor,session)
        session['account_csrf']='fixture-csrf'
    client.environ_base["HTTP_X_CSRF_TOKEN"] = "fixture-csrf"
    for index in range(1, 4):
        node_id = f"TEST_{index:03}"
        response = client.post("/api/nodes", json={
            "node_id": node_id, "name": f"Workshop {index}", "node_address": str(index),
            "mcu_family": "ESP32", "mcu_model": "ESP32-S3", "firmware_version": "1.0.0",
            "communication_type": "LoRa", "enabled": True,
        })
        assert response.status_code == 200, response.json
        for pid, name, unit, value in [
            ("temperature", "Temperature", "C", 26.4), ("humidity", "Humidity", "%", 62),
            ("battery", "Battery", "%", 84), ("rssi", "Signal", "dBm", -89),
        ]:
            response = client.post(f"/api/nodes/{node_id}/parameters", json={
                "parameter_id": pid, "parameter_name": name, "parameter_type": pid.upper(),
                "data_type": "FLOAT", "unit": unit, "graph_enabled": pid == "temperature",
                "enabled": True, "sensor_id": f"{node_id}-{pid}",
            })
            assert response.status_code == 200, response.json
            response = client.post("/api/telemetry", json={"node_id": node_id, "parameters": {pid: value}})
            assert response.status_code == 200, response.json
    return client


if __name__ == "__main__":
    seed()
    server.socketio.run(server.app, host="127.0.0.1", port=int(os.environ.get('GATEWAY_TEST_PORT','5057')), debug=False, allow_unsafe_werkzeug=True)
