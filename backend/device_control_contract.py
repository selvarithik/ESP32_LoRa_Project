"""Public non-secret device operations; hardware actions are executed only on the target."""
import ipaddress
FIELDS={
 'device_name':('text',1,64),'enabled':('bool',0,0),'telemetry_seconds':('int',2,3600),
 'wifi_dhcp':('bool',0,0),'wifi_ip':('ipv4',0,0),'wifi_subnet':('ipv4',0,0),'wifi_gateway':('ipv4',0,0),'wifi_dns':('ipv4',0,0),'wifi_dns2':('ipv4',0,0),
 'heartbeat_seconds':('int',5,3600),
 'sleep_enabled':('bool',0,0),'sleep_start_minute':('int',0,1439),
 'sleep_duration_seconds':('int',60,86400),'sleep_days_mask':('int',1,127),'utc_offset_minutes':('int',-720,840)}
READ_COMMANDS={'PING','GET_STATUS','STATUS','DIAGNOSTICS','GET_TELEMETRY','GET_CONFIG','GET_NETWORK','WIFI_SCAN','WIFI_RECONNECT','GET_RADIO_STATUS','RADIO_TEST','GET_POWER_STATUS','RESTART'}
COMMANDS=READ_COMMANDS|{'CONFIG_UPDATE','SET_SLEEP_SCHEDULE','SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL'}
SLEEP_FIELDS={'sleep_enabled','sleep_start_minute','sleep_duration_seconds','sleep_days_mask','utc_offset_minutes'}
def validate_config(data):
 if not isinstance(data,dict) or not data or set(data)-set(FIELDS):raise ValueError('UNSUPPORTED_CONFIG_FIELD')
 for key,value in data.items():
  kind,low,high=FIELDS[key]
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
 if kind=='PING':
  if set(payload)-{'message'} or ('message' in payload and (not isinstance(payload['message'],str) or len(payload['message'].encode())>128)):raise ValueError('INVALID_PING_ARGUMENTS')
 elif kind in READ_COMMANDS:
  if payload:raise ValueError('UNEXPECTED_ARGUMENTS')
 elif kind in ('CONFIG_UPDATE','SET_SLEEP_SCHEDULE'):
  fields={k:v for k,v in payload.items() if k!='expected_revision'};validate_config(fields)
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
