"""Disposable localhost Gateway + explicitly simulated Master/two Nodes. Never uses owner data."""
import argparse,getpass,hashlib,hmac,http.client,json,os,secrets,sys,tempfile,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--serve',action='store_true');parser.add_argument('--port',type=int,default=5080);parser.add_argument('--device-port',type=int,default=5081);args=parser.parse_args(argv)
 if not args.serve:parser.error('Choose --serve explicitly; software acceptance tests are tests/run_software_suite.py')
 if not (1024<=args.port<=65535 and 1024<=args.device_port<=65535 and args.port!=args.device_port):parser.error('Separate unprivileged ports required')
 password=os.environ.get('SIM_GATEWAY_ADMIN_PASSWORD')
 if not password:password=getpass.getpass('Choose a password for the disposable simulator admin (not your real Gateway password): ')
 if len(password.encode())<12:parser.error('Use at least 12 bytes for simulator login')
 os.environ['GATEWAY_ADMIN_PASSWORD']=password
 sys.path.insert(0,str(ROOT/'backend'))
 with tempfile.TemporaryDirectory(prefix='selva-simulated-') as directory:
  import database,account_settings
  database.BASE_DIR=Path(directory);database.DATA_DIR=Path(directory)/'data';database.DATABASE=database.DATA_DIR/'gateway.db';account_settings.DB=database.DATA_DIR/'accounts.sqlite3'
  import server,device_api,local_ip
  from device_simulator import SimulatedNode,SimulatedMaster
  import power_schedule
  database.DATA_DIR.mkdir(parents=True,exist_ok=True)
  # The normal account initializer consumes the chosen password; no session bypass.
  account=account_settings.connect();account.close()
  master_id='SIM-MASTER';device_api.enroll(master_id,'SIMULATED Master','MASTER')
  for i in (1,2):device_api.enroll('SIM-NODE-'+str(i),'SIMULATED Node '+str(i),'NODE',master_id,str(i))
  token=secrets.token_hex(32);key=hashlib.sha256(token.encode()).digest();local_ip.save_credential(master_id,token);local_ip.service.start(dict(bind_address='127.0.0.1',port=args.device_port))
  nodes=[SimulatedNode(identity,master_id,Path(directory)/(identity+'.json')) for identity in (master_id,'SIM-NODE-1','SIM-NODE-2')]
  def exchange(frame):
   conn=http.client.HTTPConnection('127.0.0.1',args.device_port,timeout=4)
   try:
    conn.request('GET','/api/v1/device/local-challenge',headers={'X-Device-ID':master_id});reply=conn.getresponse();challenge=json.loads(reply.read(513));nonce=challenge['nonce']
    proof=local_ip.signature(key,'LOCALIP1-TIME',master_id,nonce,str(challenge['unix_time']).encode())
    if reply.status!=200 or not hmac.compare_digest(proof,challenge['signature']):raise ValueError('SIMULATOR_CHALLENGE_FAILED')
    body=json.dumps(frame,separators=(',',':')).encode();proof=local_ip.signature(key,'LOCALIP1',master_id,nonce,body)
    conn.request('POST','/api/v1/device/local-exchange',body,{'Content-Type':'application/json','X-Device-ID':master_id,'X-Local-Nonce':nonce,'X-Local-Signature':proof});reply=conn.getresponse();raw=reply.read(6145)
    if reply.status!=200 or len(raw)>6144 or not hmac.compare_digest(local_ip.signature(key,'LOCALIP1-REPLY',master_id,nonce,raw),reply.getheader('X-Local-Signature','')):raise ValueError('SIMULATOR_EXCHANGE_FAILED')
    return json.loads(raw)
   finally:conn.close()
  master=SimulatedMaster(master_id,nodes,exchange);stop=threading.Event()
  def worker():
   announced=False;sent={};seen={}
   while not stop.wait(.5):
    try:
     if not announced:master.announce();announced=True
     if not power_schedule.remaining(nodes[0].config,time.time()):master.tick()
     now=time.monotonic()
     for node in nodes:
      if power_schedule.remaining(node.config,time.time()):continue
      if now-seen.get(node.identity,0)>=node.config['heartbeat_seconds']:master.uplink(node,'HEARTBEAT',node.status());seen[node.identity]=now
      if now-sent.get(node.identity,0)>=node.config['telemetry_seconds']:
       for sensor_kind in ('DHT11','INA219','MQ135'):master.uplink(node,'TELEMETRY',node.telemetry(sensor_kind))
       sent[node.identity]=now
    except Exception:print('SIMULATED transport interrupted; retrying without claiming delivery',flush=True);stop.wait(1)
  task=threading.Thread(target=worker,name='simulated-master-nodes',daemon=True);task.start()
  print('SIMULATION ONLY: separate temporary database; no ESP32/radio hardware; no hosted MQTT. Dashboard http://127.0.0.1:'+str(args.port),flush=True)
  try:server.socketio.run(server.app,host='127.0.0.1',port=args.port,debug=False,allow_unsafe_werkzeug=True)
  finally:stop.set();task.join(timeout=5);local_ip.service.stop()
if __name__=='__main__':main()
