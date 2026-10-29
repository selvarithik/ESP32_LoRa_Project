"""Disposable database: production Gateway APIs and simulated Master/Slave packets."""
import unittest,json,tempfile,importlib
from pathlib import Path
from gateway_fixture import seed,server
import command_manager as cm,device_api as api,device_identity,device_control_contract as contract
from device_simulator import SimulatedNode,SimulatedMaster
class CommandCenterTests(unittest.TestCase):
 def setUp(self):
  self.client=seed();self.master='SIM-MASTER';self.node='SIM-SLAVE';api.enroll(self.master,'Simulation Master','MASTER');api.enroll(self.node,'Simulation Slave','NODE',self.master,'2')
 def create(self,kind='PING',args=None,**policy):
  r=self.client.post('/api/v1/commands',json=dict(node_id=self.node,command_type=kind,payload=args or {},**policy));self.assertEqual(r.status_code,201,r.json);return r.json['command']['command_id']
 def uplink(self,cid,kind='ACK',status='ACCEPTED',source=None,data=None):
  return api.ingest(self.master,api.packet(kind,source or self.node,'GATEWAY',dict(command_id=cid,status=status,data=data or {}),correlation_id=cid))
 def age_attempt(self,cid):
  with cm.command_db() as db:db.execute("UPDATE command_delivery SET last_attempt_at='2000-01-01T00:00:00' WHERE command_id=?",(cid,))
 def test_registry_metadata_matches_commands(self):
  registry=self.client.get('/api/device-controls').json['command_registry'];self.assertEqual(set(registry),set(contract.PRIMARY_COMMANDS));self.assertEqual(registry['SET_DEVICE_NAME']['roles'],['MASTER','NODE']);self.assertIn('device_name',registry['SET_DEVICE_NAME']['arguments']);self.assertNotIn('RADIO_TEST',registry)
 def test_lost_ack_response_does_not_invent_ack(self):
  cid=self.create();api.pending_commands(self.master);self.uplink(cid,'RESPONSE','SUCCESS',data={'ok':True});c=cm.get_command(cid);self.assertEqual(c['state'],'COMPLETED');self.assertIsNone(c['ack_at'])
 def test_rejected_busy_and_invalid_ack(self):
  for status in ('REJECTED','BUSY'):
   cid=self.create();api.pending_commands(self.master);self.uplink(cid,status=status);self.assertEqual(cm.get_command(cid)['state'],'FAILED')
  cid=self.create()
  with self.assertRaises(ValueError):self.uplink(cid,status='MADE_UP')
  self.assertEqual(cm.get_command(cid)['state'],'QUEUED')
 def test_retry_bytes_and_bounded_attempts(self):
  cid=self.create(max_retries=1);first=api.pending_commands(self.master)[0];self.assertEqual(api.pending_commands(self.master),[]);self.age_attempt(cid);second=api.pending_commands(self.master)[0];self.assertEqual(first,second);self.age_attempt(cid);self.assertEqual(api.pending_commands(self.master),[]);self.assertEqual(cm.get_command(cid)['state'],'TIMEOUT')
 def test_recovery_commands_default_to_explicit_recovery_budget(self):
  for kind in ('RESTART','WIFI_RECONNECT'):
   r=self.client.post('/api/v1/commands',json={'node_id':self.master,'command_type':kind,'payload':{}})
   self.assertEqual(r.status_code,201,r.json)
   self.assertEqual(r.json['command']['timeout_seconds'],120)
   self.assertEqual(cm.delivery_policy(r.json['command']['command_id'])['response_timeout_s'],120)
   self.assertEqual(contract.describe_command(kind)['response_timeout_seconds'],120)
 def test_response_deadline_is_distinct_from_total_expiry(self):
  cid=self.create();api.pending_commands(self.master);self.uplink(cid)
  with cm.command_db() as db:
   db.execute("UPDATE commands SET timeout_at='2000-01-01T00:00:00' WHERE command_id=?",(cid,))
   db.execute("UPDATE command_delivery SET response_deadline='2000-01-01T00:00:00' WHERE command_id=?",(cid,))
  self.assertFalse(cm.claim_device_dispatch(cid))
  self.assertIn('RESPONSE_TIMEOUT',cm.get_command(cid)['error'])
 def test_ack_then_response_timeout_and_late_result(self):
  cid=self.create();api.pending_commands(self.master);self.uplink(cid);self.assertEqual(api.pending_commands(self.master),[])
  with cm.command_db() as db:db.execute("UPDATE command_delivery SET response_deadline='2000-01-01T00:00:00' WHERE command_id=?",(cid,))
  api.pending_commands(self.master);self.assertEqual(cm.get_command(cid)['state'],'TIMEOUT');self.uplink(cid,'RESPONSE','SUCCESS');self.assertEqual(cm.get_command(cid)['state'],'TIMEOUT');self.assertIn('LATE_RESPONSE',[e['event_type'] for e in cm.get_command_events(cid)])
 def test_execution_failure_and_unsupported(self):
  for state in ('FAILED','UNSUPPORTED'):
   cid=self.create();self.uplink(cid);self.uplink(cid,'RESPONSE',state,data={'error':'simulated-failure'});self.assertEqual(cm.get_command(cid)['state'],'FAILED')
 def test_wrong_device_and_malformed_packet(self):
  cid=self.create();api.enroll('SIM-OTHER','Other','NODE',self.master,'3')
  with self.assertRaises(PermissionError):self.uplink(cid,source='SIM-OTHER')
  frame=api.packet('ACK',self.node,'GATEWAY',{'command_id':cid,'status':'ACCEPTED'},correlation_id=cid);frame['payload_crc32']=0
  with self.assertRaises(ValueError):api.ingest(self.master,frame)
 def test_policy_persistence_after_module_restart(self):
  cid=self.create();api.pending_commands(self.master);before=cm.delivery_policy(cid);importlib.reload(cm);self.assertEqual(cm.delivery_policy(cid),before);self.assertEqual(api.pending_commands(self.master),[])
 def test_queue_capacity_and_secret_validation(self):
  for _ in range(64):self.create()
  r=self.client.post('/api/v1/commands',json={'node_id':self.node,'command_type':'PING'});self.assertEqual(r.status_code,400);self.assertIn('COMMAND_QUEUE_FULL',r.json['error'])
  r=self.client.post('/api/commands',json={'node_id':self.node,'command_type':'CONFIG_UPDATE','payload':{'wifi_password':'fixture-private-value'}});self.assertEqual(r.status_code,400)
 def test_no_manual_fake_device_results(self):
  cid=self.create()
  for path in ('state','ack','execute','response','timeout'):self.assertEqual(self.client.post('/api/commands/'+cid+'/'+path,json={'state':'COMPLETED'}).status_code,403)
 def test_mac_alias_preserves_enrollment(self):
  api.enroll('ESP32-10777D842178','Known identity','MASTER');self.assertEqual(device_identity.hardware_mac('ESP32-10777D842178'),'78:21:84:7D:77:10')
  r=self.client.post('/api/v1/commands',json={'node_id':'78:21:84:7d:77:10','command_type':'GET_CAPABILITIES'});self.assertEqual(r.status_code,201,r.json);self.assertEqual(r.json['command']['node_id'],'ESP32-10777D842178')
  with self.assertRaises(ValueError):device_identity.hardware_mac('78:21:84:7D:ZZ:10')
 def test_expired_unknown_and_boolean_settings(self):
  cid=self.create()
  with cm.command_db() as db:db.execute("UPDATE command_delivery SET expires_at='2000-01-01T00:00:00' WHERE command_id=?",(cid,))
  self.assertEqual(api.pending_commands(self.master),[]);self.assertEqual(cm.get_command(cid)['state'],'TIMEOUT')
  for kind,args in [('BOGUS',{}),('SET_TELEMETRY_INTERVAL',{'seconds':True}),('SET_DEVICE_NAME',{'device_name':'x','enabled':True})]:
   self.assertEqual(self.client.post('/api/v1/commands',json={'node_id':self.node,'command_type':kind,'payload':args}).status_code,400)
 def test_route_failure_not_fabricated_slave_ack(self):
  cid=self.create();api.ingest(self.master,api.packet('EVENT',self.master,'GATEWAY',{'event':'COMMAND_ROUTE_FAILED','command_id':cid,'target_device_id':self.node,'error_code':'HOP_LIMIT_EXCEEDED'}));self.assertEqual(cm.get_command(cid)['state'],'FAILED');self.assertIsNone(cm.get_command(cid)['ack_at'])
 def test_concurrent_targets_duplicate_response_and_cancel(self):
  a=self.create();b=cm.create_command(self.master,'GET_STATUS',{})['command_id']
  first=api.pending_commands(self.master)[0];second=api.pending_commands(self.master)[0];self.assertEqual({first['destination'],second['destination']},{self.node,self.master})
  self.uplink(a,'RESPONSE','SUCCESS');self.uplink(a,'RESPONSE','SUCCESS');self.assertEqual(cm.get_command(a)['state'],'COMPLETED');cm.cancel_command(b);self.assertEqual(api.pending_commands(self.master),[])
 def test_master_local_ping_and_lost_ack_duplicate_execution(self):
  with tempfile.TemporaryDirectory() as folder:
   nodes=[SimulatedNode(i,self.master,Path(folder)/(i+'.json')) for i in (self.master,self.node)]
   def exchange(frame):
    reply=api.ingest(self.master,frame,transport='SIMULATED_ONLY');reply['commands']=api.pending_commands(self.master);return reply
   master=SimulatedMaster(self.master,nodes,exchange);master.announce()
   cid=cm.create_command(self.master,'PING',{})['command_id'];master.tick();self.assertEqual(cm.get_command(cid)['state'],'COMPLETED')
   cid=self.create();nodes[1].drop_ack=True;master.tick();self.assertEqual(cm.get_command(cid)['state'],'COMPLETED');self.assertIsNone(cm.get_command(cid)['ack_at'])
   a=self.create();b=cm.create_command(self.master,'GET_STATUS',{})['command_id'];master.tick();self.assertEqual(cm.get_command(a)['state'],'COMPLETED');self.assertEqual(cm.get_command(b)['state'],'COMPLETED')
   frame=api.packet('COMMAND','GATEWAY',self.node,{'command_id':'CMD-CACHED','command':'PING','arguments':{}},message_id='CMD-CACHED')
   nodes[1].receive(frame);count=nodes[1].executions;nodes[1].receive(frame);self.assertEqual(nodes[1].executions,count)
 def test_simulated_master_slave_all_registry_reads_and_persistence(self):
  with tempfile.TemporaryDirectory() as folder:
   nodes=[SimulatedNode(i,self.master,Path(folder)/(i+'.json')) for i in (self.master,self.node)]
   def exchange(frame):
    reply=api.ingest(self.master,frame,transport='SIMULATED_ONLY');reply['commands']=api.pending_commands(self.master);return reply
   master=SimulatedMaster(self.master,nodes,exchange);master.announce()
   for kind,args in [('PING',{}),('GET_STATUS',{}),('GET_TELEMETRY',{}),('GET_CONFIGURATION',{}),('GET_CAPABILITIES',{}),('GET_SENSOR_STATUS',{}),('GET_MESH_STATUS',{}),('SET_DEVICE_NAME',{'device_name':'Renamed'}),('SET_CONFIGURATION',{'telemetry_seconds':15})]:
    cid=self.create(kind,args);master.tick();self.assertEqual(cm.get_command(cid)['state'],'COMPLETED',(kind,cm.get_command(cid)))
   restored=SimulatedNode(self.node,self.master,nodes[1].path);self.assertEqual(restored.config['device_name'],'Renamed');self.assertEqual(restored.config['telemetry_seconds'],15)
if __name__=='__main__':unittest.main()
