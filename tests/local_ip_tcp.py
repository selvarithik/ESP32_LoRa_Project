"""Real loopback TCP/HTTP framing and lifecycle; software peers, not ESP32 hardware."""
import hashlib,json,socket,time,unittest,http.client
from gateway_fixture import seed
import device_api,local_ip

class TcpTests(unittest.TestCase):
 def setUp(self):
  seed();token=device_api.enroll('TCP-MASTER','TCP Master','MASTER');self.key=hashlib.sha256(token.encode()).digest()
  self.service=local_ip.Service();self.service.migrate()
  local_ip.save_credential('TCP-MASTER',token)
  with socket.socket() as probe:probe.bind(('127.0.0.1',0));self.port=probe.getsockname()[1]
  self.service.start(dict(bind_address='127.0.0.1',port=self.port))
 def tearDown(self):self.service.stop()
 def nonce(self):
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=4);c.request('GET','/api/v1/device/local-challenge',headers={'X-Device-ID':'TCP-MASTER'});r=c.getresponse();self.assertEqual(r.status,200);data=json.loads(r.read());c.close();return data['nonce']
 def exchange(self,body,fragment=False):
  nonce=self.nonce();proof=local_ip.signature(self.key,'LOCALIP1','TCP-MASTER',nonce,body)
  headers=('POST /api/v1/device/local-exchange HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nX-Device-ID: TCP-MASTER\r\nX-Local-Nonce: '+nonce+'\r\nX-Local-Signature: '+proof+'\r\nContent-Length: '+str(len(body))+'\r\nConnection: close\r\n\r\n').encode();data=headers+body
  with socket.create_connection(('127.0.0.1',self.port),timeout=4) as sock:
   if fragment:
    for n in range(0,len(data),19):sock.sendall(data[n:n+19]);time.sleep(.002)
   else:sock.sendall(data)
   r=http.client.HTTPResponse(sock);r.begin();return r.status,r.read()
 def frame(self):return device_api.packet('TELEMETRY','TCP-MASTER','GATEWAY',{'valid':True,'parameters':{'temperature':24.0,'humidity':50.0}})
 def test_fragmented_combined_headers_and_packet_and_dedup(self):
  body=json.dumps(self.frame(),separators=(',',':')).encode();code,data=self.exchange(body,True);self.assertEqual(code,200);self.assertEqual(json.loads(data)['receipt'],'PERSISTED')
  self.assertTrue(json.loads(self.exchange(body)[1])['duplicate'])
  self.assertEqual(self.exchange(body+body)[0],400)
 def test_malformed_oversize_and_unauthenticated_listener(self):
  self.assertEqual(self.exchange(b'{bad')[0],400)
  self.assertEqual(self.exchange(b'x'*4097)[0],413)
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=4);c.request('POST','/api/v1/device/local-exchange',b'{}',{'Content-Type':'application/json'});r=c.getresponse();self.assertEqual(r.status,401);r.read();c.close()
 def test_stop_restart_loses_challenges_preserves_database_receipts(self):
  body=json.dumps(self.frame(),separators=(',',':')).encode();self.assertEqual(self.exchange(body)[0],200)
  old=self.nonce();self.service.stop();self.assertEqual(self.service.state,'STOPPED');self.service.start(dict(bind_address='127.0.0.1',port=self.port))
  self.assertNotIn(old,self.service.nonces);self.assertTrue(json.loads(self.exchange(body)[1])['duplicate'])
 def test_timeout_releases_single_listener_for_next_peer(self):
  with socket.create_connection(('127.0.0.1',self.port),timeout=4) as sock:
   sock.sendall(b'POST /api/v1/device/local-exchange HTTP/1.1\r\nHost: localhost\r\nContent-Length: 20\r\nContent-Type: application/json\r\n\r\n{')
   time.sleep(3.3)
  self.assertEqual(self.exchange(json.dumps(self.frame()).encode())[0],200)

if __name__=='__main__':unittest.main(verbosity=2)
