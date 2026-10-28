"""Permanent command scope: isolated production storage and real ingress handlers."""
import json,time,unittest
from unittest.mock import patch
from gateway_fixture import seed
import device_api,command_manager as cm,mqtt_api,mqtt_contract as contract,mqtt_runtime_policy as policy
from mqtt_service import Service,message,command_message
from test_mqtt_contract import profile

class CommandScopeTests(unittest.TestCase):
 def setUp(self):
  seed();device_api.enroll('MQTT-MASTER','Master','MASTER');self.store=mqtt_api.service().store;self.store.commission(profile())
  self.service=Service(self.store,commands_only=True);self.service.profile=profile();self.service.state='connected';self.service.subscriptions_ready=set(self.service.SUBSCRIPTIONS)
 def test_periodic_dispatch_does_not_wait_for_sensor_packets(self):
  c=cm.create_command('MQTT-MASTER','PING',{});self.service.dispatch_commands();wire=self.service.outgoing.get_nowait();self.assertEqual(wire['message_type'],'command');self.assertEqual(wire['message_id'],c['command_id'])
  self.service.dispatch_commands();self.assertTrue(self.service.outgoing.empty())
  self.assertEqual(cm.get_command(c['command_id'])['state'],'SENT')
 def test_waits_for_all_subscriptions_and_queue_space(self):
  c=cm.create_command('MQTT-MASTER','PING',{});self.service.subscriptions_ready.clear();self.service.dispatch_commands();self.assertEqual(cm.get_command(c['command_id'])['state'],'QUEUED')
  self.service.subscriptions_ready=set(self.service.SUBSCRIPTIONS)
  for i in range(23):self.service.enqueue(message(profile(),'MQTT-MASTER','config',{}))
  self.service.dispatch_commands();self.assertEqual(cm.get_command(c['command_id'])['state'],'QUEUED')
 def test_ack_is_separate_from_execution_response(self):
  c=cm.create_command('MQTT-MASTER','PING',{});self.service.dispatch_commands();self.service.outgoing.get_nowait()
  for kind,status,data in [('ACK','ACCEPTED',{}),('RESPONSE','SUCCESS',{'ok':True})]:
   packet=device_api.packet(kind,'MQTT-MASTER','GATEWAY',{'command_id':c['command_id'],'status':status,'data':data},correlation_id=c['command_id']);wire=message(profile(),'MQTT-MASTER','command_ack',{'packet':packet});wire['device_id']='MQTT-MASTER'
   self.service.handle(contract.topic(profile(),'command_ack'),contract.canonical(wire));reply=self.service.outgoing.get_nowait();self.assertEqual(reply['data']['op'],'PERSISTED')
   self.assertEqual(cm.get_command(c['command_id'])['state'],'ACK_RECEIVED' if kind=='ACK' else 'COMPLETED')
 def test_chat_is_excluded_and_retry_wire_is_stable(self):
  self.assertNotIn('chat/message',self.service.SUBSCRIPTIONS)
  with self.assertRaises(contract.ContractError):self.service.enqueue(message(profile(),'MQTT-MASTER','chat/message',{}))
  packet=device_api.packet('COMMAND','GATEWAY','MQTT-MASTER',{'command_id':'CMD-T','command':'PING','arguments':{}},message_id='CMD-T')
  a=command_message(profile(),'MQTT-MASTER',packet)
  with patch('mqtt_service.time.time',return_value=time.time()+10):b=command_message(profile(),'MQTT-MASTER',packet)
  self.assertEqual(contract.canonical(a),contract.canonical(b))
 def test_command_proof_is_bound_and_requires_telemetry_proof(self):
  proof={'schema_version':1,'scope':'TELEMETRY_COMMANDS','binding':policy.binding(self.store),'tls_verified':True,'command_puback':True,'command_ack_suback_qos1':True,'master_ack_persisted':True,'master_response_persisted':True}
  path=self.store.database.parent/'mqtt-command-authorization.json';path.write_text(json.dumps(proof),encoding='utf-8')
  self.assertFalse(policy.command_authorized(self.store))
  telemetry={'schema_version':1,'scope':'TELEMETRY_ONLY','binding':policy.binding(self.store),'tls_verified':True,'suback_qos1':True,'telemetry_persisted':True,'status_persisted':True,'config_reply_puback':True}
  (path.parent/'mqtt-telemetry-authorization.json').write_text(json.dumps(telemetry),encoding='utf-8');self.assertTrue(policy.command_authorized(self.store))
  proof['command_ack_suback_qos1']=False;path.write_text(json.dumps(proof),encoding='utf-8');self.assertFalse(policy.command_authorized(self.store))
  proof['command_ack_suback_qos1']=True;proof['binding']={};path.write_text(json.dumps(proof),encoding='utf-8');self.assertFalse(policy.command_authorized(self.store))
if __name__=='__main__':unittest.main()
