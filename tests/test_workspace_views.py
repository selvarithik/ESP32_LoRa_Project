import json
import unittest
from gateway_fixture import seed,server
import database,device_api,command_manager
import workspace_views

class WorkspaceViewsTests(unittest.TestCase):
 def setUp(self):
  self.client=seed();self.master='ESP32-010203040506';self.node='ESP32-060504030201'
  device_api.enroll(self.master,'Actual Master','MASTER');device_api.enroll(self.node,'Saved Node','NODE',self.master,'4')
 def test_supported_navigation_routes_remain_available(self):
  paths=[]
  for item in workspace_views.NAVIGATION:
   if item['label']=='Existing tools':continue
   paths.extend(child['path'] for child in item.get('children',[item]))
  for path in paths:
   with self.subTest(path=path):self.assertEqual(self.client.get(path).status_code,200)
 def test_overview_is_authenticated_and_does_not_invent_rf(self):
  data=self.client.get('/api/operations/overview').json
  self.assertEqual(data['rf_observed_links'],[]);self.assertEqual(data['registered_nodes'],1)
  self.assertEqual(data['parent_relationship_basis'],'CONFIGURED_NOT_RF_VERIFIED')
  self.assertNotIn('password',json.dumps(data).lower())
  with self.client.session_transaction() as session:session.clear()
  self.assertEqual(self.client.get('/api/operations/overview').status_code,401)
 def test_nested_command_projection_excludes_secrets(self):
  command=command_manager.create_command(self.master,'GET_RADIO_STATUS',{})
  db=database.get_connection()
  try:
   db.execute("UPDATE commands SET state='COMPLETED',result=?,response_at='2026-10-25T12:00:00' WHERE command_id=?",(json.dumps({'state':'DISABLED','observed':{'channel':17,'password':'fixture-private-value'},'token':'fixture-private-value'}),command['command_id']));db.commit()
  finally:db.close()
  raw=self.client.get('/api/operations/overview').get_data(as_text=True)
  self.assertNotIn('fixture-private-value',raw);self.assertNotIn('password',raw);self.assertIn('channel',raw)
 def test_malformed_historical_status_is_unknown(self):
  db=database.get_connection()
  try:db.execute("UPDATE nodes SET latest_status='invalid-json' WHERE node_id=?",(self.master,));db.commit()
  finally:db.close()
  self.assertEqual(self.client.get('/api/operations/overview').status_code,200)
 def test_dashboard_removes_only_recent_logs_component(self):
  html=self.client.get('/').get_data(as_text=True)
  self.assertNotIn('id="widget-activity"',html);self.assertIn('Live Telemetry / All Nodes',html)
  self.assertEqual(self.client.get('/api/logs').status_code,200)
 def test_login_retains_security_controls_and_local_assets(self):
  html=self.client.get('/login').get_data(as_text=True)
  for text in ('id="login-form"','data-csrf=','autocomplete="current-password"','AEROSPACE &amp; DEFENSE','id="feedback"'):self.assertIn(text,html)
  self.assertNotIn('https://fonts',html);self.assertNotIn('value="admin"',html)

 def test_duplicate_mac_alias_and_case_variant_are_rejected(self):
  from device_identity import hardware_mac
  self.assertEqual(hardware_mac(self.master.lower()),hardware_mac(self.master))
  for alias in (hardware_mac(self.master),self.master.lower()):
   with self.subTest(alias=alias):
    with self.assertRaisesRegex(ValueError,'Hardware MAC already enrolled'):device_api.enroll(alias,'Duplicate','MASTER')
 def test_editable_name_does_not_change_hardware_identity(self):
  before=self.client.get('/api/operations/overview').json
  db=database.get_connection()
  try:db.execute('UPDATE nodes SET name=? WHERE node_id=?',('Saved display name',self.master));db.commit()
  finally:db.close()
  after=self.client.get('/api/operations/overview').json
  a=next(n for n in before['devices'] if n['node_id']==self.master);b=next(n for n in after['devices'] if n['node_id']==self.master)
  self.assertEqual(a['hardware_mac'],b['hardware_mac']);self.assertEqual(b['name'],'Saved display name')

 def test_legacy_add_route_cannot_duplicate_hardware(self):
  import node_manager
  from device_identity import hardware_mac
  with self.assertRaisesRegex(ValueError,'Hardware MAC already enrolled'):
   node_manager.add_node(hardware_mac(self.master),'Duplicate','ESP32','ESP32-WROOM-32','test','test','Wi-Fi',{},'')
