"""Executable contract 1.0.1, wire schema 1. No network or database side effects."""
import hashlib
import json
import re
import ssl
import time
from cryptography import x509
from cryptography.hazmat.primitives import hashes

FIELDS = ('profile_name','provider','host','port','mqtt_version','tls','ca_cert','username',
          'password','client_id','keepalive_s','timeout_s','qos_default','topic_prefix','gateway_id')
TYPES = ('telemetry','status','command','command_ack','config','events','discovery',
         'chat/message','chat/ack','chat/status','chat/command')
SHARED = ('host','port','mqtt_version','tls','qos_default','topic_prefix','gateway_id')
ID = re.compile(r'[A-Za-z0-9_.:-]{1,48}\Z')
HEX = re.compile(r'[0-9a-f]{64}\Z')
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z')

class ContractError(ValueError):
    def __init__(self, code='INVALID_REQUEST', field=''):
        super().__init__(code)
        self.code, self.field = code, field

def require(condition, field='', code='INVALID_REQUEST'):
    if not condition:
        raise ContractError(code, field)

def integer(value, low=0, high=0xffffffff):
    return type(value) is int and low <= value <= high

def text(value, low, high):
    try:
        return isinstance(value, str) and '\0' not in value and low <= len(value.encode('utf-8')) <= high
    except UnicodeError:
        return False

def safe_id(value):
    return isinstance(value, str) and ID.fullmatch(value) is not None

def preserved(value):
    return value is None or isinstance(value, str) and (not value or set(value) == {'*'})

def certificates(pem):
    require(text(pem, 1, 4096), 'ca_cert', 'INVALID_PROFILE')
    blocks = re.findall(r'-----BEGIN CERTIFICATE-----\s+[A-Za-z0-9+/=\s]+-----END CERTIFICATE-----', pem)
    require(blocks and not re.sub(r'-----BEGIN CERTIFICATE-----\s+[A-Za-z0-9+/=\s]+-----END CERTIFICATE-----', '', pem).strip(), 'ca_cert', 'INVALID_PROFILE')
    try:
        certs = [x509.load_pem_x509_certificate(b.encode('ascii')) for b in blocks]
        require(all(c.extensions.get_extension_for_class(x509.BasicConstraints).value.ca for c in certs), 'ca_cert', 'INVALID_PROFILE')
        return certs
    except (ValueError, x509.ExtensionNotFound, UnicodeError):
        raise ContractError('INVALID_PROFILE', 'ca_cert') from None

def validate_profile(profile, connection_ready=False):
    require(type(profile) is dict and set(profile) == set(FIELDS), 'profile', 'INVALID_PROFILE')
    checks = {
        'profile_name': text(profile['profile_name'],1,64),
        'provider': profile['provider'] in ('EMQX','HIVEMQ','MOSQUITTO','CUSTOM'),
        'host': text(profile['host'],1,253) and bool(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*',profile['host'])) and profile['host'].lower() not in ('localhost','0.0.0.0') and not profile['host'].startswith('127.'),
        'port': integer(profile['port'],1,65535), 'mqtt_version': profile['mqtt_version']=='3.1.1',
        'tls': profile['tls'] is True, 'username':text(profile['username'],int(connection_ready),128),
        'password':text(profile['password'],int(connection_ready),256),
        'client_id':text(profile['client_id'],1,64) and bool(re.fullmatch(r'[A-Za-z0-9_.:-]+',profile['client_id'])),
        'keepalive_s':integer(profile['keepalive_s'],15,300), 'timeout_s':integer(profile['timeout_s'],2,30),
        'qos_default':integer(profile['qos_default'],1,1),
        'topic_prefix':text(profile['topic_prefix'],1,128) and bool(re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',profile['topic_prefix'])),
        'gateway_id':safe_id(profile['gateway_id'])}
    for key, valid in checks.items():
        require(valid,key,'INVALID_PROFILE')
    certificates(profile['ca_cert'])
    return dict(profile)

def topic(profile, message_type):
    require(message_type in TYPES,'message_type')
    require(text(profile.get('topic_prefix'),1,128) and re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',profile['topic_prefix']) and safe_id(profile.get('gateway_id')),'topic')
    return '/'.join((profile['topic_prefix'],profile['gateway_id'],message_type))

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)

def snapshot(profile, shared_revision=0):
    validate_profile(profile)
    require(integer(shared_revision),'shared_revision')
    values = {k:profile[k] for k in SHARED}
    values['host'] = values['host'].lower()
    values['ca_fingerprints'] = sorted({c.fingerprint(hashes.SHA256()).hex() for c in certificates(profile['ca_cert'])})
    return {'schema_version':1,'shared_revision':shared_revision,'values':values}

def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()

def compare(ours, peer, received_at, now=None):
    now = time.time() if now is None else now
    if not peer or received_at is None or not 0 <= now-received_at <= 120:
        return {'status':'UNKNOWN','fields':[],'message':'Peer snapshot unavailable or stale'}
    if peer.get('schema_version') != 1 or set(peer) != set(ours) or type(peer.get('values')) is not dict or set(peer['values']) != set(ours['values']) or not integer(peer.get('shared_revision')):
        return {'status':'INCOMPATIBLE','fields':[],'message':'Incompatible peer snapshot'}
    if peer['values']['gateway_id'] != ours['values']['gateway_id']:
        return {'status':'UNKNOWN','fields':[],'message':'Peer scope differs'}
    fields = sorted('profile.'+key for key in ours['values'] if type(ours['values'][key]) is not type(peer['values'][key]) or ours['values'][key]!=peer['values'][key])
    if ours['shared_revision'] != peer['shared_revision']:
        fields.append('shared_revision')
    return {'status':'MISMATCH' if fields else 'MATCH','fields':sorted(fields),
            'message':'Master config differs' if fields else 'Shared settings match',
            'secrets':'LOCAL_NOT_COMPARED'}

def loads(raw, maximum=6144):
    def pairs(items):
        result = {}
        for key,value in items:
            require(key not in result,'json')
            result[key] = value
        return result
    def depth(v, n=0):
        require(n<=8,'json')
        if isinstance(v,dict):
            for k,x in v.items():
                require(text(k,0,256),'json');depth(x,n+1)
        elif isinstance(v,list):
            for x in v: depth(x,n+1)
        elif isinstance(v,str):require(text(v,0,maximum),'json')
    try:
        if isinstance(raw,str):raw=raw.encode('utf-8')
        require(len(raw)<=maximum,'payload')
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _: require(False,'json'))
        require(type(value) is dict,'json');depth(value);return value
    except (ValueError,UnicodeError,RecursionError,TypeError):
        raise ContractError('INVALID_REQUEST','json') from None

def envelope(raw, received_topic, profile, now=None, retained=False):
    d=loads(raw);now=time.time() if now is None else now
    required={'schema_version','message_id','gateway_id','master_id','device_id','message_type','timestamp','data'}
    require(required<=set(d)<=required|{'correlation_id','configuration_revision','expires_at'})
    require(integer(d['schema_version'],1,1),'schema_version')
    for k in ('message_id','master_id','device_id'):require(safe_id(d[k]),k)
    require(d['gateway_id']==profile['gateway_id'],'gateway_id')
    require(received_topic==topic(profile,d['message_type']),'topic')
    require(not retained or d['message_type']=='status','retain')
    require(integer(d['timestamp'],0,0x7fffffffffffffff),'timestamp')
    if 'correlation_id' in d:require(safe_id(d['correlation_id']),'correlation_id')
    if 'configuration_revision' in d:require(integer(d['configuration_revision']),'configuration_revision')
    if d['message_type'] not in ('status','telemetry'):
        require(integer(d.get('expires_at'),1,0x7fffffffffffffff) and 0<d['timestamp']<=now+30 and d['timestamp']<d['expires_at']<=d['timestamp']+300 and now<=d['expires_at'],'expires_at')
    data=d['data'];require(type(data) is dict,'data')
    kind=d['message_type']
    if kind=='config':
        op=data.get('op');keys={'op'}
        if op=='COMPARE':
            keys|={'snapshot','digest'};require(type(data.get('snapshot')) is dict and HEX.fullmatch(str(data.get('digest',''))) and digest(data['snapshot'])==data['digest'],'digest')
        elif op in ('PROBE','PROBE_ACK'):
            keys|={'transaction_id','nonce','participant'};require(UUID.fullmatch(str(data.get('transaction_id',''))) and re.fullmatch('[0-9a-f]{32}',str(data.get('nonce',''))) and data.get('participant') in ('MASTER','GATEWAY'),'probe')
        elif op in ('SWITCH_PREPARE','SWITCH_READY','SWITCH_CONFIRM','SWITCH_COMMITTED','SWITCH_ROLLBACK'):
            keys|={'transaction_id','shared_revision','digest','participant'}
            require(UUID.fullmatch(str(data.get('transaction_id',''))) and integer(data.get('shared_revision')) and HEX.fullmatch(str(data.get('digest',''))) and data.get('participant') in ('MASTER','GATEWAY'),'switch')
            if op=='SWITCH_PREPARE':keys.add('deadline');require(integer(data.get('deadline'),1,0x7fffffffffffffff),'deadline')
        elif op=='PERSISTED':keys|={'received_message_id','status'};require(safe_id(data.get('received_message_id')) and data.get('status')=='PERSISTED','receipt')
        else:require(False,'op')
        require(set(data)==keys,'data')
    elif kind=='chat/message':
        require(set(data)=={'conversation_id','sender_id','recipient_id','text'} and text(data['conversation_id'],1,128) and data['conversation_id'].isascii() and safe_id(data['sender_id']) and safe_id(data['recipient_id']) and text(data['text'],1,2000) and len(data['text'])<=500,'chat')
    elif kind=='chat/ack':
        require({'received_message_id','conversation_id','state'}<=set(data)<={'received_message_id','conversation_id','state','error_code'} and safe_id(data.get('received_message_id')) and text(data.get('conversation_id'),1,128) and data.get('state') in ('STORED','BROKER_ACCEPTED','DELIVERED','READ','FAILED','EXPIRED'),'chat_ack')
        if 'error_code' in data:require(data['error_code'] in ('NOT_AVAILABLE','EXPIRED','QUEUE_FULL','UNAUTHORIZED','INVALID_REQUEST'),'error_code')
    elif kind=='chat/status':require(set(data)=={'recipient_id','state'} and safe_id(data['recipient_id']) and data['state'] in ('ONLINE','OFFLINE','UNKNOWN'),'chat_status')
    elif kind=='chat/command':require(set(data)=={'conversation_id','received_message_id','action'} and text(data['conversation_id'],1,128) and safe_id(data['received_message_id']) and data['action'] in ('STATUS','RETRY'),'chat_action')
    elif kind=='status' and set(data)=={'connection_state'}:require(data['connection_state']=='OFFLINE','connection_state')
    else:require(set(data)=={'packet'} and type(data['packet']) is dict and len(canonical(data['packet']).encode())<=4096,'packet')
    return d

def tls_context(profile):
    validate_profile(profile,True)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version=ssl.TLSVersion.TLSv1_2
    context.load_verify_locations(cadata=profile['ca_cert'])
    assert context.check_hostname and context.verify_mode==ssl.CERT_REQUIRED
    return context
