import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from flask import Flask
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import account_settings as accounts
import local_test_access

class LocalTestAccess(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.old=accounts.DB;accounts.DB=Path(self.folder.name)/'accounts.sqlite3'
  with patch.dict('os.environ',{'GATEWAY_ADMIN_PASSWORD':'local-fixture-initial-password'}):accounts.connect().close()
  self.app=Flask(__name__);self.app.secret_key='fixture-only';self.app.config['LOCAL_TEST_SESSION']=False;local_test_access.install(self.app);self.client=self.app.test_client()
  self.headers={'Origin':'http://localhost','X-Local-Test':'1'}
 def tearDown(self):accounts.DB=self.old;self.folder.cleanup()
 def post(self,**kw):return self.client.post(local_test_access.PATH,json={},headers=self.headers,**kw)
 def test_disabled_by_default(self):self.assertEqual(self.post().status_code,404)
 def test_expired_window_rejects_new_sessions(self):
  self.app.config.update(LOCAL_TEST_SESSION=True,LOCAL_TEST_SESSION_DEADLINE=0)
  self.assertEqual(self.post().status_code,410)
 def test_remote_host_origin_and_explicit_request(self):
  self.app.config['LOCAL_TEST_SESSION']=True
  self.assertEqual(self.post(environ_overrides={'REMOTE_ADDR':'192.168.1.8'}).status_code,403)
  self.assertEqual(self.client.post(local_test_access.PATH,json={},base_url='http://192.168.1.2',headers=self.headers).status_code,403)
  self.assertEqual(self.client.post(local_test_access.PATH,json={},headers={'Origin':'https://evil.invalid','X-Local-Test':'1'}).status_code,403)
  self.assertEqual(self.client.post(local_test_access.PATH,json={},headers={'Origin':'http://localhost'}).status_code,400)
 def test_session_uses_existing_account_without_db_change(self):
  self.app.config['LOCAL_TEST_SESSION']=True;before=accounts.DB.read_bytes()
  result=self.post();self.assertEqual(result.status_code,200)
  with self.client.session_transaction() as s:
   self.assertTrue(accounts.account_sessions.valid(s['account_sid'],s['account_id'],s['account_version'],accounts.DB))
   self.assertEqual(s['account_csrf'],result.json['csrf'])
  self.assertEqual(accounts.DB.read_bytes(),before)
 def test_must_change_account_is_not_bypassed(self):
  db=accounts.connect();db.execute('UPDATE accounts SET must_change=1');db.commit();db.close();self.app.config['LOCAL_TEST_SESSION']=True
  self.assertEqual(self.post().status_code,403)
