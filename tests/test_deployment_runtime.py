"""Deployment tests use temporary databases only; no real profile or account changes."""
import os,json,sqlite3,tempfile,unittest,sys
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from backup_manager import Backups,BackupError
from runtime_lock import InstanceLock,AlreadyRunning
import deployment_config as config
from deployment_security import install
from flask import Flask,request,jsonify
class DeploymentTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  db=sqlite3.connect(self.root/'gateway.db');db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE measurements(value TEXT)');db.execute('INSERT INTO measurements VALUES(?)',('fixture-secret-reading',));db.commit();db.close()
  (self.root/'mqtt-secrets.bin').write_bytes(b'fixture-secret-ciphertext');(self.root/'session.key').write_text('fixture-session-secret')
  self.backups=Backups(self.root,keep=2)
 def tearDown(self):self.temp.cleanup()
 def test_verified_encrypted_backup_and_preview_restore(self):
  archive=self.backups.create();self.assertNotIn(b'fixture-session-secret',archive.read_bytes());self.assertTrue(self.backups.verify(archive)['verified'])
  with closing(sqlite3.connect(self.root/'gateway.db')) as db:db.execute('DELETE FROM measurements');db.commit()
  self.assertFalse(self.backups.restore(archive)['applied'])
  with closing(sqlite3.connect(self.root/'gateway.db')) as db:self.assertEqual(db.execute('SELECT count(*) FROM measurements').fetchone()[0],0)
  self.assertTrue(self.backups.restore(archive,True)['applied'])
  with closing(sqlite3.connect(self.root/'gateway.db')) as db:self.assertEqual(db.execute('SELECT value FROM measurements').fetchone()[0],'fixture-secret-reading')
  self.assertEqual((self.root/'mqtt-secrets.bin').read_bytes(),b'fixture-secret-ciphertext')
 def test_corruption_rejected_and_running_restore_blocked(self):
  archive=self.backups.create();bad=self.root/'bad.sgwb';bad.write_bytes(archive.read_bytes()[:-10])
  with self.assertRaises(BackupError):self.backups.verify(bad)
  with InstanceLock(self.root):
   with self.assertRaises(AlreadyRunning):self.backups.restore(archive,True)
  self.assertEqual((self.root/'session.key').read_text(),'fixture-session-secret')
 def test_backup_retention_and_failure_preserve_old_archives(self):
  first=self.backups.create();self.backups.create();self.backups.create();self.assertEqual(len(list(self.backups.folder.glob('gateway-backup-*.sgwb'))),2)
  with patch('backup_manager.sqlite_bytes',side_effect=RuntimeError('fixture failure')):
   with self.assertRaises(RuntimeError):self.backups.create()
  self.assertEqual(len(list(self.backups.folder.glob('gateway-backup-*.sgwb'))),2)
 def test_restore_marker_blocks_mixed_backups(self):
  (self.root/'restore.pending.json').write_text('{}')
  with self.assertRaises(BackupError):self.backups.create()
 def test_lock_is_exclusive_and_reusable(self):
  with InstanceLock(self.root):
   with self.assertRaises(AlreadyRunning):InstanceLock(self.root).acquire()
  with InstanceLock(self.root):pass
 def test_local_config_and_unsafe_options(self):
  self.assertEqual(config.load()['host'],'127.0.0.1')
  for value in ({'host':'0.0.0.0'},{'port':True},{'mode':'proxy'},{'password':'not-allowed'},{'allowed_hosts':['*']}):
   f=self.root/'config.json';f.write_text(json.dumps(value))
   with self.assertRaises(config.DeploymentError):config.load(f)
 def test_local_security_and_private_status(self):
  app=Flask('local-fixture');app.secret_key='fixture';app.config['LOCAL_TEST_SESSION']=True
  app.get('/check')(lambda:jsonify(secure=request.is_secure,remote=request.remote_addr))
  install(app,config.load(),lambda:{'running':True})
  self.assertFalse(app.config['LOCAL_TEST_SESSION']);c=app.test_client();r=c.get('/check',headers={'X-Forwarded-Proto':'https','X-Forwarded-For':'127.0.0.1'},environ_base={'REMOTE_ADDR':'10.0.0.1'})
  self.assertFalse(r.json['secure']);self.assertEqual(r.json['remote'],'10.0.0.1');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertEqual(c.get('/check',headers={'Host':'evil.example'}).status_code,400)
 def test_retention_is_preview_and_preserves_configuration(self):
  from deployment_maintenance import retention
  db=sqlite3.connect(self.root/'gateway.db');db.execute('CREATE TABLE telemetry_values(id INTEGER PRIMARY KEY,timestamp TEXT)');db.execute("INSERT INTO telemetry_values VALUES(1,'2000-01-01T00:00:00')");db.commit();db.close()
  self.assertEqual(retention(self.root,90)['telemetry_rows_eligible'],1)
  self.assertEqual(retention(self.root,90,True)['deleted'],1)
  with closing(sqlite3.connect(self.root/'gateway.db')) as db:self.assertEqual(db.execute('SELECT count(*) FROM measurements').fetchone()[0],1)
 def test_cleanup_archives_only_unreferenced_generated_images(self):
  import importlib.util
  module_path=Path(__file__).resolve().parents[1]/'tools/cleanup_generated.py';spec=importlib.util.spec_from_file_location('cleanup_test',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  (self.root/'backend').mkdir();(self.root/'backend/server.py').write_text('# fixture');(self.root/'docs').mkdir();(self.root/'dashboard/static').mkdir(parents=True)
  (self.root/'docs/unused.png').write_bytes(b'fixture-image');(self.root/'docs/used.png').write_bytes(b'referenced');(self.root/'docs/guide.md').write_text('![used](used.png)');(self.root/'dashboard/static/logo.png').write_bytes(b'asset')
  preview=module.clean([self.root]);self.assertEqual(preview['image_count'],1);self.assertTrue((self.root/'docs/unused.png').exists())
  result=module.clean([self.root],True);self.assertEqual(result['image_count'],1);self.assertFalse((self.root/'docs/unused.png').exists());self.assertTrue((self.root/'docs/used.png').exists());self.assertTrue((self.root/'dashboard/static/logo.png').exists());self.assertTrue(Path(result['encrypted_recovery_archive']).exists())
 def test_proxy_only_trusts_configured_hop(self):
  app=Flask('proxy-fixture');app.secret_key='fixture';app.get('/check')(lambda:jsonify(secure=request.is_secure,remote=request.remote_addr))
  settings=dict(config.DEFAULTS,mode='proxy',allowed_hosts=['gateway.example.com'],trusted_proxies=['127.0.0.1/32'],public_url='https://gateway.example.com');install(app,settings,lambda:{'running':True});c=app.test_client();headers={'Host':'gateway.example.com','X-Forwarded-Proto':'https','X-Forwarded-For':'203.0.113.5','X-Forwarded-Host':'gateway.example.com'}
  self.assertEqual(c.get('/check',headers=headers,environ_base={'REMOTE_ADDR':'10.0.0.1'}).status_code,400)
  r=c.get('/check',headers=headers,environ_base={'REMOTE_ADDR':'127.0.0.1'});self.assertTrue(r.json['secure']);self.assertEqual(r.json['remote'],'203.0.113.5');self.assertIn('max-age',r.headers['Strict-Transport-Security'])
