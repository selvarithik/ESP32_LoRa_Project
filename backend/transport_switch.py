"""Password-gated, durable coordination. Device responses, never submission, prove state."""
import ipaddress
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from flask import jsonify, request
from werkzeug.security import check_password_hash
import account_settings
import command_manager
import database

LOCK=threading.RLock()
ATTEMPTS=defaultdict(deque)

def connection():
    db=database.get_connection()
    db.execute('CREATE TABLE IF NOT EXISTS transport_switches (device_id TEXT PRIMARY KEY, document TEXT NOT NULL)')
    db.commit()
    return db

def load(device):
    db=connection()
    try:
        row=db.execute('SELECT document FROM transport_switches WHERE device_id=?',(device,)).fetchone()
        return json.loads(row['document']) if row else None
    finally:db.close()

def save(device, doc):
    db=connection()
    try:
        db.execute('INSERT OR REPLACE INTO transport_switches VALUES(?,?)',(device,json.dumps(doc)))
        db.commit()
    finally:db.close()

def refreshed(device):
    doc=load(device)
    if not doc:return {'state':'IDLE'}
    for action,cid in doc['commands'].items():
        command=command_manager.get_command(cid)
        if not command:continue
        doc.setdefault('command_states',{})[action]=command['state']
        if action==doc.get('last_action'):
            if command['state']=='COMPLETED' and isinstance(command.get('result'),dict):
                result=command['result']
                if result.get('transaction_id')==doc['transaction_id']:
                    doc['state']=result.get('state','UNKNOWN')
                    doc['device_revision']=result.get('configuration_revision',doc['device_revision'])
                    doc['deadline']=result.get('deadline',doc.get('deadline'))
            elif command['state'] in ('FAILED','TIMEOUT','CANCELLED'):doc['state']='UNKNOWN_REQUIRES_DEVICE_STATUS'
    if doc.get('state')=='TRIAL' and doc.get('deadline',0)<=time.time():doc['state']='EXPIRED_AWAITING_DEVICE_STATUS'
    db=connection()
    try:node=db.execute('SELECT latest_status FROM nodes WHERE node_id=?',(device,)).fetchone()
    finally:db.close()
    try:reported=json.loads(node['latest_status']).get('transport_switch',{}) if node else {}
    except (ValueError,TypeError):reported={}
    if reported.get('transaction_id')==doc['transaction_id'] and reported.get('state') in ('COMMITTED','CANCELLED','ROLLED_BACK'):
        doc['state']=reported['state'];doc['device_revision']=reported.get('configuration_revision',doc['device_revision'])
    save(device,doc)
    return doc

def authorize_password(data):
    # A normal LAN HTTP page is not a confidential password channel.
    try:loopback=ipaddress.ip_address(request.remote_addr).is_loopback
    except ValueError:loopback=False
    if not request.is_secure and not loopback:raise ValueError('HTTPS_OR_LOOPBACK_REQUIRED')
    password=data.pop('admin_password',None)
    db=account_settings.connect()
    try:
        actor=account_settings.current(db)
        if not actor or actor['role'] not in ('creator','administrator') or actor['must_change']:raise ValueError('ADMINISTRATOR_REQUIRED')
        attempts=ATTEMPTS[actor['id']];now=time.monotonic()
        while attempts and now-attempts[0]>60:attempts.popleft()
        if len(attempts)>=5:raise ValueError('REAUTH_RATE_LIMITED')
        attempts.append(now)
        if not isinstance(password,str) or len(password)>128 or not check_password_hash(actor['password_hash'],password):raise ValueError('PASSWORD_CONFIRMATION_FAILED')
    finally:
        password=None
        db.close()

def proof(doc):
    cid=doc['commands'].get('probe')
    c=command_manager.get_command(cid) if cid else None
    r=c.get('result') if c else None
    return bool(c and c['node_id']==doc['device_id'] and c['state']=='COMPLETED' and c.get('ack_status')=='ACCEPTED' and isinstance(r,dict) and r.get('ok') is True and r.get('path_verified') is True and r.get('transaction_id')==doc['transaction_id'] and r.get('transport')==doc['target_transport'] and r.get('gateway_verified_transport')==doc['target_transport'])

def action(device, operation, data):
    import device_api
    authorize_password(data)
    db=connection()
    try:node=db.execute('SELECT * FROM nodes WHERE node_id=? AND device_enrolled=1 AND enabled=1',(device,)).fetchone()
    finally:db.close()
    if not node or node['device_role']!='MASTER':raise ValueError('ENROLLED_MASTER_REQUIRED')
    doc=refreshed(device)
    if operation=='prepare':
        if set(data)!={'local_ip_enabled','expected_revision','timeout_seconds'} or type(data['local_ip_enabled']) is not bool or type(data['expected_revision']) is not int or type(data['timeout_seconds']) is not int or not 30<=data['timeout_seconds']<=180:raise ValueError('INVALID_TRANSPORT_REQUEST')
        if data['expected_revision']!=node['configuration_revision']:raise ValueError('REVISION_CONFLICT')
        if doc['state'] not in ('IDLE','COMMITTED','CANCELLED','ROLLED_BACK'):raise ValueError('TRANSACTION_BUSY_OR_UNKNOWN')
        doc=dict(device_id=device,transaction_id='TX-'+secrets.token_hex(12),state='PREPARE_QUEUED',target_transport='IP' if data['local_ip_enabled'] else 'MQTT',device_revision=data['expected_revision'],commands={})
        payload=dict(data,transport_action='prepare',transaction_id=doc['transaction_id'])
    else:
        if set(data)!={'transaction_id'} or data['transaction_id']!=doc.get('transaction_id'):raise ValueError('TRANSACTION_NOT_FOUND')
        prior=doc['commands'].get(operation)
        if prior:return doc  # Idempotent HTTP retry; no duplicate command execution.
        if operation=='apply' and doc['state']!='PREPARED':raise ValueError('PREPARE_RESPONSE_REQUIRED')
        if operation in ('probe','confirm') and doc['state']!='TRIAL':raise ValueError('APPLY_RESPONSE_REQUIRED')
        if operation=='confirm' and not proof(doc):raise ValueError('NEW_PATH_ACK_AND_RESPONSE_REQUIRED')
        if operation not in ('apply','probe','confirm','cancel'):raise ValueError('INVALID_TRANSPORT_ACTION')
        payload=dict(transport_action=operation,transaction_id=doc['transaction_id'],expected_revision=doc['device_revision'])
    if operation=='probe':
        c=command_manager.create_command(device,'PING',{'message':'TRANSPORT:'+doc['transaction_id']},timeout_seconds=20,max_retries=1)
    else:
        c=command_manager.create_command(device,'CONFIG_UPDATE',payload,transport_authorized=True,timeout_seconds=20,max_retries=1,expiry_seconds=30)
        doc['last_action']=operation
        doc['state']=operation.upper()+'_QUEUED'
    doc['commands'][operation]=c['command_id'];save(device,doc)
    device_api._emit('command_update',c)
    return doc

def install(bp):
    import device_api
    @bp.route('/api/v1/devices/<identity>/transport',methods=['GET','POST'])
    @device_api.require_admin
    def transport(identity):
        try:
            device_api.safe_id(identity)
            with LOCK:
                if request.method=='GET':return jsonify(refreshed(identity))
                data,error=device_api.json_body(1024)
                if error:return error
                operation=data.pop('operation',None)
                return jsonify(action(identity,operation,data)),202
        except (ValueError,TypeError,KeyError):return jsonify(error='TRANSPORT_ACTION_REJECTED',detail='Check password, revision, transaction state and verified new-path ACK/RESPONSE.'),409
