"""Single-process Windows/local deployment entry point. No device provisioning."""
import argparse,importlib.util,json,logging,logging.handlers,os,signal,socket,sqlite3,sys,threading,time,uuid,webbrowser
from pathlib import Path
from deployment_config import load,DeploymentError
from runtime_paths import data_dir
from runtime_lock import InstanceLock,AlreadyRunning
from backup_manager import Backups,BackupError,atomic_json

class RuntimeErrorCode(RuntimeError):pass

def read_state(root):
 try:return json.loads((Path(root)/'runtime/status.json').read_text(encoding='utf-8'))
 except (OSError,ValueError):return {'running':False,'state':'STOPPED'}

def running(root):
 try:
  with InstanceLock(root):return False
 except AlreadyRunning:return True

def preflight(root,settings):
 root=Path(root).resolve()
 if (root/'restore.pending.json').exists():raise RuntimeErrorCode('RESTORE_RECOVERY_REQUIRED')
 if os.environ.get('GATEWAY_MQTT_TRUST_ACL')=='1':raise RuntimeErrorCode('UNSCOPED_MQTT_ACL_OVERRIDE_NOT_ALLOWED')
 if not (root/'gateway.db').is_file() or not (root/'accounts.sqlite3').is_file():raise RuntimeErrorCode('EXISTING_DATA_REQUIRED_USE_DATA_DIR_OR_RESTORE')
 try:
  db=sqlite3.connect((root/'accounts.sqlite3').as_uri()+'?mode=ro',uri=True)
  try:
   if db.execute('SELECT count(*) FROM accounts').fetchone()[0]<1:raise RuntimeErrorCode('ACCOUNT_SETUP_REQUIRED')
  finally:db.close()
 except sqlite3.Error:raise RuntimeErrorCode('ACCOUNT_STORE_UNAVAILABLE') from None
 if importlib.util.find_spec('waitress') is None:raise RuntimeErrorCode('INSTALL_REQUIREMENTS_DEPLOYMENT')
 return {'configuration_valid':True,'mode':settings['mode'],'host':settings['host'],'port':settings['port'],'local_testing_disabled':True,'realtime_transport':'SOCKET_IO_HTTP_POLLING','existing_data_found':True}

class Runtime:
 def __init__(self,root,settings,open_browser=False):
  self.root=Path(root).resolve();self.settings=settings;self.open_browser=open_browser;self.stop_event=threading.Event();self.backups=Backups(root,settings['backup_keep']);self.worker=None;self.http=None;self.http_thread=None;self.heartbeat=None;self.started=False;self.run_id=uuid.uuid4().hex;self.server_module=None
 def status(self):
  mqtt={"state":"NOT_STARTED","worker_alive":False}
  if self.worker:mqtt={'state':self.worker.state,'worker_alive':bool(self.worker.thread and self.worker.thread.is_alive()),'last_error':self.worker.last_error,'queued':self.worker.outgoing.qsize()}
  local={'state':'NOT_STARTED'}
  if self.server_module:local={'state':self.server_module.local_ip.service.state,'error':self.server_module.local_ip.service.error}
  return {'running':self.started,'state':'RUNNING' if self.started else 'STOPPED','pid':os.getpid(),'run_id':self.run_id,'mode':self.settings['mode'],'host':self.settings['host'],'port':self.settings['port'],'realtime_transport':'SOCKET_IO_HTTP_POLLING','mqtt':mqtt,'local_ip':local,'backup':dict(self.backups.status),'local_test_access':False}
 def stop(self):self.stop_event.set()
 def log(self,event):logging.getLogger('gateway.deployment').info(event)
 def serve(self):
  with InstanceLock(self.root):
   preflight(self.root,self.settings)
   # Bind before importing/startup services to avoid a second MQTT worker when an old server owns the port.
   with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
    try:probe.bind((self.settings['host'],self.settings['port']))
    except OSError:raise RuntimeErrorCode('PORT_IN_USE_NO_WORKERS_STARTED') from None
   self.root.joinpath('logs').mkdir(parents=True,exist_ok=True)
   handler=logging.handlers.RotatingFileHandler(self.root/'logs/gateway.log',maxBytes=2*1024*1024,backupCount=5,encoding='utf-8');handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'));logger=logging.getLogger('gateway.deployment');logger.setLevel(logging.INFO);logger.addHandler(handler)
   try:
    if self.backups.due(self.settings['backup_hours']):self.backups.create()
    os.environ['GATEWAY_DATA_DIR']=str(self.root);os.environ['GATEWAY_DEPLOYMENT_MODE']=self.settings['mode'];os.environ.pop('GATEWAY_LOCAL_TEST_SESSION',None)
    import server
    self.server_module=server
    from deployment_security import install
    install(server.app,self.settings,self.status)
    from waitress import create_server
    self.http=create_server(server.app,host=self.settings['host'],port=self.settings['port'],threads=self.settings['threads'],connection_limit=100,channel_timeout=30,asyncore_loop_timeout=.5,clear_untrusted_proxy_headers=True)
    server.account_settings.connect().close()
    server.local_ip.start_saved()
    import mqtt_adapter
    self.worker=mqtt_adapter.start_from_environment()
    self.heartbeat=server.socketio.start_background_task(server.server_time_heartbeat,self.stop_event)
    self.http_thread=threading.Thread(target=self.http.run,name='gateway-http',daemon=True);self.http_thread.start();self.started=True;atomic_json(self.root/'runtime/status.json',self.status());self.backups.start(self.settings['backup_hours']);self.log('GATEWAY_STARTED')
    if self.open_browser:webbrowser.open(self.settings['public_url'] or 'http://'+self.settings['host']+':'+str(self.settings['port']))
    stop_file=self.root/'runtime'/('stop-'+self.run_id+'.request')
    while not self.stop_event.wait(.5):
     if not self.http_thread.is_alive():raise RuntimeErrorCode('HTTP_WORKER_STOPPED')
     if stop_file.exists():stop_file.unlink();self.stop_event.set();break
     atomic_json(self.root/'runtime/status.json',self.status())
   finally:
    self.started=False;self.stop_event.set();self.backups.stop()
    if self.worker:self.worker.stop()
    if self.server_module:
     self.server_module.local_ip.service.stop()
     self.server_module.socketio.server.shutdown()
    if self.http:
     def close_http():
      from waitress import wasyncore
      wasyncore.close_all(map=self.http._map)
     try:self.http.trigger.pull_trigger(close_http)
     except Exception:self.http.close()
     self.http.task_dispatcher.shutdown(cancel_pending=True,timeout=5)
    if self.http_thread:self.http_thread.join(timeout=5)
    atomic_json(self.root/'runtime/status.json',self.status());self.log('GATEWAY_STOPPED');logger.removeHandler(handler);handler.close()

def cli(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('command',nargs='?',default='serve',choices=['serve','status','stop','check','backup','verify-backup','restore','maintenance'])
 parser.add_argument('--data-dir',type=Path);parser.add_argument('--config',type=Path);parser.add_argument('--archive',type=Path);parser.add_argument('--apply',action='store_true');parser.add_argument('--retention-days',type=int,default=90);parser.add_argument('--no-browser',action='store_true')
 args=parser.parse_args(argv);root=(args.data_dir or data_dir()).resolve()
 try:
  settings=load(args.config)
  if args.command=='serve':
   runtime=Runtime(root,settings,not args.no_browser)
   for event in (signal.SIGINT,signal.SIGTERM):signal.signal(event,lambda *_:runtime.stop())
   runtime.serve();return 0
  if args.command=='status':result=read_state(root);result['running']=running(root)
  elif args.command=='stop':
   result=read_state(root)
   if running(root):
    run=result.get('run_id','')
    if not isinstance(run,str) or len(run)!=32 or any(c not in '0123456789abcdef' for c in run):raise RuntimeErrorCode('CONTROL_STATE_UNAVAILABLE')
    (root/'runtime'/('stop-'+run+'.request')).write_text('stop',encoding='ascii')
    for _ in range(40):
     if not running(root):break
     time.sleep(.5)
    if running(root):raise RuntimeErrorCode('STOP_TIMEOUT_NO_PROCESS_WAS_KILLED')
   result={'running':False,'state':'STOPPED'}
  elif args.command=='check':result=preflight(root,settings)
  elif args.command=='backup':result={'backup':Backups(root,settings['backup_keep']).create().name,'verified':True,'encrypted':True}
  elif args.command in ('verify-backup','restore'):
   if not args.archive:raise RuntimeErrorCode('ARCHIVE_REQUIRED')
   manager=Backups(root,settings['backup_keep']);result=manager.verify(args.archive) if args.command=='verify-backup' else manager.restore(args.archive,args.apply)
  else:
   from deployment_maintenance import retention
   result=retention(root,args.retention_days,args.apply)
  print(json.dumps(result,indent=2));return 0
 except (DeploymentError,RuntimeErrorCode,AlreadyRunning,BackupError) as error:print(json.dumps({'ok':False,'error':str(error)}));return 1
 except Exception as error:print(json.dumps({'ok':False,'error':'OPERATION_FAILED','type':type(error).__name__}));return 1
