"""Telemetry-mode isolation, using disposable Gateway storage."""
import unittest
from gateway_fixture import seed
import database,device_api,command_manager,mqtt_api,mqtt_contract as contract
from mqtt_service import Service,message
from test_mqtt_contract import profile

class TelemetryModeTests(unittest.TestCase):
 def setUp(self):
  seed();device_api.enroll('MQTT-MASTER','Master','MASTER')
  self.service=Service(mqtt_api.service().store,telemetry_only=True);self.service.profile=profile()
 def test_real_ingestion_persists_and_does_not_dispatch_pending_command(self):
  command=command_manager.create_command('MQTT-MASTER','PING',{})
  packet=device_api.packet('TELEMETRY','MQTT-MASTER','GATEWAY',{'valid':True,'parameters':{'temperature':21.5,'humidity':45}})
  envelope=message(profile(),'MQTT-MASTER','telemetry',{'packet':packet},packet['message_id']);envelope['device_id']='MQTT-MASTER'
  self.service.handle(contract.topic(profile(),'telemetry'),contract.canonical(envelope))
  reply=self.service.outgoing.get_nowait();self.assertEqual(reply['data']['op'],'PERSISTED');self.assertTrue(self.service.outgoing.empty())
  self.assertEqual(command_manager.get_command(command['command_id'])['state'],'QUEUED')
  self.service.handle(contract.topic(profile(),'telemetry'),contract.canonical(envelope));self.assertEqual(self.service.outgoing.get_nowait(),reply)
 def test_outbound_commands_are_rejected_in_telemetry_mode(self):
  with self.assertRaises(contract.ContractError):self.service.enqueue(message(profile(),'MQTT-MASTER','command',{}))
  self.assertTrue(self.service.outgoing.empty())

class TelemetryAuthorizationTests(unittest.TestCase):
 def setUp(self):
  seed();self.store=mqtt_api.service().store;self.store.commission(profile());self.path=self.store.database.parent/'mqtt-telemetry-authorization.json'
 def test_authorization_is_bound_to_profile_and_credential_reference(self):
  import json,mqtt_runtime_policy as policy
  proof={'schema_version':1,'scope':'TELEMETRY_ONLY','binding':policy.binding(self.store),'tls_verified':True,'suback_qos1':True,'telemetry_persisted':True,'status_persisted':True,'config_reply_puback':True}
  self.path.write_text(json.dumps(proof),encoding='utf-8');self.assertTrue(policy.authorized(self.store))
  self.store.change(self.store.read()['revision'],lambda s:s.update(active_secret_ref='changed-reference'))
  self.assertFalse(policy.authorized(self.store))
  proof['binding']=policy.binding(self.store);self.path.write_text(json.dumps(proof),encoding='utf-8');self.assertTrue(policy.authorized(self.store))
  self.store.change(self.store.read()['revision'],lambda s:s['active'].update(host='changed.example'))
  self.assertFalse(policy.authorized(self.store))
 def test_partial_or_corrupt_proof_fails_closed(self):
  import json,mqtt_runtime_policy as policy
  self.path.write_text('{}',encoding='utf-8');self.assertFalse(policy.authorized(self.store))
  self.path.write_text('invalid',encoding='utf-8');self.assertFalse(policy.authorized(self.store))
