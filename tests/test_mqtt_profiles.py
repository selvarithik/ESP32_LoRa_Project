import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gateway_fixture import seed,server
from mqtt_store import Store
from mqtt_profiles import Catalog
from mqtt_service import Service
import mqtt_contract as contract
from test_mqtt_contract import profile
class SavedProfileTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'db.sqlite',Path(self.temp.name)/'secrets.bin');self.profile=profile();self.profile['profile_name']='Active';self.store.commission(self.profile);self.catalog=Catalog(self.store)
 def tearDown(self):self.temp.cleanup()
 def draft(self,name='Other'):
  p=dict(self.profile);p['profile_name']=name;p.pop('password');return p
 def test_save_reload_edit_and_select_only_stages(self):
  before=self.store.read();saved=self.catalog.change('save',{'catalog_revision':0,'profile':self.draft()});self.assertEqual(saved['catalog_revision'],1);self.assertNotIn('password',str(saved));self.assertEqual(Catalog(self.store).read(),saved)
  result=self.catalog.select({'catalog_revision':1,'expected_revision':before['revision'],'profile_name':'Other'});self.assertEqual(result['transaction']['state'],'PENDING');self.assertEqual(result['active'],self.store.public()['active']);self.assertEqual(self.store.read()['active'],before['active']);self.assertIsNone(result['transaction']['deadline'])
 def test_stale_confirmed_delete_and_active_protection(self):
  self.catalog.change('save',{'catalog_revision':0,'profile':self.draft('Active')})
  with self.assertRaises(contract.ContractError):self.catalog.change('delete',{'catalog_revision':1,'profile_name':'Active','confirm_profile_name':'Active'})
  self.catalog.change('save',{'catalog_revision':1,'profile':self.draft()})
  for rev,name in [(1,'Other'),(2,'wrong')]:
   with self.assertRaises(contract.ContractError):self.catalog.change('delete',{'catalog_revision':rev,'profile_name':'Other','confirm_profile_name':name})
  self.assertEqual(len(self.catalog.change('delete',{'catalog_revision':2,'profile_name':'Other','confirm_profile_name':'Other'})['profiles']),1)
 def test_catalog_bounds_tls_and_secret_fail_closed(self):
  for i in range(4):self.catalog.change('save',{'catalog_revision':i,'profile':self.draft(str(i))})
  for changes in ({'tls':False},{'password':'must-not-be-a-network-secret'},{'profile_name':'Fifth'}):
   p=self.draft();p.update(changes)
   with self.assertRaises(contract.ContractError):self.catalog.change('save',{'catalog_revision':4,'profile':p})
 def test_api_auth_csrf_and_invalid_operation(self):
  client=seed();self.assertEqual(server.app.test_client().get('/api/mqtt/profiles').status_code,401)
  self.assertEqual(client.post('/api/mqtt/profiles/save',headers={'X-CSRF-Token':'wrong'},json={}).status_code,403)
  self.assertEqual(client.get('/api/mqtt/profiles').status_code,200)
  self.assertEqual(client.post('/api/mqtt/profiles/activate',json={}).status_code,409)
 def test_runtime_connect_retains_acl_gate_and_disconnect_preserves_profile(self):
  client=seed();before=client.get('/api/mqtt').json
  response=client.post('/api/mqtt/runtime/connect',json={'expected_revision':before['revision']});self.assertEqual(response.status_code,409);self.assertEqual(response.json['error']['code'],'ACL_CONFIRMATION_REQUIRED')
  self.assertEqual(client.post('/api/mqtt/runtime/disconnect',json={'expected_revision':before['revision']}).status_code,202)
  after=client.get('/api/mqtt').json;self.assertEqual(before['revision'],after['revision']);self.assertEqual(before.get('active'),after.get('active'))
 def test_injected_client_starts_one_worker_without_network(self):
  class Fake:
   def disconnect(self):pass
   def loop_stop(self):pass
  fake=Fake();calls=[]
  def factory(p):calls.append(p['client_id']);return fake
  service=Service(self.store,True,client_factory=factory)
  with patch.object(service,'run',return_value=None):service.start();service.thread.join();
  self.assertIs(service.client,fake);self.assertEqual(calls,[self.profile['client_id']]);self.assertEqual(service.state,'connecting');service.stop()
if __name__=='__main__':unittest.main(verbosity=2)
