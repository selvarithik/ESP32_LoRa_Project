import json
import unittest
from contextlib import contextmanager
from gateway_fixture import seed
import database,device_api,telemetry_manager

@contextmanager
def connection():
 db=database.get_connection()
 try:
  with db:yield db
 finally:db.close()

class EffectiveFreshnessTests(unittest.TestCase):
 def setUp(self):
  self.client=seed();device_api.enroll('CADENCE-MASTER','Cadence Master','MASTER')
  device_api.ingest('CADENCE-MASTER',device_api.packet('STATUS','CADENCE-MASTER','GATEWAY',{'device_id':'CADENCE-MASTER','role':'MASTER','master_id':'CADENCE-MASTER','heartbeat_seconds':30,'telemetry_seconds':10,'configuration_revision':1}))
  device_api.ingest('CADENCE-MASTER',device_api.packet('TELEMETRY','CADENCE-MASTER','GATEWAY',{'sensor_type':'DHT11','valid':True,'parameters':{'temperature':25,'humidity':50}}))
 def row(self):return next(x for x in telemetry_manager.get_latest_values('CADENCE-MASTER') if x['parameter_id']=='temperature')
 def saved(self):
  with connection() as db:return [tuple(x) for x in db.execute("SELECT parameter_id,widget_config FROM sensor_parameters WHERE node_id='CADENCE-MASTER' ORDER BY parameter_id")]
 def test_api_uses_reported_cadence_without_changing_saved_configuration(self):
  before=self.saved();response=self.client.get('/api/nodes/CADENCE-MASTER/parameters/latest');self.assertEqual(response.status_code,200)
  row=next(x for x in response.json['parameters'] if x['parameter_id']=='temperature')
  self.assertEqual(row['expected_transmission_seconds'],10);self.assertEqual(row['effective_stale_timeout_s'],25)
  self.assertEqual(row['widget_config']['stale_timeout'],10);self.assertEqual(self.saved(),before)
 def test_longer_explicit_timeout_is_preserved(self):
  with connection() as db:db.execute("UPDATE sensor_parameters SET widget_config=? WHERE node_id='CADENCE-MASTER' AND parameter_id='temperature'",(json.dumps({'stale_timeout':120}),))
  self.assertEqual(self.row()['effective_stale_timeout_s'],120)
 def test_invalid_reported_interval_does_not_expand_timeout(self):
  for value in (None,True,'10',0,3601):
   with self.subTest(value=value):
    with connection() as db:db.execute("UPDATE nodes SET latest_status=? WHERE node_id='CADENCE-MASTER'",(json.dumps({'telemetry_seconds':value}),))
    row=self.row();self.assertIsNone(row['expected_transmission_seconds']);self.assertEqual(row['effective_stale_timeout_s'],10)
 def test_legacy_nodes_keep_existing_timeout(self):
  with connection() as db:db.execute("UPDATE nodes SET device_enrolled=0 WHERE node_id='CADENCE-MASTER'")
  self.assertEqual(self.row()['effective_stale_timeout_s'],10)
