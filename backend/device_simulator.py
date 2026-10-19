"""Explicit software-only Master/Node model. Uses production packets and Gateway ingress."""
import hashlib,json,time
from pathlib import Path
import device_api
import device_control_contract as control
import power_schedule
from radio_model import SimulatedRadio

class SimulatedNode:
 def __init__(self,identity,master_id,storage):
  self.identity=identity;self.master_id=master_id;self.path=Path(storage);self.path.parent.mkdir(parents=True,exist_ok=True)
  self.config={'device_name':identity,'telemetry_seconds':10,'heartbeat_seconds':30,'enabled':True,'sleep_enabled':False,'sleep_start_minute':0,'sleep_duration_seconds':3600,'sleep_days_mask':127,'utc_offset_minutes':330,'wifi_dhcp':True,'wifi_ip':'','wifi_subnet':'255.255.255.0','wifi_gateway':'','wifi_dns':'','wifi_dns2':''}
  self.revision=1;self.executions=0;self.cache={};self.sensor_valid=True;self.drop_ack=False;self.drop_response=False
  if self.path.exists():
   state=json.loads(self.path.read_text(encoding='utf-8'));self.config=state['config'];self.revision=state['revision'];self.executions=state['executions'];self.cache=state['cache']
 def save(self):
  temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(dict(config=self.config,revision=self.revision,executions=self.executions,cache=self.cache)),encoding='utf-8');temp.replace(self.path)
 def status(self):return dict(device_id=self.identity,device_name=self.config['device_name'],master_id=self.master_id,role='MASTER' if self.identity==self.master_id else 'NODE',heartbeat_seconds=self.config['heartbeat_seconds'],configuration_revision=self.revision,simulated=True)
 def telemetry(self,kind='DHT11'):
  samples={'DHT11':{'temperature':24.5,'humidity':55.0},'INA219':{'bus_voltage':12.0,'shunt_voltage':10.0,'current':0.1,'power':1.2},'MQ135':{'mq135_adc_raw':1200,'mq135_pin_mv':900}}
  return dict(valid=self.sensor_valid,parameters=samples[kind] if self.sensor_valid else {},sensor_type=kind,sensor_id=self.identity+'-SIMULATED-'+kind,status='SIMULATED_RAW_ONLY' if self.sensor_valid else 'READ_ERROR',simulated=True,sampled_uptime_ms=2000)
 def receive(self,frame):
  body=device_api.validate_packet(frame)
  if frame['type']!='COMMAND' or frame['destination']!=self.identity or frame['source'] not in ('GATEWAY',self.master_id):raise ValueError('WRONG_TARGET_OR_SOURCE')
  if body.get('command_id')!=frame['message_id'] or not isinstance(body.get('arguments'),dict):raise ValueError('INVALID_COMMAND')
  if frame['timestamp']<int(time.time())-60 or frame['timestamp']>int(time.time())+30:raise ValueError('EXPIRED_COMMAND')
  identity=frame['source']+':'+frame['message_id'];request=hashlib.sha256(frame['payload'].encode()).hexdigest()
  if identity in self.cache:
   record=self.cache[identity]
   if record['request']!=request:raise ValueError('COMMAND_ID_CONFLICT')
  else:
   kind=body['command'];args=body['arguments'];ok=True
   try:
    control.validate_command(kind,args)
    if 'expected_revision' in args and args['expected_revision']!=self.revision:raise ValueError('REVISION_CONFLICT')
    self.executions+=1
    if kind in ('CONFIG_UPDATE','SET_SLEEP_SCHEDULE'):
     self.config.update({k:v for k,v in args.items() if k!='expected_revision'});self.revision+=1;result={'saved':True,'configuration_revision':self.revision,'restart_required':any(k.startswith('wifi_') for k in args)}
    elif kind in ('SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL'):
     self.config['telemetry_seconds' if kind=='SET_TELEMETRY_INTERVAL' else 'heartbeat_seconds']=args['seconds'];self.revision+=1;result={'saved':True,'configuration_revision':self.revision}
    elif kind in ('PING',):result={'ok':True}
    elif kind in ('STATUS','GET_STATUS'):result=self.status()
    elif kind=='GET_CONFIG':result=dict(self.config,configuration_revision=self.revision,config_scope='RUNTIME')
    elif kind=='GET_TELEMETRY':result=self.telemetry()
    elif kind=='RESTART':result={'restarted':True,'reset_reason':'SIMULATED_SOFTWARE_RESET'}
    elif kind=='GET_POWER_STATUS':result=dict(self.config,state='SIMULATED_SLEEPING' if power_schedule.remaining(self.config,time.time()) else 'SIMULATED_ACTIVE',sleep_remaining_seconds=power_schedule.remaining(self.config,time.time()),remote_wake_supported=False)
    elif kind in ('GET_RADIO_STATUS','RADIO_TEST'):result={'state':'SIMULATED_RADIO','physical_driver_available':False}
    elif kind in ('GET_NETWORK','WIFI_SCAN','WIFI_RECONNECT'):result={'state':'SIMULATED_NETWORK','internet_status':'UNKNOWN','gateway_reachable':True,'results':[]}
    else:result={'state':'SIMULATED_DIAGNOSTICS'}
   except ValueError as error:ok=False;result={'error':str(error)}
   result['simulated']=True
   cid=frame['message_id'];ack=device_api.packet('ACK',self.identity,'GATEWAY',{'command_id':cid,'status':'RECEIVED'},correlation_id=cid)
   response=device_api.packet('RESPONSE',self.identity,'GATEWAY',{'command_id':cid,'status':'SUCCESS' if ok else 'FAILED','data':result},correlation_id=cid)
   record={'request':request,'ack':ack,'response':response};self.cache[identity]=record
   while len(self.cache)>32:del self.cache[next(iter(self.cache))]
   self.save()
  return ([] if self.drop_ack else [record['ack']])+([] if self.drop_response else [record['response']])

class SimulatedMaster:
 def __init__(self,identity,nodes,exchange):self.radio=SimulatedRadio();self.identity=identity;self.nodes={n.identity:n for n in nodes};self.exchange=exchange;self.forwarded=0;self.lost=0
 def uplink(self,node,kind,body):
  frame=device_api.packet(kind,node.identity,'GATEWAY',body)
  if node.identity!=self.identity:frame=self.radio.transfer(frame,node.identity,self.identity)
  return self.exchange(frame) if frame else {'accepted':False,'commands':[],'error':'SIMULATED_RADIO_LOSS'}
 def announce(self):
  for node in self.nodes.values():self.uplink(node,'HELLO',node.status())
 def tick(self):
  master=self.nodes[self.identity];reply=self.uplink(master,'STATUS',master.status())
  for frame in reply.get('commands',[]):
   node=self.nodes.get(frame['destination'])
   if not node:continue
   if node.identity!=self.identity:frame=self.radio.transfer(frame,self.identity,node.identity)
   if frame is None:self.lost+=1;continue
   for response in node.receive(frame):
    if node.identity!=self.identity:response=self.radio.transfer(response,node.identity,self.identity)
    if response is not None:self.exchange(response);self.forwarded+=1
  return reply
