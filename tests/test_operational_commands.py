"""Production Gateway endpoints and MQTT ingress; disposable DB/network fixtures only."""
import unittest,json,time
from gateway_fixture import seed,server
import device_api as api,command_manager as cm,device_control_contract as control,mqtt_api,mqtt_contract as mqtt
from mqtt_service import Service,message
from test_mqtt_contract import profile
VALID={'SYNC_TIME':{'unix_time':1800000000},'MQTT_CONNECT':{},'MQTT_RECONNECT':{},'MQTT_DISCONNECT':{'restore_after_seconds':30},'MQTT_TEST':{},'RADIO_INSPECT':{},'DISCOVER_NODES':{'timeout_seconds':5},'I2C_SCAN':{'confirm':True},'GET_COMMAND_RESULT':{'command_id':'CMD-OLD'},'RESET_DIAGNOSTIC_COUNTERS':{'scope':'NETWORK','confirm':True},'SLEEP_NOW':{'duration_seconds':60,'mode':'LIGHT'},'CANCEL_PENDING_SLEEP':{}}
class OperationalCommandTests(unittest.TestCase):
 def setUp(self):
  self.c=seed();self.device='OPS-MASTER';api.enroll(self.device,'Operational fixture','MASTER')
 def submit(self,name,args=None):return self.c.post('/api/v1/commands',json={'node_id':self.device,'command_type':name,'payload':VALID[name] if args is None else args})
 def test_extension_catalog_does_not_change_primary_ui(self):
  catalog=self.c.get('/api/device-controls').json
  self.assertEqual(len(catalog['commands']),21);self.assertEqual(set(catalog['operational_commands']),set(VALID))
  self.assertEqual(catalog['operational_registry']['MQTT_CONNECT']['roles'],['MASTER'])
 def test_all_extensions_queue_ack_and_final_result_separately(self):
  for name in VALID:
   with self.subTest(name=name):
    response=self.submit(name);self.assertEqual(response.status_code,201,response.json);cid=response.json['command']['command_id']
    self.assertEqual(cm.get_command(cid)['state'],'QUEUED')
    api.pending_commands(self.device)
    api.ingest(self.device,api.packet('ACK',self.device,'GATEWAY',{'command_id':cid,'status':'ACCEPTED'},correlation_id=cid))
    self.assertEqual(cm.get_command(cid)['state'],'ACK_RECEIVED')
    packet=api.packet('RESPONSE',self.device,'GATEWAY',{'command_id':cid,'status':'FAILED','data':{'error':'FIXTURE_HARDWARE_UNAVAILABLE'}},correlation_id=cid)
    api.ingest(self.device,packet);api.ingest(self.device,packet)
    self.assertEqual(cm.get_command(cid)['state'],'FAILED')
 def test_malformed_and_secret_fields_are_rejected(self):
  for name in VALID:
   with self.subTest(name=name):
    self.assertEqual(self.submit(name,dict(VALID[name],password='fixture-rejected')).status_code,400)
  for name,args in [('SYNC_TIME',{'unix_time':True}),('SLEEP_NOW',{'mode':'LIGHT','duration_seconds':1}),('MQTT_DISCONNECT',{}),('I2C_SCAN',{'confirm':False}),('DISCOVER_NODES',{'timeout_seconds':31})]:self.assertEqual(self.submit(name,args).status_code,400)
 def test_unauthenticated_and_missing_csrf_are_rejected(self):
  anon=server.app.test_client();self.assertEqual(anon.post('/api/v1/commands',json={'node_id':self.device,'command_type':'MQTT_CONNECT'}).status_code,401)
  self.assertEqual(self.c.post('/api/v1/commands',json={'node_id':self.device,'command_type':'MQTT_CONNECT'},headers={'X-CSRF-Token':'wrong'}).status_code,403)
 def test_queued_only_cancellation_and_dispatched_refusal(self):
  cid=self.submit('MQTT_TEST').json['command']['command_id'];url='/api/v1/devices/'+self.device+'/commands/'+cid+'/cancel-queued'
  reply=self.c.post(url,json={});self.assertEqual(reply.status_code,200,reply.json);self.assertFalse(reply.json['device_execution_cancelled'])
  cid=self.submit('MQTT_TEST').json['command']['command_id'];api.pending_commands(self.device)
  self.assertEqual(self.c.post('/api/v1/devices/'+self.device+'/commands/'+cid+'/cancel-queued',json={}).status_code,409)
 def test_radio_staging_validation_is_exclusive_and_revisioned(self):
  for args in ({'lora_channel':4},{'lora_channel':4,'expected_revision':1,'wifi_ssid':'forbidden-mix'},{'lora_tx_power':30,'expected_revision':1},{'lora_enabled':True,'expected_revision':1}):
   self.assertEqual(self.c.post('/api/v1/commands',json={'node_id':self.device,'command_type':'CONFIG_UPDATE','payload':args}).status_code,400)
  self.assertEqual(self.c.post('/api/v1/commands',json={'node_id':self.device,'command_type':'CONFIG_UPDATE','payload':{'lora_channel':4,'expected_revision':1}}).status_code,201)
 def test_mqtt_test_receipt_is_actual_ingress_persistence(self):
  store=mqtt_api.service().store;store.commission(profile());service=Service(store,commands_only=True);service.profile=profile();service.state='connected'
  status={'device_id':self.device,'device_name':'Fixture','role':'MASTER','master_id':self.device,'heartbeat_seconds':30,'configuration_revision':0}
  packet=api.packet('STATUS',self.device,'GATEWAY',status);wire=message(profile(),self.device,'status',{'packet':packet});wire['device_id']=self.device
  service.handle(mqtt.topic(profile(),'status'),mqtt.canonical(wire));receipt=service.outgoing.get_nowait()
  self.assertEqual(receipt['data']['op'],'PERSISTED');self.assertEqual(receipt['data']['received_message_id'],packet['message_id'])
  with api.connect() as db:self.assertTrue(db.execute('SELECT latest_status FROM nodes WHERE node_id=?',(self.device,)).fetchone()['latest_status'])
 def test_power_transition_status_is_receipted_by_scoped_worker(self):
  store=mqtt_api.service().store;store.commission(profile());service=Service(store,commands_only=True);service.profile=profile();service.state='connected'
  self.assertIn('status',service.SUBSCRIPTIONS);self.assertNotIn('events',service.SUBSCRIPTIONS)
  data={'device_id':self.device,'device_name':'Fixture','role':'MASTER','master_id':self.device,'heartbeat_seconds':30,'configuration_revision':0,'operating_state':'RESTART_DRAINING','event':'POWER_TRANSITION_INTENT'}
  packet=api.packet('STATUS',self.device,'GATEWAY',data);wire=message(profile(),self.device,'status',{'packet':packet});wire['device_id']=self.device
  service.handle(mqtt.topic(profile(),'status'),mqtt.canonical(wire));receipt=service.outgoing.get_nowait()
  self.assertEqual(receipt['data']['op'],'PERSISTED');self.assertEqual(receipt['data']['received_message_id'],packet['message_id'])
