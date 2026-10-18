import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from gateway_fixture import server
import account_settings as accounts
import account_sessions

class AccessLifecycleTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.previous=accounts.DB;accounts.DB=Path(self.temp.name)/'accounts.sqlite3'
  with patch.dict(os.environ,{'GATEWAY_ADMIN_PASSWORD':'fixture-initial-password'}):accounts.connect().close()
  self.client=server.app.test_client();self.client.environ_base['REMOTE_ADDR']='fixture-'+self.id()
 def tearDown(self):
  accounts.DB=self.previous;self.temp.cleanup()
 def sign_in(self,client=None):
  c=client or self.client;c.get('/login')
  with c.session_transaction() as s:csrf=s['account_csrf']
  r=c.post('/api/auth/login',json={'username':'admin','password':'fixture-initial-password'},headers={'X-CSRF-Token':csrf})
  self.assertEqual(r.status_code,200);return {'X-CSRF-Token':r.json['csrf']}
 def test_all_pages_require_login_and_api_is_json(self):
  for path in ['/','/nodes','/sensors','/commands','/network','/communication','/firmware','/logs','/mqtt','/system','/chat','/accounts']:
   r=self.client.get(path);self.assertEqual(r.status_code,302,path);self.assertEqual(r.location,'/login')
  self.assertEqual(self.client.get('/api/mqtt').status_code,401)
  self.assertTrue(self.client.get('/api/mqtt').is_json)
  self.assertIn(b'Gateway sign in',self.client.get('/login').data)
 def test_login_csrf_bad_types_rate_limit_and_safe_redirect(self):
  self.client.get('/login')
  self.assertEqual(self.client.post('/api/auth/login',json={'username':'admin','password':'fixture-initial-password'}).status_code,403)
  h=self.sign_in();self.assertEqual(self.client.get('/login?next=https://evil.invalid').status_code,200)
  self.assertEqual(self.client.post('/api/auth/logout',headers=h).status_code,200)
  self.client.get('/login')
  with self.client.session_transaction() as s:csrf=s['account_csrf']
  for _ in range(12):r=self.client.post('/api/auth/login',json={'username':'admin','password':'wrong'},headers={'X-CSRF-Token':csrf})
  self.assertEqual(r.status_code,429)
 def test_logout_rejects_replayed_cookie(self):
  h=self.sign_in();cookie=self.client.get_cookie('session').value
  self.assertEqual(self.client.post('/api/auth/logout',headers=h).status_code,200)
  replay=server.app.test_client();replay.set_cookie('session',cookie)
  self.assertEqual(replay.get('/api/accounts').status_code,401)
 def test_logout_disconnects_existing_realtime_session(self):
  import time
  h=self.sign_in();socket=server.socketio.test_client(server.app,flask_test_client=self.client)
  self.assertTrue(socket.is_connected())
  self.assertEqual(self.client.post('/api/auth/logout',headers=h).status_code,200)
  until=time.monotonic()+2
  while socket.is_connected() and time.monotonic()<until:time.sleep(.01)
  self.assertFalse(socket.is_connected())
 def test_idle_expiry_and_secure_cookie(self):
  self.sign_in()
  with patch('account_sessions.time.monotonic',return_value=10**12):self.assertEqual(self.client.get('/api/accounts').status_code,401)
  secure=server.app.test_client();r=secure.get('/login',base_url='https://localhost')
  self.assertIn('Secure;',r.headers['Set-Cookie']);self.assertIn('HttpOnly;',r.headers['Set-Cookie']);self.assertIn('SameSite=Lax',r.headers['Set-Cookie'])
 def test_password_change_revokes_other_sessions_and_preserves_profile(self):
  h=self.sign_in();other=server.app.test_client();self.sign_in(other)
  actor=self.client.get('/api/accounts').json['user']
  r=self.client.patch('/api/accounts/'+str(actor['id']),json={'current_password':'fixture-initial-password','password':'fixture-new-password'},headers=h)
  self.assertEqual(r.status_code,200);self.assertTrue(r.json['reauthenticate'])
  self.assertEqual(other.get('/api/accounts').status_code,401);self.assertEqual(self.client.get('/api/accounts').status_code,401)
 def test_limit_permissions_and_last_creator(self):
  h=self.sign_in()
  for i in range(7):self.assertEqual(self.client.post('/api/accounts',json={'username':'user'+str(i),'name':'User','role':'user','password':'fixture-user-password'},headers=h).status_code,200)
  self.assertEqual(self.client.post('/api/accounts',json={'username':'ninth','name':'User','password':'fixture-user-password'},headers=h).status_code,409)
  self.assertEqual(self.client.patch('/api/accounts/1',json={'role':'user'},headers=h).status_code,400)
 def test_recovery_preview_and_bootstrap_are_explicit(self):
  tool=Path(accounts.__file__).with_name('recover_account.py')
  import sys
  before=accounts.DB.read_bytes()
  subprocess.run([sys.executable,str(tool),'--database',str(accounts.DB),'--user','admin'],capture_output=True,check=True)
  self.assertEqual(accounts.DB.read_bytes(),before)
  db=accounts.connect()
  try:
   row=db.execute('SELECT password_hash FROM accounts WHERE id=1').fetchone()
   db.execute("INSERT INTO accounts(username,name,role,password_hash) VALUES('other','Other','user',?)",(row['password_hash'],));db.commit()
   other=tuple(db.execute("SELECT * FROM accounts WHERE username='other'").fetchone())
  finally:db.close()
  subprocess.run([sys.executable,str(tool),'--database',str(accounts.DB),'--user','admin','--apply'],capture_output=True,check=True)
  db=accounts.connect()
  try:
   self.assertTrue(tuple(db.execute("SELECT * FROM accounts WHERE username='other'").fetchone())==other)
   self.assertEqual(db.execute('SELECT count(*) FROM accounts').fetchone()[0],2)
   self.assertEqual(db.execute("SELECT must_change FROM accounts WHERE username='admin'").fetchone()[0],1)
  finally:db.close()
  subprocess.run([sys.executable,str(tool),'--database',str(accounts.DB),'--user','other','--apply'],capture_output=True,check=True)
  db=accounts.connect()
  try:self.assertEqual(db.execute("SELECT role FROM accounts WHERE username='other'").fetchone()[0],'user')
  finally:db.close()
  fresh=Path(self.temp.name)/'new.sqlite3'
  old=accounts.DB;accounts.DB=fresh
  try:
   with patch.dict(os.environ,{'GATEWAY_ADMIN_PASSWORD':''}):
    with self.assertRaises(RuntimeError):accounts.connect()
   db=sqlite3.connect(fresh)
   try:self.assertEqual(db.execute('SELECT count(*) FROM accounts').fetchone()[0],0)
   finally:db.close()
  finally:accounts.DB=old
  subprocess.run([sys.executable,str(tool),'--database',str(fresh),'--bootstrap','--apply'],capture_output=True,check=True)
  old=accounts.DB;accounts.DB=fresh
  try:
   c=server.app.test_client();c.get('/login')
   with c.session_transaction() as s:csrf=s['account_csrf']
   r=c.post('/api/auth/login',json={'username':'admin','password':'admin'},headers={'X-CSRF-Token':csrf})
   self.assertEqual(r.json['redirect'],'/accounts');self.assertEqual(c.get('/').location,'/accounts')
   self.assertEqual(c.post('/api/nodes',json={},headers={'X-CSRF-Token':r.json['csrf']}).status_code,403)
   changed=c.patch('/api/accounts/'+str(r.json['user']['id']),json={'current_password':'admin','password':'fixture-bootstrap-replaced'},headers={'X-CSRF-Token':r.json['csrf']})
   self.assertEqual(changed.status_code,200);self.assertTrue(changed.json['reauthenticate'])
   c.get('/login')
   with c.session_transaction() as s:csrf=s['account_csrf']
   self.assertEqual(c.post('/api/auth/login',json={'username':'admin','password':'admin'},headers={'X-CSRF-Token':csrf}).status_code,401)
   login=c.post('/api/auth/login',json={'username':'admin','password':'fixture-bootstrap-replaced'},headers={'X-CSRF-Token':csrf})
   self.assertEqual(login.status_code,200);self.assertEqual(login.json['redirect'],'/')
   self.assertEqual(login.json['user']['must_change'],0)
  finally:accounts.DB=old
 def test_mqtt_refresh_is_read_only(self):
  self.sign_in()
  import mqtt_api
  service=mqtt_api.service();revision=service.store.read()['revision'];client=service.client
  with patch.object(service,'start') as start,patch.object(service,'enqueue') as enqueue:
   for _ in range(3):self.assertEqual(self.client.get('/api/mqtt').status_code,200)
   start.assert_not_called();enqueue.assert_not_called()
  self.assertEqual(service.store.read()['revision'],revision);self.assertIs(service.client,client)
 def test_mqtt_subscription_readiness_requires_all_qos_one_grants(self):
  import json
  from mqtt_store import Store
  from mqtt_service import Service
  service=Service(Store(Path(self.temp.name)/'mqtt.db',Path(self.temp.name)/'secret.bin'),False)
  service.profile=json.loads((Path(accounts.__file__).resolve().parents[1]/'deployment/profile.example.json').read_text())
  class Client:
   mid=0
   def subscribe(self,*a,**kw):self.mid+=1;return 0,self.mid
  c=Client();service.on_connect(c,None,None,136,None)
  self.assertEqual(service.last_error,'CONNECTION_REFUSED');self.assertEqual(service.status()['authentication_state'],'UNKNOWN')
  service.on_connect(c,None,None,134,None);self.assertEqual(service.last_error,'AUTH_FAILED')
  service.on_connect(c,None,None,0,None)
  self.assertEqual(service.status()['subscription_state'],'SUBSCRIPTION_PENDING')
  service.on_subscribe(c,None,1,[128],None);self.assertEqual(service.last_error,'SUBSCRIPTION_REJECTED')
  for mid in range(1,len(service.SUBSCRIPTIONS)+1):service.on_subscribe(c,None,mid,[1],None)
  self.assertEqual(service.status()['subscription_state'],'READY')
  service.on_disconnect(c,None,None,0,None);self.assertEqual(service.status()['subscription_state'],'UNKNOWN')

if __name__=='__main__':unittest.main()
