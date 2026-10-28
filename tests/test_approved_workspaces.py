"""Rendered production pages, disposable SQLite, no physical or broker mutations."""
import unittest
from html.parser import HTMLParser
from gateway_fixture import seed
import mqtt_api
import command_manager

class IDs(HTMLParser):
 def __init__(self):super().__init__();self.ids=[]
 def handle_starttag(self,tag,attrs):
  self.ids.extend(v for k,v in attrs if k=='id')

class ApprovedWorkspacesTests(unittest.TestCase):
 def setUp(self):self.client=seed()
 def test_mqtt_page_is_read_only_and_retains_handlers(self):
  store=mqtt_api.service().store;before=store.read()
  page=self.client.get('/mqtt');self.assertEqual(page.status_code,200)
  html=page.get_data(as_text=True);parser=IDs();parser.feed(html)
  self.assertEqual(len(parser.ids),len(set(parser.ids)))
  for name in ('mqtt-form','mqtt-test','mqtt-confirm','mqtt-cancel','mqtt-connect-active','mqtt-disconnect-active','mqtt-diagnostic-result','mqtt-runtime','mqtt-topic-filter'):
   self.assertIn(name,parser.ids)
  self.assertEqual(before,store.read())
  self.assertIn('data-topic-type="command_ack"',html)
  self.assertNotIn('data-topic-type="chat/',html)
 def test_command_page_does_not_create_or_dispatch_commands(self):
  page=self.client.get('/command-center');self.assertEqual(page.status_code,200)
  parser=IDs();parser.feed(page.get_data(as_text=True))
  self.assertEqual(len(parser.ids),len(set(parser.ids)))
  for name in ('command-config-close','command-config-toggle','cmd-ack-timeout','cmd-expiry','cmd-timeout-input','cmd-retries-input','btn-send-command'):
   self.assertIn(name,parser.ids)
  self.assertEqual(self.client.get('/api/commands').json['commands'],[])
 def test_layout_keeps_authentication_and_csrf(self):
  with self.client.session_transaction() as session:session.clear()
  for route in ('/mqtt','/command-center'):
   self.assertIn(self.client.get(route).status_code,(302,401))
  self.assertEqual(self.client.post('/api/mqtt/candidate',json={}).status_code,401)
if __name__=='__main__':unittest.main()
