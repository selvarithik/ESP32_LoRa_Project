"""Local HTTP/TCP device transport. No MQTT, Internet, bearer disclosure or demo data."""
import atexit
from collections import OrderedDict
import hashlib
import hmac
import ipaddress
import json
import secrets
import threading
import time
from contextlib import contextmanager
from flask import Flask, jsonify, render_template, request
from werkzeug.serving import make_server, WSGIRequestHandler
import database
import device_api
from pathlib import Path
from mqtt_store import SecretFile

MAX_PACKET = 4096
MAX_REPLY = 6144

@contextmanager
def connection():
    db=database.get_connection()
    try:
        with db:yield db
    finally:db.close()

def signature(key, domain, identity, nonce, body):
    return hmac.new(key, (domain+'\n'+identity+'\n'+nonce+'\n').encode()+body, hashlib.sha256).hexdigest()

def credential_file(identity):
    return database.DATA_DIR/('local-ip-token-'+hashlib.sha256(identity.encode()).hexdigest()+'.bin')

def credential_key(identity, fingerprint, allow_legacy=False):
    """Only the DPAPI file supplies the MAC key; the DB holds its one-way verifier."""
    try:
        value=json.loads(SecretFile.protect(credential_file(identity).read_bytes(),True))
        if value['device_id']!=identity:return None
        key=hashlib.sha256(value['local_ip_token'].encode()).digest()
        # Accept the initial development representation only for the migration.
        if fingerprint != hashlib.sha256(key).hexdigest() and not (allow_legacy and fingerprint == key.hex()):return None
        return key
    except Exception:return None

def save_credential(identity, token):
    key=hashlib.sha256(token.encode()).digest();fingerprint=hashlib.sha256(key).hexdigest()
    with connection() as db:
        old=db.execute('SELECT key_hash FROM local_ip_credentials WHERE device_id=?',(identity,)).fetchone()
        if old and old['key_hash'] not in (key.hex(),fingerprint):raise ValueError('CREDENTIAL_ROTATION_NOT_REQUESTED')
    path=credential_file(identity);temporary=path.with_suffix('.tmp')
    temporary.write_bytes(SecretFile.protect(json.dumps({'device_id':identity,'local_ip_token':token}).encode()));temporary.replace(path)
    with connection() as db:db.execute('INSERT INTO local_ip_credentials VALUES(?,?) ON CONFLICT(device_id) DO UPDATE SET key_hash=excluded.key_hash',(identity,fingerprint))

def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out: raise ValueError('INVALID_JSON')
            out[key] = value
        return out
    obj = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('INVALID_JSON')))
    def depth(value, n=0):
        if n > 8: raise ValueError('INVALID_JSON')
        if isinstance(value, dict):
            for v in value.values(): depth(v, n+1)
        elif isinstance(value, list):
            for v in value: depth(v, n+1)
    depth(obj)
    if not isinstance(obj, dict): raise ValueError('INVALID_JSON')
    return obj

class BoundedHandler(WSGIRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(3)
    def log_request(self, code='-', size='-'):
        # Do not put device identities, headers or payloads into access logs.
        pass

class Service:
    def __init__(self):
        self.lock = threading.RLock()
        self.lifecycle = threading.RLock()
        self.server = None
        self.thread = None
        self.state = 'STOPPED'
        self.error = None
        self.nonces = OrderedDict()
        self.connections = OrderedDict()
        self.received = self.accepted = self.rejected = self.duplicates = 0
        self.last_packet_error = None
        self.last_received_at = self.last_persisted_at = None
        self.app = Flask('local_ip_peer')
        self.app.config['MAX_CONTENT_LENGTH'] = MAX_PACKET
        self.app.add_url_rule('/api/v1/device/local-challenge', 'challenge', self.challenge)
        self.app.add_url_rule('/api/v1/device/local-exchange', 'exchange', self.exchange, methods=['POST'])

    def migrate(self):
        with connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS local_ip_settings (id INTEGER PRIMARY KEY CHECK(id=1),document TEXT NOT NULL)')
            db.execute('INSERT OR IGNORE INTO local_ip_settings VALUES(1,?)', (json.dumps(dict(schema_version=1,revision=1,enabled=False,bind_address='127.0.0.1',port=5001)),))
            db.execute('CREATE TABLE IF NOT EXISTS local_ip_permissions (device_id TEXT PRIMARY KEY,direct_allowed INTEGER NOT NULL DEFAULT 0)')
            db.execute('CREATE TABLE IF NOT EXISTS local_ip_credentials (device_id TEXT PRIMARY KEY,key_hash TEXT NOT NULL)')
            for row in db.execute('SELECT device_id,key_hash FROM local_ip_credentials').fetchall():
                key=credential_key(row['device_id'],row['key_hash'],allow_legacy=True)
                if key and row['key_hash']==key.hex():
                    db.execute('UPDATE local_ip_credentials SET key_hash=? WHERE device_id=?',(hashlib.sha256(key).hexdigest(),row['device_id']))

    def settings(self):
        with connection() as db:
            return json.loads(db.execute('SELECT document FROM local_ip_settings WHERE id=1').fetchone()[0])

    def peer(self, identity):
        if not isinstance(identity, str) or not device_api.ID.fullmatch(identity): return None
        with connection() as db:
            row = db.execute("SELECT n.*,coalesce(p.direct_allowed,0) AS direct_allowed,c.key_hash AS local_key_hash FROM nodes n LEFT JOIN local_ip_permissions p ON p.device_id=n.node_id LEFT JOIN local_ip_credentials c ON c.device_id=n.node_id WHERE n.node_id=? AND n.device_enrolled=1 AND n.enabled=1", (identity,)).fetchone()
        if not row or not row['local_key_hash'] or (row['device_role']=='NODE' and not row['direct_allowed']): return None
        if row['device_role']=='NODE':
            with connection() as db:
                master=db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_enrolled=1 AND enabled=1 AND device_role='MASTER'",(row['master_id'],)).fetchone()
            if not master:return None
        key=credential_key(identity,row['local_key_hash'])
        if key is None:return None
        result=dict(row);result['_key']=key;return result

    def challenge(self):
        identity = request.headers.get('X-Device-ID', '')
        if not device_api.rate_limit('local:'+str(request.remote_addr), 120):return jsonify(error='RATE_LIMIT'),429
        peer = self.peer(identity)
        if not peer: return jsonify(error='AUTH_FAILED'),401
        nonce = secrets.token_hex(16)
        stamp = str(int(time.time()))
        with self.lock:
            now=time.monotonic()
            for old in list(self.nonces):
                if now-self.nonces[old][1]>30:self.nonces.pop(old,None)
            self.nonces[nonce] = (identity, now)
            while len(self.nonces)>256:self.nonces.popitem(last=False)
        return jsonify(nonce=nonce,unix_time=int(stamp),signature=signature(peer['_key'],'LOCALIP1-TIME',identity,nonce,stamp.encode()))

    def exchange(self):
        if request.headers.get('Transfer-Encoding') or request.content_length is None:return jsonify(error='CONTENT_LENGTH_REQUIRED'),411
        if not 0 < request.content_length <= MAX_PACKET:return jsonify(error='OVERSIZED'),413
        identity=request.headers.get('X-Device-ID','');nonce=request.headers.get('X-Local-Nonce','');proof=request.headers.get('X-Local-Signature','')
        peer=self.peer(identity)
        with self.lock:
            entry=self.nonces.pop(nonce,None);self.received+=1;self.last_received_at=int(time.time())
        if not peer or not entry or entry[0]!=identity or time.monotonic()-entry[1]>30:
            return self.failure('AUTH_FAILED',401)
        raw=request.get_data();key=peer['_key']
        if request.mimetype!='application/json' or not hmac.compare_digest(signature(key,'LOCALIP1',identity,nonce,raw),proof):
            return self.failure('AUTH_FAILED',401)
        try:
            frame=strict_json(raw)
            if set(frame)!={'protocol_version','message_id','source','destination','origin_id','final_destination_id','next_hop','type','ttl','timestamp','sequence_number','correlation_id','payload','payload_length','payload_crc32'}:raise ValueError('INVALID_FIELDS')
            device_api.safe_id(frame['next_hop'])
            strict_json(frame['payload'])
            device_api.validate_packet(frame)
            if peer['device_role']=='NODE' and frame.get('source')!=identity:raise PermissionError()
            stamp=frame['timestamp'];now=int(time.time())
            if (stamp and (stamp>now+30 or now-stamp>300)) or (not stamp and frame['type'] in ('COMMAND','CONFIG_GET','CONFIG_UPDATE','ACK','RESPONSE')):raise ValueError('EXPIRED')
            result=device_api.ingest(peer['master_id'],frame,transport='local-ip')
            commands=device_api.pending_commands(peer['master_id'],identity if peer['device_role']=='NODE' else None)
            result.update(schema_version=1,received_message_id=frame['message_id'],receipt='PERSISTED',commands=commands)
            body=json.dumps(result,separators=(',',':'),ensure_ascii=False).encode()
            if len(body)>MAX_REPLY:raise ValueError('OVERSIZED_REPLY')
            with self.lock:
                self.accepted+=1;self.duplicates+=bool(result.get('duplicate'));self.last_persisted_at=int(time.time())
                self.connections[identity]=dict(device_id=identity,peer_ip=request.remote_addr,role=peer['device_role'],path='DIRECT',interface='IP_UNREPORTED',state='CONNECTED',last_seen=int(time.time()),last_error=None,last_message_id=frame['message_id'])
                self.connections.move_to_end(identity)
                while len(self.connections)>64:self.connections.popitem(last=False)
            response=self.app.response_class(body,mimetype='application/json')
            response.headers['X-Local-Signature']=signature(key,'LOCALIP1-REPLY',identity,nonce,body)
            response.headers['Cache-Control']='no-store'
            return response
        except PermissionError:return self.failure('UNAUTHORIZED',403)
        except (ValueError,TypeError,KeyError,UnicodeError):return self.failure('INVALID_OR_EXPIRED_PACKET',400)
        except Exception:return self.failure('STORAGE_FAILED',503)

    def failure(self, code, status):
        with self.lock:self.rejected+=1;self.last_packet_error=code
        return jsonify(error=code),status

    def stop(self):
        server=self.server;thread=self.thread
        self.server=None;self.thread=None
        if server:server.shutdown();server.server_close()
        if thread and thread is not threading.current_thread():thread.join(timeout=5)
        self.state='STOPPED'
        with self.lock:self.nonces.clear()

    def start(self, settings=None):
        settings=settings or self.settings()
        if self.server:return
        self.error=None
        try:
            self.server=make_server(settings['bind_address'],settings['port'],self.app,threaded=False,request_handler=BoundedHandler)
            self.thread=threading.Thread(target=self.server.serve_forever,name='local-ip-listener',daemon=True)
            self.thread.start();self.state='LISTENING'
        except (OSError,SystemExit):
            self.server=None;self.state='FAILED';self.error='BIND_FAILED';raise ValueError('BIND_FAILED') from None

    def configure(self, data):
        if set(data)!={'expected_revision','enabled','bind_address','port'}:raise ValueError('INVALID_SETTINGS')
        if type(data['enabled']) is not bool or type(data['port']) is not int or not 1024<=data['port']<=65535:raise ValueError('INVALID_SETTINGS')
        try:address=ipaddress.IPv4Address(data['bind_address'])
        except Exception:raise ValueError('INVALID_BIND_ADDRESS') from None
        if address.is_unspecified or address.is_multicast or address.is_link_local or not (address.is_private or address.is_loopback) or str(address)=='255.255.255.255':raise ValueError('PRIVATE_INTERFACE_REQUIRED')
        with self.lifecycle:
            old=self.settings()
            if type(data['expected_revision']) is not int or data['expected_revision']!=old['revision']:raise ValueError('REVISION_CONFLICT')
            if old['revision']>=0xffffffff:raise ValueError('REVISION_OVERFLOW')
            new=dict(schema_version=1,revision=old['revision']+1,**{k:data[k] for k in ('enabled','bind_address','port')})
            was_running=self.server is not None
            self.stop()
            try:
                if new['enabled']:self.start(new)
                with connection() as db:db.execute('UPDATE local_ip_settings SET document=? WHERE id=1',(json.dumps(new),))
            except Exception:
                self.stop()
                if was_running:
                    try:self.start(old)
                    except ValueError:pass
                raise
        return self.status()

    def status(self):
        with self.lock:
            now=int(time.time());connections=[]
            for row in self.connections.values():
                row=dict(row);row['state']='CONNECTED' if now-row['last_seen']<=15 else 'STALE' if now-row['last_seen']<=90 else 'DISCONNECTED';connections.append(row)
            with connection() as db:
                devices=[dict(r) for r in db.execute('SELECT n.node_id AS device_id,n.device_role AS role,n.master_id,n.enabled,coalesce(p.direct_allowed,0) AS direct_allowed FROM nodes n LEFT JOIN local_ip_permissions p ON p.device_id=n.node_id WHERE n.device_enrolled=1')]
            return dict(settings=self.settings(),state=self.state,last_error=self.error,last_packet_error=self.last_packet_error,last_received_at=self.last_received_at,last_database_persisted_at=self.last_persisted_at,persistence_receipts=self.accepted,received=self.received,accepted=self.accepted,rejected=self.rejected,duplicates=self.duplicates,connections=connections,devices=devices,security='HMAC_SHA256_CHALLENGE_RESPONSE',confidentiality='TRUSTED_LAN_OR_VERIFIED_HTTPS_REQUIRED',listener_active=self.server is not None)

service=Service()

def install(app):
    service.migrate()
    @app.get('/local-ip',endpoint='local_ip_page')
    def page():return render_template('local_ip.html')
    @app.get('/api/local-ip',endpoint='local_ip_status')
    @device_api.require_admin
    def status():return jsonify(service.status())
    @app.post('/api/local-ip',endpoint='local_ip_configure')
    @device_api.require_admin
    def configure():
        data,error=device_api.json_body(1024)
        if error:return error
        try:return jsonify(service.configure(data))
        except ValueError as e:return jsonify(error=str(e)),409 if str(e)=='REVISION_CONFLICT' else 400
    @app.post('/api/local-ip/devices/<identity>',endpoint='local_ip_permission')
    @device_api.require_admin
    def permission(identity):
        data,error=device_api.json_body(256)
        if error:return error
        if set(data)!={'direct_allowed'} or type(data['direct_allowed']) is not bool:return jsonify(error='INVALID_PERMISSION'),400
        with connection() as db:
            if not db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_enrolled=1",(identity,)).fetchone():return jsonify(error='NOT_ENROLLED'),404
            db.execute('INSERT INTO local_ip_permissions VALUES(?,?) ON CONFLICT(device_id) DO UPDATE SET direct_allowed=excluded.direct_allowed',(identity,int(data['direct_allowed'])))
        return jsonify(ok=True)
    atexit.register(service.stop)

def start_saved():
    if service.settings()['enabled']:service.start()
