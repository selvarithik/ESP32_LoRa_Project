"""Isolated real Gateway API/database tests. Device responses below are simulated, not RF evidence."""
import json
import unittest
from unittest.mock import patch
from gateway_fixture import seed, server
import command_manager
import device_api
import device_control_contract as control
import transport_switch as switch

class TransportSwitchTests(unittest.TestCase):
 def setUp(self):
  self.client=seed();switch.ATTEMPTS.clear();self.device='SIM-MASTER-SWITCH'
  device_api.enroll(self.device,'Switch Master','MASTER')
  device_api.ingest(self.device,device_api.packet('HELLO',self.device,'GATEWAY',dict(device_id=self.device,device_name='Switch Master',role='MASTER',master_id=self.device,heartbeat_seconds=30,configuration_revision=7)))
  self.url='/api/v1/devices/'+self.device+'/transport'
 def post(self,operation,**data):
  return self.client.post(self.url,json=dict(operation=operation,admin_password='fixture-only-admin-123',**data))
 def prepare(self):
  r=self.post('prepare',local_ip_enabled=True,expected_revision=7,timeout_seconds=90)
  self.assertEqual(r.status_code,202,r.json);return r.json
 def reply(self,doc,op,data,transport='mqtt',ack=True):
  cid=doc['commands'][op]
  if ack:device_api.ingest(self.device,device_api.packet('ACK',self.device,'GATEWAY',{'command_id':cid,'status':'ACCEPTED'},correlation_id=cid),transport=transport)
  device_api.ingest(self.device,device_api.packet('RESPONSE',self.device,'GATEWAY',{'command_id':cid,'status':'SUCCESS','data':data},correlation_id=cid),transport=transport)
 def prepared(self):
  doc=self.prepare();self.reply(doc,'prepare',dict(transaction_id=doc['transaction_id'],state='PREPARED',configuration_revision=7))
  return self.client.get(self.url).json
 def trial(self):
  doc=self.prepared();doc=self.post('apply',transaction_id=doc['transaction_id']).json
  import time
  self.reply(doc,'apply',dict(transaction_id=doc['transaction_id'],state='TRIAL',configuration_revision=7,deadline=int(time.time())+90))
  return self.client.get(self.url).json
 def test_password_transport_and_api_bypass_rejected(self):
  self.assertEqual(self.client.post(self.url,json=dict(operation='prepare',admin_password='wrong')).status_code,409)
  r=self.client.post(self.url,json=dict(operation='prepare',admin_password='fixture-only-admin-123'),environ_overrides={'REMOTE_ADDR':'192.168.1.2'})
  self.assertEqual(r.status_code,409)
  r=self.client.post('/api/v1/commands',json=dict(node_id=self.device,command_type='CONFIG_UPDATE',payload=dict(transport_action='apply',transaction_id='TX-x',expected_revision=7)))
  self.assertEqual(r.status_code,400)
  with self.assertRaises(ValueError):control.validate_command('CONFIG_UPDATE',dict(local_ip_enabled=True,expected_revision=7))
 def test_staging_durable_no_secret_or_early_apply(self):
  doc=self.prepare();cid=doc['commands']['prepare'];c=command_manager.get_command(cid)
  self.assertNotIn('password',json.dumps(c));self.assertNotIn('fixture-only-admin-123',json.dumps(c))
  self.assertEqual(self.post('apply',transaction_id=doc['transaction_id']).status_code,409)
  self.assertEqual(switch.load(self.device)['transaction_id'],doc['transaction_id'])
 def test_stale_revision_and_wrong_target_rejected(self):
  self.assertEqual(self.post('prepare',local_ip_enabled=True,expected_revision=6,timeout_seconds=90).status_code,409)
  device_api.enroll('SIM-SLAVE-SWITCH','Slave','NODE',self.device)
  self.assertEqual(self.client.post('/api/v1/devices/SIM-SLAVE-SWITCH/transport',json=dict(operation='prepare',admin_password='fixture-only-admin-123',local_ip_enabled=True,expected_revision=0,timeout_seconds=90)).status_code,409)
 def test_complete_flow_requires_actual_ingress_path(self):
  doc=self.trial();tx=doc['transaction_id']
  self.assertEqual(self.post('confirm',transaction_id=tx).status_code,409)
  doc=self.post('probe',transaction_id=tx).json
  self.reply(doc,'probe',dict(ok=True,path_verified=True,transaction_id=tx,transport='IP'),transport='local-ip')
  # Refreshed state survives a coordinator re-read (process-local state is not authoritative).
  self.assertTrue(switch.proof(switch.refreshed(self.device)))
  doc=self.post('confirm',transaction_id=tx).json
  self.reply(doc,'confirm',dict(transaction_id=tx,state='COMMITTED',configuration_revision=8),transport='local-ip')
  self.assertEqual(self.client.get(self.url).json['state'],'COMMITTED')
 def test_forged_path_missing_ack_and_expiry_fail_closed(self):
  doc=self.trial();tx=doc['transaction_id'];doc=self.post('probe',transaction_id=tx).json
  self.reply(doc,'probe',dict(ok=True,path_verified=True,transaction_id=tx,transport='IP',gateway_verified_transport='IP'),transport='mqtt',ack=False)
  self.assertFalse(switch.proof(switch.refreshed(self.device)))
  self.assertEqual(self.post('confirm',transaction_id=tx).status_code,409)
  with patch('transport_switch.time.time',return_value=10**11):self.assertEqual(switch.refreshed(self.device)['state'],'EXPIRED_AWAITING_DEVICE_STATUS')
 def test_sleep_modes_and_exact_primary_registry(self):
  for mode in ('LIGHT','DEEP'):control.validate_command('SET_SLEEP_SCHEDULE',dict(sleep_mode=mode,lora_sleep_mode='DEEP'))
  with self.assertRaises(ValueError):control.validate_command('SET_SLEEP_SCHEDULE',dict(sleep_mode='MODEM'))
  registry=self.client.get('/api/device-controls').json
  self.assertEqual(len(registry['commands']),21);self.assertEqual(set(registry['commands']),set(control.PRIMARY_COMMANDS))
 def test_cancel_is_queued_not_fake_rollback(self):
  doc=self.prepared();r=self.post('cancel',transaction_id=doc['transaction_id'])
  self.assertEqual(r.json['state'],'CANCEL_QUEUED')
  self.reply(r.json,'cancel',dict(transaction_id=doc['transaction_id'],state='CANCELLED',configuration_revision=7))
  self.assertEqual(self.client.get(self.url).json['state'],'CANCELLED')
 def test_device_report_reconciles_autonomous_rollback(self):
  doc=self.trial();tx=doc['transaction_id']
  status=dict(device_id=self.device,device_name='Switch Master',role='MASTER',master_id=self.device,heartbeat_seconds=30,configuration_revision=7,transport_switch=dict(transaction_id=tx,state='ROLLED_BACK',configuration_revision=7))
  device_api.ingest(self.device,device_api.packet('STATUS',self.device,'GATEWAY',status),transport='mqtt')
  self.assertEqual(self.client.get(self.url).json['state'],'ROLLED_BACK')

if __name__=='__main__':unittest.main()
