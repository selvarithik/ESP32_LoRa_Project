"""Real loopback HTTP/Socket.IO lifecycle using temporary data; no broker/devices."""
import argparse,subprocess,tempfile,sqlite3,json,os,time,socket,re,sys,http.cookiejar
from pathlib import Path
from urllib.request import build_opener,HTTPCookieProcessor,Request
from urllib.error import HTTPError,URLError
from werkzeug.security import generate_password_hash
ROOT=Path(__file__).resolve().parents[1]
def main(executable=None):
 with tempfile.TemporaryDirectory(prefix='gateway-runtime-smoke-') as temp:
  root=Path(temp);data=root/'data';data.mkdir();db=sqlite3.connect(data/'gateway.db');db.execute('CREATE TABLE fixture_marker(value TEXT)');db.commit();db.close()
  db=sqlite3.connect(data/'accounts.sqlite3');db.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT UNIQUE,name TEXT,role TEXT,password_hash TEXT,version INTEGER DEFAULT 1,must_change INTEGER DEFAULT 0)');db.execute('INSERT INTO accounts VALUES(1,?,?,?,?,1,0)',('admin','Fixture','creator',generate_password_hash('fixture-deployment-only-123')));db.commit();db.close()
  with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
  config=root/'config.json';config.write_text(json.dumps({'port':port}));base='http://127.0.0.1:'+str(port)
  prefix=[str(executable)] if executable else [sys.executable,str(ROOT/'tools/gateway.py')]
  common=['--data-dir',str(data),'--config',str(config)];env=dict(os.environ,GATEWAY_LOCAL_TEST_SESSION='1');env.pop('GATEWAY_MQTT_TRUST_ACL',None)
  cookies=http.cookiejar.CookieJar();browser=build_opener(HTTPCookieProcessor(cookies))
  def request(path,body=None,headers=None):
   r=Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
   try:
    with browser.open(r,timeout=8) as response:return response.status,response.read().decode(),response.headers
   except HTTPError as response:return response.code,response.read().decode(),response.headers
  with tempfile.TemporaryFile() as log:
   process=subprocess.Popen(prefix+['serve',*common,'--no-browser'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
   try:
    for _ in range(100):
     if process.poll() is not None:raise AssertionError('Runtime exited before readiness')
     try:
      if request('/healthz')[0]==200:break
     except (URLError,TimeoutError):pass
     time.sleep(.2)
    else:raise AssertionError('Runtime readiness timeout')
    assert request('/api/status')[0]==401
    assert request('/api/auth/local-test-session',{}, {'Origin':base,'X-Local-Test':'1'})[0]==404
    html=request('/login')[1];csrf=re.search(r'data-csrf="([^"]+)"',html)[1]
    assert request('/api/auth/login',{'username':'admin','password':'fixture-deployment-only-123'},{'X-CSRF-Token':csrf})[0]==200
    status=json.loads(request('/api/deployment/status')[1]);assert status['running'] and status['local_test_access'] is False
    assert request('/static/css/dashboard.css')[0]==200
    # Actual Engine.IO HTTP-polling handshake; no WebSocket upgrade is advertised.
    code,payload,_=request('/socket.io/?EIO=4&transport=polling');assert code==200 and payload.startswith('0');hello=json.loads(payload[1:]);assert hello['upgrades']==[];sid=hello['sid']
    url=base+'/socket.io/?EIO=4&transport=polling&sid='+sid
    with browser.open(Request(url,data=b'40',headers={'Content-Type':'text/plain'}),timeout=8) as response:assert response.status==200
    with browser.open(url,timeout=8) as response:assert '40' in response.read().decode()
    with browser.open(url,timeout=8) as response:assert 'server_time' in response.read().decode()
    duplicate=subprocess.run(prefix+['serve',*common,'--no-browser'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=20);assert duplicate.returncode==1 and 'GATEWAY_ALREADY_RUNNING' in duplicate.stdout
    backups=list((data/'backups').glob('*.sgwb'));assert backups
    verify=subprocess.run(prefix+['verify-backup',*common,'--archive',str(backups[0])],cwd=ROOT,capture_output=True,text=True,timeout=20);assert verify.returncode==0,verify.stdout
    stop=subprocess.run(prefix+['stop',*common],cwd=ROOT,capture_output=True,text=True,timeout=30);assert stop.returncode==0,stop.stdout;assert process.wait(timeout=15)==0
    print('PASS '+('frozen EXE' if executable else 'source')+': production HTTP, normal login/CSRF, test bypass disabled, Socket.IO polling events, single instance, encrypted backup verify, clean stop; no broker/device connections.')
   except BaseException:
    log.seek(0);print(log.read().decode('utf-8',errors='replace')[-2500:]);raise
   finally:
    if process.poll() is None:process.terminate();process.wait(timeout=10)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--executable',type=Path);a=p.parse_args();main(a.executable)
