import unittest,socket,sys,importlib.util
from pathlib import Path
from unittest.mock import patch
from gateway_fixture import seed,server
import mqtt_api,device_control_contract as controls,local_ip
from mqtt_explorer import Feed
from test_mqtt_contract import profile

class CompletionWorkTests(unittest.TestCase):
 def setUp(self):self.client=seed()
 def test_remote_connectivity_settings_require_revision_and_reject_credentials(self):
  for fields in ({'role':'NODE'},{'wifi_ssid':'Bench'},{'local_ip_enabled':True}):
   with self.assertRaises(ValueError):controls.validate_command('CONFIG_UPDATE',fields)
   self.assertEqual(controls.validate_command('CONFIG_UPDATE',{**fields,'expected_revision':1}),{**fields,'expected_revision':1})
  for fields in ({'role':'SLAVE','expected_revision':1},{'wifi_password':'fixture-secret','expected_revision':1},{'routing_policy':'bogus','expected_revision':1}):
   with self.assertRaises(ValueError):controls.validate_command('CONFIG_UPDATE',fields)
 def test_feed_bounded_and_never_contains_raw_payload(self):
  feed=Feed();p=profile()
  for i in range(205):feed.record(p,{'message_type':'telemetry','message_id':str(i),'device_id':'MASTER','data':{'packet':{'payload':{'password':'fixture-secret','current':1.0,'status':'OK'}}}})
  data=feed.read();self.assertEqual(len(data['messages']),200);self.assertNotIn('fixture-secret',str(data));self.assertNotIn('password',str(data));self.assertEqual(len(feed.read(204)['messages']),1)
 def test_explorer_auth_and_no_profile_mutation(self):
  store=mqtt_api.service().store;before=store.read();self.assertEqual(self.client.get('/api/mqtt/explorer').status_code,200);self.assertEqual(before,store.read())
  self.assertEqual(server.app.test_client().get('/api/mqtt/explorer').status_code,401)
  self.assertEqual(self.client.get('/api/mqtt/explorer?after=bad').status_code,400)
  self.assertEqual(self.client.post('/api/mqtt/explorer/probe',json={'master_id':'NO','expected_revision':0},headers={'X-CSRF-Token':'wrong'}).status_code,403)
  self.assertEqual(self.client.post('/api/mqtt/explorer/probe',json={'master_id':'NO','expected_revision':0}).status_code,409)
 def test_bind_error_distinguishes_unassigned_address(self):
  service=local_ip.Service();error=OSError(10049,'fixture')
  with patch('local_ip.socket.socket') as factory:
   factory.return_value.__enter__.return_value.bind.side_effect=error
   with self.assertRaises(ValueError):service.start({'bind_address':'192.0.2.2','port':5001})
  self.assertEqual(service.error,'BIND_FAILED');self.assertEqual(service.bind_failure_reason,'ADDRESS_NOT_ASSIGNED')
 def test_calibration_arithmetic_requires_real_inputs_and_does_not_write(self):
  spec=importlib.util.spec_from_file_location('calibration',Path(__file__).resolve().parents[1]/'tools/mq135_calibration.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  result=m.calculate(1000,2,5000,10000,100,100,-1);self.assertAlmostEqual(result['rs_ohms'],15000);self.assertAlmostEqual(result['r0_ohms'],15000);self.assertFalse(result['device_settings_written'])
  for pin in (0,3000,float('nan')):
   with self.assertRaises(ValueError):m.calculate(pin,2,5000,10000,100,100,-1)
