"""Software-only device controls and full real Gateway command/receipt persistence."""
import json,tempfile,time,unittest
from pathlib import Path
from gateway_fixture import seed,server
import database,device_api,local_ip,command_manager
import device_control_contract as contract
from device_simulator import SimulatedNode,SimulatedMaster
class DeviceControlsTests(unittest.TestCase):
 def setUp(self):
  self.client=seed();self.folder=tempfile.TemporaryDirectory();self.master_id='SIM-MASTER';device_api.enroll(self.master_id,'Sim Master','MASTER')
  device_api.enroll('SIM-NODE-1','Sim Node 1','NODE',self.master_id,'11');device_api.enroll('SIM-NODE-2','Sim Node 2','NODE',self.master_id,'12')
  self.nodes=[SimulatedNode(i,self.master_id,Path(self.folder.name)/(i+'.json')) for i in (self.master_id,'SIM-NODE-1','SIM-NODE-2')]
  def exchange(frame):
   result=device_api.ingest(self.master_id,frame,transport='SIMULATED_LOCAL_IP');result['commands']=list(device_api.pending_commands(self.master_id));return result
  self.master=SimulatedMaster(self.master_id,self.nodes,exchange);self.master.announce()
 def tearDown(self):self.folder.cleanup()
 def command(self,kind,payload=None,target='SIM-NODE-1'):
  r=self.client.post('/api/v1/commands',json={'node_id':target,'command_type':kind,'payload':payload or {}});self.assertEqual(r.status_code,201,r.json);return r.json['command']['command_id']
 def test_gateway_master_nodes_ack_execution_and_database(self):
  cid=self.command('PING');self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'COMPLETED')
  self.master.uplink(self.nodes[1],'TELEMETRY',self.nodes[1].telemetry());self.master.uplink(self.nodes[2],'TELEMETRY',self.nodes[2].telemetry())
  snapshot=self.client.get('/api/live/snapshot').json;sim=[n for n in snapshot['nodes'] if n['node_id'].startswith('SIM-')];self.assertTrue(all(n['simulated'] for n in sim));self.assertEqual(len(sim),3)
  self.assertTrue(self.client.get('/api/device-controls').json['interval_presets']==[2,5,10,30,60])
 def test_persist_interval_name_schedule_and_stale_revision(self):
  cid=self.command('CONFIG_UPDATE',{'device_name':'Workshop sensor','telemetry_seconds':2,'expected_revision':1});self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'COMPLETED')
  restored=SimulatedNode(self.nodes[1].identity,self.master_id,self.nodes[1].path);self.assertEqual(restored.config['device_name'],'Workshop sensor');self.assertEqual(restored.identity,'SIM-NODE-1');self.assertEqual(restored.config['telemetry_seconds'],2)
  cid=self.command('SET_SLEEP_SCHEDULE',{'sleep_enabled':True,'sleep_start_minute':1380,'sleep_duration_seconds':7200,'utc_offset_minutes':330,'sleep_days_mask':127,'expected_revision':1});self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'FAILED')
 def test_lost_response_duplicate_and_process_restart_no_reexecution(self):
  self.nodes[1].drop_response=True;cid=self.command('RESTART');reply=self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'ACK_RECEIVED');count=self.nodes[1].executions
  restored=SimulatedNode(self.nodes[1].identity,self.master_id,self.nodes[1].path);self.master.nodes[restored.identity]=restored;self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'ACK_RECEIVED');self.assertEqual(restored.executions,count)
  with command_manager.command_db() as db:db.execute("UPDATE command_delivery SET response_deadline='2000-01-01T00:00:00' WHERE command_id=?",(cid,))
  self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'TIMEOUT')
 def test_invalid_settings_permissions_and_wrong_target(self):
  for data in ({'telemetry_seconds':True},{'telemetry_seconds':1},{'device_name':''},{'sleep_days_mask':0},{'utc_offset_minutes':841},{'wifi_password':'never-network'}):
   self.assertEqual(self.client.post('/api/v1/commands',json={'node_id':'SIM-NODE-1','command_type':'CONFIG_UPDATE','payload':data}).status_code,400)
  self.assertEqual(server.app.test_client().get('/api/device-controls').status_code,401)
  with self.assertRaises(ValueError):self.nodes[1].receive(device_api.packet('COMMAND','GATEWAY','SIM-NODE-2',{'command_id':'BAD','command':'PING','arguments':{}}))
 def test_lost_radio_fragment_retries_without_false_ack(self):
  cid=self.command('PING');self.master.radio.drop_next=1;self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'SENT');self.assertEqual(self.nodes[1].executions,0)
  with command_manager.command_db() as db:db.execute("UPDATE command_delivery SET last_attempt_at='2000-01-01T00:00:00' WHERE command_id=?",(cid,))
  self.master.tick();self.assertEqual(command_manager.get_command(cid)['state'],'COMPLETED');self.assertEqual(self.nodes[1].executions,1);self.assertTrue(self.master.radio.status()['simulated'])
 def test_failed_sensor_does_not_create_numeric_samples(self):
  self.nodes[1].sensor_valid=False;self.master.uplink(self.nodes[1],'TELEMETRY',self.nodes[1].telemetry())
  with local_ip.connection() as db:self.assertEqual(db.execute("SELECT count(*) FROM telemetry_values WHERE node_id='SIM-NODE-1'").fetchone()[0],0)
 def test_complete_static_network_validation(self):
  invalid={'wifi_dhcp':False,'wifi_ip':'192.168.1.0','wifi_subnet':'255.255.255.0','wifi_gateway':'192.168.1.1','wifi_dns':'1.1.1.1'}
  with self.assertRaises(ValueError):contract.validate_config(invalid)
  invalid['wifi_ip']='192.168.1.20';self.assertEqual(contract.validate_config(invalid),invalid)
  self.assertEqual(self.client.post('/api/v1/commands',json={'node_id':'SIM-NODE-1','command_type':'PING','timeout_seconds':True}).status_code,400)
 def test_duplicate_json_and_untrusted_response_secrets(self):
  response=self.client.post('/api/v1/commands',data='{"node_id":"SIM-NODE-1","command_type":"PING","command_type":"RESTART"}',content_type='application/json');self.assertEqual(response.status_code,400)
  cid=self.command('PING');frame=device_api.packet('RESPONSE','SIM-NODE-1','GATEWAY',{'command_id':cid,'status':'SUCCESS','data':{'local_ip_token':'must_not_leak','nested':{'password':'must_not_leak'},'ok':True}},correlation_id=cid)
  device_api.ingest(self.master_id,frame);self.assertNotIn('must_not_leak',json.dumps(self.client.get('/api/v1/commands').json))
 def test_ipv4_validation(self):
  self.assertTrue(contract.static_network('192.168.1.20','255.255.255.0','192.168.1.1','1.1.1.1','8.8.8.8'))
  for ip,mask,g in [('192.168.1.0','255.255.255.0','192.168.1.1'),('192.168.1.2','255.0.255.0','192.168.1.1'),('192.168.1.2','255.255.255.0','192.168.2.1')]:self.assertFalse(contract.static_network(ip,mask,g,'1.1.1.1'))
if __name__=='__main__':unittest.main(verbosity=2)
