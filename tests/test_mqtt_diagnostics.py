import json
import ssl
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from gateway_fixture import seed
from test_mqtt_contract import profile
import mqtt_api,mqtt_diagnostics,device_api

class FakeSocket:
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def version(self):return 'TLSv1.3'
 def getpeercert(self):return {'notAfter':'fixture-expiry'}
class FakeContext:
 def wrap_socket(self,*args,**kwargs):return FakeSocket()
class FakeInfo:
 def wait_for_publish(self,timeout):pass
 def is_published(self):return True
class FakeClient:
 authentication_reason=0
 def connect(self,*args):self.on_connect(self,None,None,self.authentication_reason,None)
 def loop_start(self):pass
 def loop_stop(self):pass
 def disconnect(self):pass
 def subscribe(self,topic,qos):self.on_subscribe(self,None,1,[1],None);return (0,1)
 def publish(self,topic,payload,qos,retain):self.on_message(self,None,SimpleNamespace(topic=topic,payload=payload,retain=False));return FakeInfo()

class MqttDiagnosticsTests(unittest.TestCase):
 def setUp(self):self.client=seed();device_api.enroll('PROBE-MASTER','Probe Master','MASTER')
 def run_probe(self,client=None,ssl_error=False):
  worker=mqtt_diagnostics.Diagnostics()
  with patch('mqtt_diagnostics.contract.tls_context',return_value=FakeContext()),patch('mqtt_diagnostics.socket.create_connection',side_effect=ssl.SSLCertVerificationError() if ssl_error else None,return_value=FakeSocket()),patch('mqtt_diagnostics.client_for',return_value=client or FakeClient()):
   worker.start(profile(),1,'PROBE-MASTER','roundtrip');worker.thread.join(3)
   self.assertFalse(worker.thread.is_alive());return worker.status()
 def test_mocked_roundtrip_is_not_master_or_acl_proof(self):
  result=self.run_probe();self.assertEqual(result['state'],'PASSED')
  for key in ('tls_verified','connack','suback','puback','loopback_received'):self.assertTrue(result[key])
  self.assertEqual(result['master_delivery'],'NOT_TESTED');self.assertEqual(result['acl_status'],'UNVERIFIED')
  self.assertNotIn('fixture-secret-not-deployment',json.dumps(result))
 def test_tls_error_fails_closed(self):
  result=self.run_probe(ssl_error=True);self.assertEqual(result['state'],'FAILED');self.assertEqual(result['error'],'TLS_VERIFICATION_FAILED');self.assertFalse(result['connack'])
 def test_wrong_credentials_are_distinct(self):
  client=FakeClient();client.authentication_reason=135
  result=self.run_probe(client);self.assertEqual(result['error'],'AUTH_FAILED');self.assertTrue(result['tls_verified']);self.assertFalse(result['puback'])
 def test_api_rejects_stale_revision_and_arbitrary_payload(self):
  store=mqtt_api.service().store;store.commission(profile());before=store.read()
  data={'expected_revision':before['revision']-1,'master_id':'PROBE-MASTER','operation':'roundtrip'}
  self.assertEqual(self.client.post('/api/mqtt/diagnostics',json=data).status_code,409)
  data['expected_revision']=before['revision'];data['password']='must-not-be-accepted'
  self.assertEqual(self.client.post('/api/mqtt/diagnostics',json=data).status_code,409);self.assertEqual(store.read(),before)
 def test_api_requires_login_role_and_csrf(self):
  self.assertEqual(self.client.post('/api/mqtt/diagnostics',json={},headers={'X-CSRF-Token':'wrong'}).status_code,403)
  with self.client.session_transaction() as session:session.clear()
  self.assertEqual(self.client.get('/api/mqtt/diagnostics').status_code,401)

 def test_invalid_json_shapes_and_master_types_are_rejected(self):
  for data in ([{}],{'expected_revision':0,'master_id':{},'operation':'tls'},{'expected_revision':0,'master_id':None,'operation':'tls'}):
   with self.subTest(data=data):self.assertEqual(self.client.post('/api/mqtt/diagnostics',json=data).status_code,409)
 def test_normal_user_cannot_trigger_broker_probe(self):
  import account_settings
  with self.client.session_transaction() as session:identity=session['account_id']
  db=account_settings.connect();old=db.execute('SELECT role FROM accounts WHERE id=?',(identity,)).fetchone()['role']
  try:
   db.execute("UPDATE accounts SET role='user' WHERE id=?",(identity,));db.commit()
   self.assertEqual(self.client.post('/api/mqtt/diagnostics',json={}).status_code,403)
  finally:db.execute('UPDATE accounts SET role=? WHERE id=?',(old,identity));db.commit();db.close()
