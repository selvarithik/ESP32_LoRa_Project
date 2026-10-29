"""Configuration for the existing sensor_parameters model; no parallel registry."""
import json
import math
import re
from flask import Blueprint, jsonify, request, session
from database import get_connection
import account_settings
CATALOG = [
  {
    "parameter_type": "Temperature",
    "parameter_id": "TEMP_001",
    "unit": "°C",
    "color": "#2563EB",
    "icon": "thermometer",
    "category": "core",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Pressure",
    "parameter_id": "PRESS_001",
    "unit": "hPa",
    "color": "#0D9488",
    "icon": "gauge",
    "category": "core",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Battery Voltage",
    "parameter_id": "BATT_V_001",
    "unit": "V",
    "color": "#16A34A",
    "icon": "battery",
    "category": "core",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "RSSI",
    "parameter_id": "RSSI_001",
    "unit": "dBm",
    "color": "#7C3AED",
    "icon": "signal",
    "category": "core",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Battery Level",
    "parameter_id": "BATT_PCT_001",
    "unit": "%",
    "color": "#D97706",
    "icon": "battery",
    "category": "core",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Power Consumption",
    "parameter_id": "POWER_001",
    "unit": "W",
    "color": "#EA580C",
    "icon": "zap",
    "category": "core",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "SNR",
    "parameter_id": "SNR_001",
    "unit": "dB",
    "color": "#0891B2",
    "icon": "signal",
    "category": "core",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Humidity",
    "parameter_id": "HUM_001",
    "unit": "%RH",
    "color": "#0284C7",
    "icon": "droplet",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Light Intensity",
    "parameter_id": "LIGHT_001",
    "unit": "lux",
    "color": "#CA8A04",
    "icon": "sun",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Air Quality",
    "parameter_id": "AQI_001",
    "unit": "AQI",
    "color": "#059669",
    "icon": "wind",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "CO2 Level",
    "parameter_id": "CO2_001",
    "unit": "ppm",
    "color": "#64748B",
    "icon": "wind",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Gas Concentration",
    "parameter_id": "GAS_001",
    "unit": "ppm",
    "color": "#DC2626",
    "icon": "wind",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Vibration",
    "parameter_id": "VIB_001",
    "unit": "mm/s",
    "color": "#9333EA",
    "icon": "activity",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Sound Level",
    "parameter_id": "SOUND_001",
    "unit": "dB(A)",
    "color": "#4F46E5",
    "icon": "activity",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Water Level",
    "parameter_id": "WATER_LEVEL_001",
    "unit": "cm",
    "color": "#0284C7",
    "icon": "droplet",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Flow Rate",
    "parameter_id": "FLOW_001",
    "unit": "L/min",
    "color": "#0D9488",
    "icon": "gauge",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Distance",
    "parameter_id": "DIST_001",
    "unit": "cm",
    "color": "#475569",
    "icon": "gauge",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Motion Detection",
    "parameter_id": "MOTION_001",
    "unit": "",
    "color": "#7C3AED",
    "icon": "activity",
    "category": "environment",
    "data_type": "TEXT",
    "widget_type": "state"
  },
  {
    "parameter_type": "GPS Location",
    "parameter_id": "GPS_001",
    "unit": "",
    "color": "#DB2777",
    "icon": "map-pin",
    "category": "environment",
    "data_type": "TEXT",
    "widget_type": "gps"
  },
  {
    "parameter_type": "Device Uptime",
    "parameter_id": "UPTIME_001",
    "unit": "s",
    "color": "#2563EB",
    "icon": "clock",
    "category": "environment",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "LoRa Link Quality",
    "parameter_id": "LORA_LINK_001",
    "unit": "%",
    "color": "#2563EB",
    "icon": "signal",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Connected Nodes",
    "parameter_id": "NODES_ONLINE",
    "unit": "count",
    "color": "#0D9488",
    "icon": "network",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Packets Received",
    "parameter_id": "PKT_RX_001",
    "unit": "packets",
    "color": "#16A34A",
    "icon": "network",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Packet Loss Rate",
    "parameter_id": "PKT_LOSS_001",
    "unit": "%",
    "color": "#DC2626",
    "icon": "network",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "LoRa Round-Trip Time",
    "parameter_id": "LORA_RTT_001",
    "unit": "ms",
    "color": "#7C3AED",
    "icon": "clock",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Gateway CPU Usage",
    "parameter_id": "GW_CPU_001",
    "unit": "%",
    "color": "#0891B2",
    "icon": "cpu",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Free Memory",
    "parameter_id": "GW_MEM_FREE",
    "unit": "bytes",
    "color": "#D97706",
    "icon": "cpu",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "MQTT Connection",
    "parameter_id": "MQTT_STATUS",
    "unit": "",
    "color": "#0284C7",
    "icon": "network",
    "category": "network",
    "data_type": "TEXT",
    "widget_type": "state"
  },
  {
    "parameter_type": "Data Update Interval",
    "parameter_id": "DATA_INTERVAL_001",
    "unit": "s",
    "color": "#EA580C",
    "icon": "clock",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  },
  {
    "parameter_type": "Active Alarms",
    "parameter_id": "GW_ALARMS",
    "unit": "count",
    "color": "#DC2626",
    "icon": "activity",
    "category": "network",
    "data_type": "FLOAT",
    "widget_type": "numeric"
  }
]
bp = Blueprint("sensor_widgets", __name__)
ICONS = {"thermometer","gauge","battery","signal","zap","droplet","sun","wind","activity","map-pin","clock","network","cpu","fan","flame","cloud-rain","magnet","door","weight","ruler","volume","compass","beaker"}
ICON_COLORS = {'fan': '#0D9488', 'flame': '#DC2626', 'cloud-rain': '#0284C7', 'magnet': '#7C3AED', 'door': '#B45309', 'weight': '#475569', 'ruler': '#2563EB', 'volume': '#BE185D', 'compass': '#4F46E5', 'beaker': '#15803D'}

def migrate():
    db = get_connection()
    try:
        columns = {row["name"] for row in db.execute("PRAGMA table_info(sensor_parameters)")}
        if "widget_config" not in columns:
            db.execute("ALTER TABLE sensor_parameters ADD COLUMN widget_config TEXT NOT NULL DEFAULT '{}'")
        db.execute("CREATE TABLE IF NOT EXISTS feature_migrations (name TEXT PRIMARY KEY)")
        if not db.execute("SELECT 1 FROM feature_migrations WHERE name='sensor-widgets-v1'").fetchone():
            db.execute("UPDATE sensor_parameters SET display_enabled=CASE WHEN lower(parameter_type) IN ('temperature','pressure','battery voltage','rssi') OR upper(parameter_id) IN ('TEMP_001','PRESS_001','BATT_V_001','RSSI_001') THEN 1 ELSE 0 END WHERE widget_config='{}'")
            db.execute("INSERT INTO feature_migrations(name) VALUES('sensor-widgets-v1')")
        db.commit()
    finally:
        db.close()

def decode(value):
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value or "{}")
    except (ValueError, TypeError):
        return {}

def template(parameter):
    text = " ".join(str(parameter.get(k) or "") for k in ("parameter_type","parameter_name","parameter_id")).lower()
    return next((p for p in CATALOG if p["parameter_type"].lower() == str(parameter.get("parameter_type","")).lower()), None) or next((p for p in CATALOG if p["parameter_id"].lower() in text), CATALOG[0])

def config(parameter):
    preset = template(parameter)
    saved = decode(parameter.get("widget_config"))
    direct = parameter.get("parameter_id", "")
    icon_color=ICON_COLORS.get(saved.get("icon"),preset["color"])
    return dict(category=preset["category"], icon=preset["icon"], color=icon_color, widget_type="numeric" if parameter.get("data_type") in ("FLOAT","DOUBLE","INT","UINT","UINT32") else preset["widget_type"] if preset["widget_type"] != "numeric" else "state",
                source="node_telemetry", source_field=direct, scale=1, offset=0, stale_timeout=10, reporting_interval=2,
                position=parameter.get("id", 0), **{}) | saved

def validate(payload, current=None):
    merged = dict(current or {}) | payload
    for key in ("parameter_name","parameter_type","unit","description","sensor_id"):
        if key in merged and merged[key] is not None and (not isinstance(merged[key], str) or len(merged[key]) > (500 if key == "description" else 100)):
            raise ValueError(f"Invalid {key}")
    pid = merged.get("parameter_id", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", pid):
        raise ValueError("Parameter ID must use letters, numbers, dots, underscores or hyphens.")
    if not str(merged.get("parameter_name", "")).strip():
        raise ValueError("Sensor name is required.")
    if merged.get("data_type") not in ("FLOAT","DOUBLE","INT","UINT","UINT32","TEXT","ENUM","BOOL"):
        raise ValueError("Unsupported data type.")
    for flag in ("enabled","display_enabled","graph_enabled","alarm_enabled"):
        if flag in payload and not isinstance(payload[flag], bool):
            raise ValueError(f"{flag} must be true or false.")
    for key in ("min_value","max_value","low_alarm","high_alarm"):
        v = merged.get(key)
        if v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)):
            raise ValueError(f"{key} must be a finite number.")
    for lower, upper in (("min_value","max_value"),("low_alarm","high_alarm")):
        if merged.get(lower) is not None and merged.get(upper) is not None and merged[lower] > merged[upper]:
            raise ValueError(f"{lower} must not exceed {upper}.")
    precision = merged.get("decimal_places",2)
    if type(precision) is not int or not 0 <= precision <= 8:
        raise ValueError("Precision must be between 0 and 8.")
    cfg = config(merged)
    if cfg.get("source") != "node_telemetry":
        raise ValueError("Only the existing normalized node telemetry source is available. Configure transport in Nodes.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", str(cfg.get("source_field",""))):
        raise ValueError("A valid telemetry payload field is required.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(cfg.get("color",""))):
        raise ValueError("Invalid widget color.")
    if cfg.get("icon") not in ICONS or cfg.get("widget_type") not in ("numeric","state","gps"):
        raise ValueError("Invalid icon or widget type.")
    if not isinstance(cfg.get("category"),str) or not 1 <= len(cfg["category"]) <= 64:
        raise ValueError("Category must contain 1-64 characters.")
    if cfg["widget_type"] == "numeric" and merged.get("data_type") not in ("FLOAT","DOUBLE","INT","UINT","UINT32"):
        raise ValueError("Numeric widgets require a numeric data type.")
    if cfg["widget_type"] in ("state","gps") and merged.get("data_type") in ("FLOAT","DOUBLE","INT","UINT","UINT32"):
        raise ValueError("State and GPS widgets require a text or state data type.")
    allowed = {"category","icon","color","widget_type","source","source_field","scale","offset","stale_timeout","reporting_interval","position","warning_low","warning_high"}
    if set(decode(merged.get("widget_config"))) - allowed:
        raise ValueError("Unknown widget configuration field.")
    for key, low, high in (("scale",-1e9,1e9),("offset",-1e12,1e12),("stale_timeout",1,604800),("reporting_interval",1,86400),("position",0,1000000)):
        value = cfg.get(key)
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Invalid {key}.")
    for key in ("warning_low","warning_high"):
        if cfg.get(key) is not None and (type(cfg[key]) not in (float,int) or not math.isfinite(cfg[key])):
            raise ValueError("Warning thresholds must be finite numbers.")
    if cfg.get("warning_low") is not None and cfg.get("warning_high") is not None and cfg["warning_low"] > cfg["warning_high"]:
        raise ValueError("Warning minimum exceeds maximum.")
    return json.dumps(cfg)

@bp.get("/api/sensor-catalog")
def catalog():
    return jsonify(templates=CATALOG, sources=[{"id":"node_telemetry","name":"Existing node telemetry (HTTP / LoRa / configured gateway adapter)"}],
                   unavailable_sources=["Direct MQTT subscriptions","Direct Modbus polling","Direct gateway diagnostic metrics"],
                   explanation="Templates describe possible metrics. A template is not a configured or connected sensor.")

@bp.before_app_request
def protect_sensor_changes():
    if request.endpoint not in ("api_add_parameter","api_update_parameter","api_delete_parameter","api_enable_parameter","api_save_graph"):
        return
    if request.method == "GET":
        return
    db = account_settings.connect()
    try:
        actor = account_settings.current(db)
        if not actor:
            return jsonify(success=False,error="Sign in through Account Settings to change sensor configuration."),401
        if actor["role"] not in ("administrator","creator"):
            return jsonify(success=False,error="Administrator or creator access is required."),403
        import secrets
        if not secrets.compare_digest(request.headers.get("X-CSRF-Token",""),session.get("account_csrf",secrets.token_hex(32))):
            return jsonify(success=False,error="Reload Sensor Management and try again."),403
    finally:
        db.close()
    if request.endpoint in ("api_add_parameter","api_update_parameter"):
        try:
            import sensor_manager
            body = request.get_json(silent=True)
            if not isinstance(body,dict):
                raise ValueError("JSON object required.")
            old = sensor_manager.get_parameter(request.view_args["node_id"],request.view_args.get("parameter_id",""))
            if request.endpoint == "api_update_parameter" and old is None:
                return jsonify(success=False,error="Sensor not found."),404
            if old and "parameter_id" in body and body["parameter_id"] != old["parameter_id"]:
                raise ValueError("Parameter IDs cannot be renamed because they identify stored history.")
            sensor_id = body.get("sensor_id",old.get("sensor_id") if old else None)
            if sensor_id:
                db=get_connection()
                try:
                    conflict=db.execute("SELECT 1 FROM sensor_parameters WHERE node_id=? AND sensor_id=? AND parameter_id!=?",
                        (request.view_args["node_id"],sensor_id,old["parameter_id"] if old else body.get("parameter_id",""))).fetchone()
                    if conflict:
                        raise ValueError("Sensor identifier already exists on this node.")
                finally:
                    db.close()
            cfg = validate(body,old)
            request.sensor_widget_config = cfg
            body["widget_config"] = cfg
        except (ValueError,TypeError) as error:
            return jsonify(success=False,error=str(error)),400
    if request.endpoint == "api_delete_parameter":
        db = get_connection()
        try:
            count = db.execute("SELECT COUNT(*) FROM telemetry_values WHERE node_id=? AND parameter_id=?", (request.view_args["node_id"],request.view_args["parameter_id"])).fetchone()[0]
            if count:
                return jsonify(success=False,error="Historical readings exist. Disable this sensor and remove its widget to retain history."),409
        finally:
            db.close()


    if request.endpoint == "api_enable_parameter":
        body=request.get_json(silent=True)
        if not isinstance(body,dict) or not isinstance(body.get("enabled"),bool):
            return jsonify(success=False,error="enabled must be true or false."),400
