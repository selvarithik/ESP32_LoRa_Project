"""Public non-secret device operations; hardware actions are executed only on the target."""
import ipaddress
FIELDS={
 'role':('role',0,0),'master_id':('id',0,48),'wifi_ssid':('text',1,32),'local_ip_enabled':('bool',0,0),'routing_policy':('routing',0,0),
 'device_name':('text',1,64),'enabled':('bool',0,0),'telemetry_seconds':('int',2,3600),
 'wifi_dhcp':('bool',0,0),'wifi_ip':('ipv4',0,0),'wifi_subnet':('ipv4',0,0),'wifi_gateway':('ipv4',0,0),'wifi_dns':('ipv4',0,0),'wifi_dns2':('ipv4',0,0),
 'heartbeat_seconds':('int',5,3600),
 'sleep_mode':('sleep_mode',0,0),'lora_sleep_mode':('lora_sleep_mode',0,0),
 'sleep_enabled':('bool',0,0),'sleep_start_minute':('int',0,1439),
 'sleep_duration_seconds':('int',60,86400),'sleep_days_mask':('int',1,127),'utc_offset_minutes':('int',-720,840)}
READ_COMMANDS={'PING','GET_STATUS','STATUS','DIAGNOSTICS','GET_TELEMETRY','GET_CONFIG','GET_NETWORK','WIFI_SCAN','WIFI_RECONNECT','GET_RADIO_STATUS','RADIO_TEST','GET_POWER_STATUS','RESTART','GET_CONFIGURATION','GET_CAPABILITIES','GET_SENSOR_STATUS','GET_MESH_STATUS','GET_NODE_STATUS','GET_ROUTE_INFO','REBOOT'}
ALIASES={'GET_CONFIGURATION':'GET_CONFIG','SET_CONFIGURATION':'CONFIG_UPDATE','REBOOT':'RESTART'}
COMMANDS=READ_COMMANDS|{'SET_CONFIGURATION','SET_DEVICE_NAME','CONFIG_UPDATE','SET_SLEEP_SCHEDULE','SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL'}
PRIMARY_COMMANDS=('PING','GET_STATUS','GET_CAPABILITIES','GET_CONFIG','GET_NETWORK','GET_TELEMETRY','GET_SENSOR_STATUS','GET_POWER_STATUS','GET_RADIO_STATUS','GET_MESH_STATUS','GET_NODE_STATUS','GET_ROUTE_INFO','DIAGNOSTICS','SET_DEVICE_NAME','SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL','SET_SLEEP_SCHEDULE','CONFIG_UPDATE','WIFI_SCAN','WIFI_RECONNECT','RESTART')
OPERATION_COMMANDS=('SYNC_TIME','MQTT_CONNECT','MQTT_RECONNECT','MQTT_DISCONNECT','MQTT_TEST','RADIO_INSPECT','DISCOVER_NODES','I2C_SCAN','GET_COMMAND_RESULT','RESET_DIAGNOSTIC_COUNTERS','SLEEP_NOW','CANCEL_PENDING_SLEEP')
COMMANDS |= set(OPERATION_COMMANDS)
RADIO_FIELDS={'lora_address_high':('int',0,255),'lora_address_low':('int',0,255),'lora_baud':('int',1200,115200),'lora_channel':('int',0,80),'lora_air_rate':('int',0,7),'lora_tx_power':('int',10,22),'lora_packet_bytes':('int',64,200),'lora_wor_cycle_ms':('int',500,4000),'lora_work_mode':('radio_mode',0,0),'lora_fixed_mode':('bool',0,0),'lora_rssi':('bool',0,0),'lora_lbt':('bool',0,0)}
FIELDS.update(RADIO_FIELDS)

def validate_operation(kind,payload):
 def integer(key,lo,hi):return type(payload.get(key)) is int and lo<=payload[key]<=hi
 if kind=='SYNC_TIME':valid=set(payload)=={'unix_time'} and integer('unix_time',1700000000,2147483647)
 elif kind=='GET_COMMAND_RESULT':
  import re
  valid=set(payload)=={'command_id'} and isinstance(payload.get('command_id'),str) and bool(re.fullmatch(r'[A-Za-z0-9_.:-]{1,48}',payload['command_id']))
 elif kind=='RESET_DIAGNOSTIC_COUNTERS':valid=set(payload)=={'scope','confirm'} and payload.get('scope')=='NETWORK' and payload.get('confirm') is True
 elif kind=='SLEEP_NOW':valid=set(payload)=={'duration_seconds','mode'} and integer('duration_seconds',60,86400) and payload.get('mode') in ('DEEP','LIGHT')
 elif kind=='MQTT_DISCONNECT':valid=set(payload)=={'restore_after_seconds'} and integer('restore_after_seconds',10,120)
 elif kind=='DISCOVER_NODES':valid=set(payload)=={'timeout_seconds'} and integer('timeout_seconds',5,30)
 elif kind=='I2C_SCAN':valid=set(payload)=={'confirm'} and payload.get('confirm') is True
 else:valid=not payload
 if not valid:raise ValueError('INVALID_OPERATION_ARGUMENTS')
 return dict(payload)

SLEEP_FIELDS={'sleep_mode','lora_sleep_mode','sleep_enabled','sleep_start_minute','sleep_duration_seconds','sleep_days_mask','utc_offset_minutes'}
def validate_config(data):
 if not isinstance(data,dict) or not data or set(data)-set(FIELDS):raise ValueError('UNSUPPORTED_CONFIG_FIELD')
 for key,value in data.items():
  kind,low,high=FIELDS[key]
  if kind=='radio_mode' and value not in ('NORMAL','WOR_TX','WOR_RX'):raise ValueError('INVALID_RADIO_MODE')
  if key=='lora_baud' and value not in (1200,2400,4800,9600,19200,38400,57600,115200):raise ValueError('INVALID_RADIO_BAUD')
  if key=='lora_tx_power' and value not in (10,13,17,22):raise ValueError('INVALID_RADIO_POWER')
  if key=='lora_packet_bytes' and value not in (64,128,200):raise ValueError('INVALID_RADIO_PACKET')
  if key=='lora_wor_cycle_ms' and (type(value) is not int or value%500):raise ValueError('INVALID_RADIO_WOR_CYCLE')
  if kind=='sleep_mode' and value not in ('DEEP','LIGHT'):raise ValueError('INVALID_SLEEP_MODE')
  if kind=='lora_sleep_mode' and value not in ('KEEP','DEEP'):raise ValueError('INVALID_RADIO_SLEEP_MODE')
  if kind=='role' and value not in ('MASTER','NODE'):raise ValueError('INVALID_ROLE')
  if kind=='routing' and value not in ('MASTER_ONLY','DIRECT_ONLY','DIRECT_PREFERRED'):raise ValueError('INVALID_ROUTING_POLICY')
  if kind=='id' and (not isinstance(value,str) or len(value)>48 or any(not(c.isascii() and (c.isalnum() or c in '_.:-')) for c in value)):raise ValueError('INVALID_MASTER_ID')
  if kind=='bool' and type(value) is not bool:raise ValueError('BOOLEAN_REQUIRED:'+key)
  if kind=='int' and (type(value) is not int or not low<=value<=high):raise ValueError('RANGE_ERROR:'+key)
  if kind=='ipv4' and value:
   try:ipaddress.IPv4Address(value)
   except (ValueError,TypeError):raise ValueError('INVALID_IP_ADDRESS:'+key) from None
  if kind=='ipv4' and not isinstance(value,str):raise ValueError('IP_ADDRESS_STRING_REQUIRED')
  if kind=='text' and (not isinstance(value,str) or not low<=len(value.encode())<=high or any(ord(c)<32 for c in value)):raise ValueError('INVALID_NAME')
 if data.get('wifi_dhcp') is False:
  required=('wifi_ip','wifi_subnet','wifi_gateway','wifi_dns')
  if any(k not in data for k in required) or not static_network(*(data[k] for k in required),data.get('wifi_dns2','')):raise ValueError('INVALID_STATIC_NETWORK')
 return dict(data)
def validate_command(kind,payload):
 if kind not in COMMANDS or not isinstance(payload,dict):raise ValueError('UNSUPPORTED_COMMAND')
 kind=ALIASES.get(kind,kind)
 if kind in OPERATION_COMMANDS:return validate_operation(kind,payload)
 if kind=='CONFIG_UPDATE' and 'transport_action' in payload:
  import re
  action=payload['transport_action'];keys={'transport_action','transaction_id','expected_revision'}
  if action=='prepare':keys|={'local_ip_enabled','timeout_seconds'}
  if action not in ('prepare','apply','confirm','cancel') or set(payload)!=keys or not isinstance(payload.get('transaction_id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',payload['transaction_id']) or type(payload.get('expected_revision')) is not int or not 0<=payload['expected_revision']<0xffffffff:raise ValueError('INVALID_TRANSPORT_REQUEST')
  if action=='prepare' and (type(payload.get('local_ip_enabled')) is not bool or type(payload.get('timeout_seconds')) is not int or not 30<=payload['timeout_seconds']<=180):raise ValueError('INVALID_TRANSPORT_REQUEST')
  return dict(payload)
 if kind=='SET_DEVICE_NAME':
  if set(payload)-{'device_name','expected_revision'} or 'device_name' not in payload:raise ValueError('NAME_FIELDS_ONLY')
  validate_config({'device_name':payload['device_name']})
  if 'expected_revision' in payload and (type(payload['expected_revision']) is not int or not 0<=payload['expected_revision']<0xffffffff):raise ValueError('INVALID_REVISION')
  return dict(payload)
 if kind=='PING':
  if set(payload)-{'message'} or ('message' in payload and (not isinstance(payload['message'],str) or len(payload['message'].encode())>128)):raise ValueError('INVALID_PING_ARGUMENTS')
 elif kind in READ_COMMANDS:
  if payload:raise ValueError('UNEXPECTED_ARGUMENTS')
 elif kind in ('CONFIG_UPDATE','SET_SLEEP_SCHEDULE'):
  if 'local_ip_enabled' in payload:raise ValueError('TRANSPORT_TRANSACTION_REQUIRED')
  fields={k:v for k,v in payload.items() if k!='expected_revision'};validate_config(fields)
  if set(fields)&set(RADIO_FIELDS):
   if set(fields)-set(RADIO_FIELDS):raise ValueError('RADIO_FIELDS_ONLY')
   if 'expected_revision' not in payload:raise ValueError('REVISION_REQUIRED')
  if set(fields)&{'role','master_id','wifi_ssid','local_ip_enabled','routing_policy'} and 'expected_revision' not in payload:raise ValueError('REVISION_REQUIRED')
  if kind=='SET_SLEEP_SCHEDULE' and set(fields)-SLEEP_FIELDS:raise ValueError('SCHEDULE_FIELDS_ONLY')
  if 'expected_revision' in payload and (type(payload['expected_revision']) is not int or not 0<=payload['expected_revision']<0xffffffff):raise ValueError('INVALID_REVISION')
 else:
  if set(payload)!={'seconds'} or type(payload['seconds']) is not int or not (2 if kind=='SET_TELEMETRY_INTERVAL' else 5)<=payload['seconds']<=3600:raise ValueError('INVALID_INTERVAL')
 return dict(payload)
def state(command):
 result=dict(command);result['canonical_state']={'ACK_RECEIVED':'ACKNOWLEDGED','WAITING_ACK':'SENT','EXECUTING':'ACKNOWLEDGED','RESPONSE_RECEIVED':'ACKNOWLEDGED'}.get(result['state'],result['state']);return result
def static_network(address,mask,gateway,dns,dns2=''):
 try:
  ipaddress.IPv4Address(mask)
  ip=ipaddress.IPv4Address(address);net=ipaddress.IPv4Network(address+'/'+mask,strict=False);g=ipaddress.IPv4Address(gateway)
  good=lambda a:not (a.is_multicast or a.is_unspecified or a.is_loopback or int(a)>=0xe0000000 or int(a)>>24==0)
  return net.prefixlen not in (0,32) and good(ip) and good(g) and ip!=g and g in net and ip not in (net.network_address,net.broadcast_address) and g not in (net.network_address,net.broadcast_address) and good(ipaddress.IPv4Address(dns)) and (not dns2 or good(ipaddress.IPv4Address(dns2)))
 except (ValueError,TypeError):return False


def describe_command(name):
 if name not in COMMANDS:raise ValueError('UNSUPPORTED_COMMAND')
 kind=ALIASES.get(name,name)
 mutation=kind in set(OPERATION_COMMANDS)-{'GET_COMMAND_RESULT','RADIO_INSPECT','I2C_SCAN','MQTT_TEST'} or kind in {'CONFIG_UPDATE','SET_DEVICE_NAME','SET_SLEEP_SCHEDULE','SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL','RESTART','WIFI_RECONNECT'}
 if kind=='PING':arguments={'message':{'type':'text','maximum_utf8_bytes':128,'required':False}}
 elif kind in ('SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL'):arguments={'seconds':{'type':'integer','minimum':2 if kind=='SET_TELEMETRY_INTERVAL' else 5,'maximum':3600,'required':True}}
 elif kind in ('CONFIG_UPDATE','SET_SLEEP_SCHEDULE','SET_DEVICE_NAME'):
  keys={'device_name'} if kind=='SET_DEVICE_NAME' else SLEEP_FIELDS if kind=='SET_SLEEP_SCHEDULE' else FIELDS
  arguments={k:{'type':FIELDS[k][0],'minimum':FIELDS[k][1],'maximum':FIELDS[k][2]} for k in keys}
  arguments['expected_revision']={'type':'integer','minimum':0,'maximum':0xfffffffe,'required':False}
 elif kind in OPERATION_COMMANDS:arguments=operation_arguments(kind)
 else:arguments={}
 return {'canonical_name':kind,'roles':['MASTER'] if kind.startswith('MQTT_') else ['MASTER','NODE'],'permission':'administrator','arguments':arguments,
         'handler':'NetworkService','response_statuses':['SUCCESS','FAILED','UNSUPPORTED'],
         'ack_timeout_seconds':5,'response_timeout_seconds':120 if kind in (*OPERATION_COMMANDS,'RESTART','WIFI_RECONNECT') else 30,'max_retries':3,
         'changes_configuration':kind in ('CONFIG_UPDATE','SET_DEVICE_NAME','SET_SLEEP_SCHEDULE','SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL'),
         'reboot_action':kind=='RESTART','idempotent_values':kind not in ('RESTART','WIFI_RECONNECT','MQTT_RECONNECT','MQTT_DISCONNECT','SYNC_TIME','RESET_DIAGNOSTIC_COUNTERS','SLEEP_NOW','CANCEL_PENDING_SLEEP','DISCOVER_NODES'),
         'hardware_state':'DRIVER_UNAVAILABLE' if kind=='RADIO_TEST' else 'CAPABILITY_DEPENDENT'}

def operation_arguments(kind):
 return {
 'SYNC_TIME':{'unix_time':{'type':'integer','minimum':1700000000,'maximum':2147483647,'required':True}},
 'GET_COMMAND_RESULT':{'command_id':{'type':'id','maximum':48,'required':True}},
 'RESET_DIAGNOSTIC_COUNTERS':{'scope':{'type':'enum','values':['NETWORK'],'required':True},'confirm':{'type':'boolean','required':True}},
 'SLEEP_NOW':{'duration_seconds':{'type':'integer','minimum':60,'maximum':86400,'required':True},'mode':{'type':'enum','values':['DEEP','LIGHT'],'required':True}},
 'MQTT_DISCONNECT':{'restore_after_seconds':{'type':'integer','minimum':10,'maximum':120,'required':True}},
 'DISCOVER_NODES':{'timeout_seconds':{'type':'integer','minimum':5,'maximum':30,'required':True}},
 'I2C_SCAN':{'confirm':{'type':'boolean','required':True}}}.get(kind,{})
