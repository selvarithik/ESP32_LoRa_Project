"""Part 1 authenticated device bridge; reuses existing node/telemetry/command models."""
from __future__ import annotations
import hashlib
import json
import math
import re
import secrets
import threading
import time
import zlib
from collections import OrderedDict
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request, session
import account_settings
import command_manager
import device_identity
import database
import node_manager
import sensor_manager
import telemetry_manager
import sensor_telemetry
import device_control_contract as control
import mqtt_contract as json_contract

bp = Blueprint("device_api", __name__)
LOCK = threading.RLock()
MAX_FRAME = 4096
MAX_PAYLOAD = 2048
TYPES = {"HELLO", "HEARTBEAT", "STATUS", "TELEMETRY", "COMMAND", "ACK", "RESPONSE", "CONFIG_GET", "CONFIG_UPDATE", "EVENT", "ALARM", "DIAGNOSTIC"}
SAFE_COMMANDS = control.COMMANDS
ID = re.compile(r"^[A-Za-z0-9_.:-]{1,48}$")
_emit = lambda event, payload: None
_limits = OrderedDict()

def connect():
    return database.get_connection()

def migrate():
    db = connect()
    try:
        columns = {r[1] for r in db.execute("PRAGMA table_info(nodes)")}
        additions = {"device_role": "TEXT DEFAULT 'NODE'", "master_id": "TEXT", "configuration_revision": "INTEGER DEFAULT 0", "heartbeat_seconds": "INTEGER DEFAULT 30", "latest_status": "TEXT DEFAULT '{}'", "device_token_hash": "TEXT", "device_enrolled": "INTEGER DEFAULT 0"}
        for name, sql in additions.items():
            if name not in columns:
                db.execute(f"ALTER TABLE nodes ADD COLUMN {name} {sql}")
        db.execute("CREATE TABLE IF NOT EXISTS device_receipts(source_id TEXT NOT NULL,message_id TEXT NOT NULL,fingerprint TEXT NOT NULL,received_at TEXT NOT NULL,PRIMARY KEY(source_id,message_id))")
        db.commit()
    finally:
        db.close()

def require_admin(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        db = account_settings.connect()
        try:
            actor = account_settings.current(db)
            if not actor:
                return jsonify(error="Sign in through Account Settings."), 401
            if actor["role"] not in ("creator", "administrator"):
                return jsonify(error="Administrator required."), 403
            if request.method != "GET" and not secrets.compare_digest(request.headers.get("X-CSRF-Token", ""), session.get("account_csrf", secrets.token_hex(32))):
                return jsonify(error="Invalid CSRF token."), 403
        finally:
            db.close()
        return fn(*a, **kw)
    return wrapped

def safe_id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("Invalid device identifier")
    return value

def json_body(maximum=MAX_FRAME):
    if request.mimetype != "application/json":
        return None, (jsonify(error="application/json required"), 415)
    raw = request.get_data(cache=True)
    if len(raw) > maximum:
        return None, (jsonify(error="Payload too large"), 413)
    try:value=json_contract.loads(raw,maximum)
    except json_contract.ContractError:return None,(jsonify(error="Invalid JSON object"),400)
    if not isinstance(value, dict):
        return None, (jsonify(error="JSON object required"), 400)
    return value, None

def rate_limit(identity, maximum=240):
    now = time.monotonic()
    with LOCK:
        start, count = _limits.get(identity, (now, 0))
        if now - start > 60:
            start, count = now, 0
        _limits[identity] = (start, count + 1)
        _limits.move_to_end(identity)
        while len(_limits) > 256:
            _limits.popitem(last=False)
        return count < maximum

def authenticate_master():
    identity = request.headers.get("X-Device-ID", "")
    if not rate_limit(request.remote_addr or identity):
        return None, (jsonify(error="Rate limit"), 429)
    db = connect()
    try:
        row = db.execute("SELECT * FROM nodes WHERE node_id=? AND device_enrolled=1 AND device_role='MASTER' AND enabled=1", (identity,)).fetchone()
    finally:
        db.close()
    token = request.headers.get("Authorization", "")
    digest = hashlib.sha256(token[7:].encode()).hexdigest() if token.startswith("Bearer ") else ""
    if not row or not row["device_token_hash"] or not secrets.compare_digest(digest, row["device_token_hash"]):
        return None, (jsonify(error="Unauthorized device"), 401)
    return identity, None

def validate_packet(packet):
    if not isinstance(packet, dict) or len(json.dumps(packet, separators=(",", ":"), ensure_ascii=False).encode()) > MAX_FRAME:
        raise ValueError("Oversized or invalid packet")
    fields={"protocol_version","message_id","source","destination","origin_id","final_destination_id","next_hop","type","ttl","timestamp","sequence_number","correlation_id","payload","payload_length","payload_crc32"}
    if set(packet)!=fields:raise ValueError("Invalid packet fields")
    for field in ("message_id", "source", "destination", "origin_id", "final_destination_id", "next_hop"):
        safe_id(packet.get(field))
    if packet.get("origin_id") != packet["source"] or packet["final_destination_id"] != packet["destination"]:
        raise ValueError("Inconsistent packet identity")
    correlation = packet.get("correlation_id")
    if not isinstance(correlation, str) or (correlation and not ID.fullmatch(correlation)):
        raise ValueError("Invalid correlation ID")
    for field in ("protocol_version", "ttl", "timestamp", "sequence_number", "payload_length", "payload_crc32"):
        if type(packet.get(field)) is not int or not 0 <= packet[field] <= 0xffffffff:
            raise ValueError("Invalid integer field: " + field)
    if packet["protocol_version"] != 1 or not 1 <= packet["ttl"] <= 15 or packet.get("type") not in TYPES:
        raise ValueError("Unsupported protocol, type or TTL")
    payload = packet.get("payload")
    if not isinstance(payload, str):
        raise ValueError("Payload must be an encoded JSON object string")
    raw = payload.encode("utf-8")
    if len(raw) > MAX_PAYLOAD or len(raw) != packet["payload_length"] or zlib.crc32(raw) != packet["payload_crc32"]:
        raise ValueError("Payload size/integrity error")
    body = json.loads(payload, parse_constant=lambda v: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    if not isinstance(body, dict):
        raise ValueError("Payload object required")
    return body

def packet(kind, source, destination, body, message_id=None, correlation_id=""):
    payload = json.dumps(body, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    raw = payload.encode()
    return dict(protocol_version=1, message_id=message_id or "MSG-" + secrets.token_hex(12), source=source, destination=destination, origin_id=source, final_destination_id=destination, next_hop=destination, type=kind, ttl=5, timestamp=int(time.time()), sequence_number=0, correlation_id=correlation_id, payload=payload, payload_length=len(raw), payload_crc32=zlib.crc32(raw))

def public_node(row):
    data = dict(row)
    data.pop("device_token_hash", None)
    try:data["hardware_mac"]=device_identity.hardware_mac(data["node_id"])
    except ValueError:data["hardware_mac"]=None
    data["latest_status"] = json.loads(data.get("latest_status") or "{}")
    data["simulated"] = data["latest_status"].get("simulated") is True
    age = (datetime.now() - datetime.fromisoformat(data["last_seen"])).total_seconds() if data.get("last_seen") else None
    hb = data.get("heartbeat_seconds") or 30
    data["health"] = "UNKNOWN" if age is None else "ONLINE" if age <= hb * 2 else "STALE" if age <= hb * 3 else "OFFLINE"
    if not data.get("enabled"):
        data["health"] = "OFFLINE"
    return data

def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()
                if not any(word in key.lower() for word in ("password", "token", "secret", "credential", "mesh_key", "private_key", "password_hash"))}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value

def store_local_token(identity, token):
    """Keep recoverable tokens outside DB exports and HTTP responses."""
    from mqtt_store import SecretFile
    path=database.DATA_DIR / ('device-token-'+hashlib.sha256(identity.encode()).hexdigest()+'.bin')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    with temporary.open('wb') as handle:
        handle.write(SecretFile.protect(json.dumps({'device_id':identity,'gateway_token':token}).encode()))
        handle.flush()
        import os
        os.fsync(handle.fileno())
    temporary.replace(path)
    return path


def enroll(identity, name, role, master_id="", address=""):
    safe_id(identity)
    if address:
        safe_id(address)
    if role not in ("MASTER", "NODE") or not isinstance(name, str) or not 1 <= len(name) <= 64:
        raise ValueError("Invalid device name or role")
    if role == "NODE":
        safe_id(master_id)
        if identity == master_id:
            raise ValueError("Node cannot be its own Master")
    token = secrets.token_hex(32) if role == "MASTER" else None
    with LOCK:
        db = connect()
        try:
            if role == "NODE" and not db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_role='MASTER' AND device_enrolled=1", (master_id,)).fetchone():
                raise ValueError("Enroll the Master first")
            if db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_enrolled=1", (identity,)).fetchone():
                raise ValueError("Identity already enrolled; use the explicit credential rotation API")
            device_identity.require_available_hardware(identity,db)
            if address and db.execute("SELECT 1 FROM nodes WHERE master_id=? AND node_address=? AND node_id!=? AND device_enrolled=1", (master_id, address, identity)).fetchone():
                raise ValueError("Duplicate logical Node address")
        finally:
            db.close()
        if not node_manager.get_node(identity):
            node_manager.add_node(identity, name, "ESP32", "ESP32-WROOM-32", "DevKit V1", "1.0.0-part1", "Wi-Fi", {}, address, True)
        db = connect()
        try:
            with db:
                db.execute("UPDATE nodes SET device_role=?,master_id=?,device_enrolled=1,device_token_hash=?,name=?,node_address=? WHERE node_id=?", (role, identity if role == "MASTER" else master_id, hashlib.sha256(token.encode()).hexdigest() if token else None, name, address, identity))
        finally:
            db.close()
        if role == "NODE":
            for pid, unit in (("temperature", "C"), ("humidity", "%RH")):
                if not sensor_manager.get_parameter(identity, pid):
                    sensor_manager.add_parameter(identity, pid, pid.title(), pid.upper(), "FLOAT", unit=unit, sensor_id=identity + "-DHT11-" + pid, graph_enabled=True)
    return token

def ingest(master_id, frame, transport='wifi'):
    body = validate_packet(frame)
    source = frame["source"]
    if frame["destination"] != "GATEWAY" or frame["type"] in {"COMMAND", "CONFIG_UPDATE", "CONFIG_GET"}:
        raise ValueError("Unsupported uplink destination/type")
    digest = hashlib.sha256(json.dumps(frame, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    now = datetime.now().isoformat()
    event = None
    with LOCK:
        db = connect()
        try:
            row = db.execute("SELECT * FROM nodes WHERE node_id=? AND device_enrolled=1 AND enabled=1", (source,)).fetchone()
            if not row or row["master_id"] != master_id or (source != master_id and row["device_role"] != "NODE"):
                raise PermissionError("Source is not assigned to this Master")
            previous = db.execute("SELECT fingerprint FROM device_receipts WHERE source_id=? AND message_id=?", (source, frame["message_id"])).fetchone()
            if previous:
                if previous[0] != digest:
                    raise ValueError("Message ID reused with different content")
                return {"accepted": True, "duplicate": True}
            kind = frame["type"]
            if kind in {"HELLO", "HEARTBEAT", "STATUS"}:
                if body.get("device_id") != source or body.get("role") != row["device_role"] or body.get("master_id") != row["master_id"]:
                    raise ValueError("Status identity/assignment mismatch")
                hb = body.get("heartbeat_seconds", 30)
                revision = body.get("configuration_revision", 0)
                if type(hb) is not int or not 5 <= hb <= 3600 or type(revision) is not int or revision < 0:
                    raise ValueError("Invalid status intervals/revision")
                db.execute("UPDATE nodes SET latest_status=?,heartbeat_seconds=?,configuration_revision=?,firmware_version=? WHERE node_id=?", (json.dumps(redact(body)), hb, revision, str(body.get("firmware_version", ""))[:64], source))
            elif kind == "TELEMETRY":
                sensor_kind, values = sensor_telemetry.validate(body)
                for pid in values:
                    unit = sensor_telemetry.SPECS[sensor_kind][pid][2]
                    if not sensor_manager.get_parameter(source,pid):
                        sensor_manager.add_parameter(source,pid,pid.replace('_',' ').title(),pid.upper(),'FLOAT',unit=unit,sensor_id=source+'-'+sensor_kind+'-'+pid,graph_enabled=True,decimal_places=sensor_telemetry.PRECISION.get(pid,2))
                # Same parameter table and widget transforms as the existing telemetry path.
                import sensor_widgets
                for parameter in sensor_manager.get_parameters(source):
                    cfg = sensor_widgets.config(parameter)
                    field = cfg["source_field"]
                    if parameter["enabled"] and field in values:
                        value = values[field] * cfg["scale"] + cfg["offset"]
                        db.execute("INSERT INTO telemetry_values(node_id,parameter_id,timestamp,value,data_type,quality,status,source) VALUES(?,?,?,?,?,'GOOD','NORMAL',?)", (source, parameter["parameter_id"], now, value, parameter["data_type"],transport))
                event = ("telemetry_update", {"node_id": source, "parameters": values, "timestamp": now})
            elif kind in {"ACK", "RESPONSE"}:
                cid = body.get("command_id")
                if cid != frame["correlation_id"]:
                    raise ValueError("Invalid command correlation")
                cmd = command_manager.get_command(safe_id(cid))
                if not cmd or cmd["node_id"] != source:
                    # Commands initiated locally on the Master are not Gateway commands.
                    if not str(cid).startswith("MSG-"):
                        raise PermissionError("Command belongs to another device")
                elif cmd["state"] in ("TIMEOUT","CANCELLED") and kind=="RESPONSE":
                    db.commit()
                    command_manager.record_command_event(cid,source,"LATE_RESPONSE",cmd["state"],details={"status":body.get("status"),"data":redact(body.get("data"))})
                elif cmd["state"] not in command_manager.TERMINAL_STATES:
                    # Existing manager owns command state transitions and audit records.
                    db.commit()
                    if kind == "ACK":
                        command_manager.process_command_ack(cid, source, status=body.get("status"), message=body.get("error_code"))
                    else:
                        if body.get("status") not in {"SUCCESS", "FAILED", "UNSUPPORTED"}:
                            raise ValueError("Invalid response status")
                        command_manager.process_command_response(cid, source, status=body["status"], data=redact(body.get("data")))
                    if kind=="RESPONSE" and body.get("status")=="SUCCESS" and isinstance(body.get("data"),dict):
                        result=body['data']
                        if type(result.get('configuration_revision')) is int:
                            db.execute('UPDATE nodes SET configuration_revision=? WHERE node_id=?',(result['configuration_revision'],source))
                        if cmd['command_type'] in ('CONFIG_UPDATE','SET_CONFIGURATION','SET_DEVICE_NAME') and isinstance(cmd.get('payload'),dict) and 'device_name' in cmd['payload'] and result.get('saved') is True:
                            db.execute('UPDATE nodes SET name=? WHERE node_id=?',(cmd['payload']['device_name'],source))
                    event = ("command_update", command_manager.get_command(cid))
            elif kind in {"EVENT", "ALARM", "DIAGNOSTIC"}:
                if kind=='EVENT' and body.get('event')=='COMMAND_ROUTE_FAILED':
                    if source!=master_id:raise PermissionError('Only the assigned Master may report routing failure')
                    cid=safe_id(body.get('command_id'));cmd=command_manager.get_command(cid)
                    target=db.execute('SELECT master_id FROM nodes WHERE node_id=?',(body.get('target_device_id'),)).fetchone()
                    if not cmd or cmd['node_id']!=body.get('target_device_id') or not target or target['master_id']!=master_id:raise PermissionError('Routing failure does not belong to Master')
                    if body.get('error_code') not in ('ROUTE_NOT_FOUND','HOP_LIMIT_EXCEEDED','ROUTE_QUEUE_FULL'):raise ValueError('INVALID_ROUTE_ERROR')
                    db.commit()
                    if cmd['state'] not in command_manager.TERMINAL_STATES:
                        command_manager.update_command_state(cid,'FAILED',error=body['error_code'])
                        command_manager.record_command_event(cid,cmd['node_id'],'ROUTE_FAILED','FAILED',error=body['error_code'])
                        _emit('command_update',command_manager.get_command(cid))
                db.execute("INSERT INTO logs(timestamp,severity,source,message,node_id) VALUES(?,?,?,?,?)", (now, "error" if kind == "ALARM" else "info", kind, json.dumps(redact(body))[:2048], source))
            else:
                raise ValueError("Unsupported uplink packet")
            db.execute("UPDATE nodes SET status='online',last_seen=?,updated_at=? WHERE node_id=?", (now, now, source))
            db.execute("INSERT INTO device_receipts VALUES(?,?,?,?)", (source, frame["message_id"], digest, now))
            db.execute("DELETE FROM device_receipts WHERE rowid NOT IN (SELECT rowid FROM device_receipts ORDER BY rowid DESC LIMIT 4096)")
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    if event:
        if event[0] == 'telemetry_update':
            # Emit the persisted, transformed parameter records used by every UI path.
            # Raw device parameters are a mapping and are not the browser event schema.
            latest = telemetry_manager.get_latest_values(source)
            fields = event[1]['parameters']
            event = ('telemetry_update', {
                'node_id': source, 'received_at': now,
                'parameters': [p for p in latest if sensor_widgets.config(p)['source_field'] in fields]
            })
        _emit(*event)
    return {"accepted": True, "duplicate": False}

def pending_commands(master_id, device_id=None):
    db = connect()
    try:
        rows = db.execute("SELECT c.* FROM commands c JOIN nodes n ON c.node_id=n.node_id WHERE n.master_id=? AND n.device_enrolled=1 AND n.enabled=1 AND c.state NOT IN ('COMPLETED','FAILED','CANCELLED','TIMEOUT') ORDER BY c.priority DESC,c.created_at LIMIT 64", (master_id,)).fetchall()
    finally:
        db.close()
    for row in rows:
        if device_id is not None and row['node_id'] != device_id:
            continue
        cmd = command_manager.get_command(row["command_id"])
        if not command_manager.claim_device_dispatch(cmd["command_id"]):
            continue
        cmd=command_manager.get_command(cmd["command_id"])
        args = cmd.get("payload") or {}
        kind = cmd["command_type"]
        if kind not in SAFE_COMMANDS:
            command_manager.update_command_state(cmd["command_id"], "FAILED", error="Command not supported by Part 1 device adapter")
            continue
        if cmd["state"] == "QUEUED":
            command_manager.update_command_state(cmd["command_id"], "SENT")
        out = packet("COMMAND", "GATEWAY", cmd["node_id"], {"command_id": cmd["command_id"], "command": kind, "arguments": args}, message_id=cmd["command_id"], correlation_id=cmd["command_id"])
        # Stable encoding across polls, reconnects, and transport changes.
        out["timestamp"] = int(datetime.fromisoformat(cmd["created_at"]).timestamp())
        if len(json.dumps(out, separators=(",", ":")).encode()) > MAX_FRAME or out["payload_length"] > MAX_PAYLOAD:
            command_manager.update_command_state(cmd["command_id"], "FAILED", error="Command payload exceeds firmware frame limit")
            continue
        return [out]
    return []

@bp.post("/api/v1/device/<operation>")
def exchange(operation):
    if operation not in {"exchange", "register", "heartbeat", "telemetry", "status", "ack", "response", "diagnostic", "events", "alarms"}:
        return jsonify(error="Unknown operation"), 404
    master_id, error = authenticate_master()
    if error:
        return error
    body, error = json_body()
    if error:
        return error
    try:
        result = ingest(master_id, body)
        result["commands"] = pending_commands(master_id)
        return jsonify(result)
    except PermissionError as exc:
        return jsonify(error=str(exc)), 403
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify(error=str(exc)), 400

@bp.route("/api/v1/devices", methods=["GET", "POST"])
@require_admin
def devices():
    if request.method == "GET":
        db = connect()
        try:
            return jsonify(devices=[public_node(r) for r in db.execute("SELECT * FROM nodes WHERE device_enrolled=1")])
        finally:
            db.close()
    body, error = json_body()
    if error:
        return error
    try:
        token = enroll(body.get("device_id"), body.get("device_name"), body.get("role"), body.get("master_id", ""), str(body.get("node_address", "")))
        return jsonify(success=True, device_id=body["device_id"], credential_state="LOCAL_PROVISIONING_REQUIRED" if token else "NOT_REQUIRED"), 201
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400

@bp.post("/api/v1/devices/<identity>/rotate-token")
@require_admin
def rotate(identity):
    # A new credential must not be issued over the existing ordinary HTTP route.
    return jsonify(error="LOCAL_PROVISIONING_REQUIRED",message="Use the local enrollment console to rotate and USB-provision credentials"),409


@bp.route("/api/v1/commands", methods=["GET", "POST"])
@require_admin
def commands():
    if request.method == "GET":
        return jsonify(commands=[control.state(c) for c in command_manager.list_commands(limit=100)])
    body, error = json_body()
    if error:
        return error
    try:
        if set(body)-{'node_id','command_type','payload','timeout_seconds','command_id','priority','max_retries','ack_timeout_seconds','response_timeout_seconds','expiry_seconds'}:raise ValueError('UNSUPPORTED_REQUEST_FIELD')
        timeout=body.get('timeout_seconds',60)
        if type(timeout) is not int or not 1<=timeout<=300:raise ValueError('TIMEOUT_MUST_BE_INTEGER_1_TO_300')
        identity_db=connect()
        try:body['node_id']=device_identity.resolve(body.get('node_id'),identity_db)
        finally:identity_db.close()
        kind = body.get("command_type")
        control.validate_command(kind,body.get("payload",{}))
        db = connect()
        try:
            if not db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_enrolled=1 AND enabled=1", (body.get("node_id"),)).fetchone():
                raise ValueError("Target must be enrolled and enabled")
        finally:
            db.close()
        if body.get("command_id"):
            old = command_manager.get_command(body["command_id"])
            if old:
                if old["node_id"] != body.get("node_id") or old["command_type"] != kind or old["payload"] != body.get("payload", {}):
                    return jsonify(error="Command ID reused with different content"), 409
                return jsonify(command=old, duplicate=True), 200
        cmd = command_manager.create_command(body.get("node_id"), kind, body.get("payload", {}), timeout_seconds=timeout, command_id=body.get("command_id"),priority=body.get('priority',1),max_retries=body.get('max_retries',3),ack_timeout_seconds=body.get('ack_timeout_seconds',5),response_timeout_seconds=body.get('response_timeout_seconds',timeout),expiry_seconds=body.get('expiry_seconds',300))
        _emit("command_update", cmd)
        return jsonify(command=control.state(cmd)), 201
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400

def install(app, emit):
    global _emit
    _emit = emit
    migrate()
    app.register_blueprint(bp)

@bp.route('/api/v1/devices/<identity>/config', methods=['GET', 'POST'])
@require_admin
def configuration(identity):
    db=connect()
    try:
        row=db.execute('SELECT * FROM nodes WHERE node_id=? AND device_enrolled=1',(identity,)).fetchone()
    finally:
        db.close()
    if not row:
        return jsonify(error='Device not enrolled'),404
    if request.method=='GET':
        return jsonify(source='LAST_RECEIVED_STATUS',configuration_revision=row['configuration_revision'],status=public_node(row)['latest_status'],
                       retrieval='Submit GET_CONFIG through /api/v1/commands for a fresh device response')
    data,error=json_body()
    if error:return error
    try:control.validate_command('CONFIG_UPDATE',data)
    except (ValueError,TypeError) as error:return jsonify(error=str(error)),400
    cmd=command_manager.create_command(identity,'CONFIG_UPDATE',data,timeout_seconds=60)
    _emit('command_update',cmd)
    return jsonify(command=cmd,delivery='POLLING_OR_MQTT'),202

@bp.get('/api/v1/devices/<identity>/status')
@require_admin
def status(identity):
    db=connect()
    try:row=db.execute('SELECT * FROM nodes WHERE node_id=? AND device_enrolled=1',(identity,)).fetchone()
    finally:db.close()
    return (jsonify(device=public_node(row)),200) if row else (jsonify(error='Device not enrolled'),404)

@bp.get('/api/v1/devices/<identity>/diagnostics')
@require_admin
def diagnostics(identity):
    db=connect()
    try:rows=db.execute("SELECT * FROM logs WHERE node_id=? AND source IN ('EVENT','ALARM','DIAGNOSTIC') ORDER BY id DESC LIMIT 100",(identity,)).fetchall()
    finally:db.close()
    return jsonify(entries=[dict(row) for row in rows])
