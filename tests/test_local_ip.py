"""Local IP unit/API tests; disposable data only, no EMQX or physical devices."""
import copy
import hashlib
import json
import time
import unittest
from unittest.mock import patch
from gateway_fixture import seed, server
import database
import device_api
import local_ip

class LocalIpTests(unittest.TestCase):
    def setUp(self):
        self.client=seed()
        self.token=device_api.enroll('IP-MASTER','IP Master','MASTER')
        self.key=hashlib.sha256(self.token.encode()).digest()
        self.service=local_ip.Service();self.service.migrate();self.peer=self.service.app.test_client()
        local_ip.save_credential('IP-MASTER',self.token)
    def tearDown(self):self.service.stop()
    def test_saved_bind_failure_keeps_dashboard_and_settings_available(self):
        with local_ip.connection() as db:
            settings=self.service.settings();settings['enabled']=True
            db.execute('UPDATE local_ip_settings SET document=? WHERE id=1',(json.dumps(settings),))
        for failure in (OSError('address unavailable'),SystemExit(1)):
            with self.subTest(failure=type(failure).__name__),patch.object(local_ip,'service',self.service),patch.object(local_ip,'make_server',side_effect=failure):
                self.assertFalse(local_ip.start_saved())
                self.assertEqual(self.service.state,'FAILED')
                self.assertEqual(self.service.error,'BIND_FAILED')
                self.assertIsNone(self.service.server)
                self.assertEqual(self.service.settings(),settings)
                response=self.client.get('/')
                self.assertEqual(response.status_code,200)
                self.assertIn(b'Open Local IP settings',response.data)
    def test_saved_listener_disabled_and_unexpected_failure(self):
        with patch.object(local_ip,'service',self.service),patch.object(self.service,'start') as start:
            self.assertFalse(local_ip.start_saved());start.assert_not_called()
            with local_ip.connection() as db:
                settings=self.service.settings();settings['enabled']=True
                db.execute('UPDATE local_ip_settings SET document=? WHERE id=1',(json.dumps(settings),))
            start.side_effect=ValueError('UNEXPECTED_CONFIGURATION_ERROR')
            with self.assertRaisesRegex(ValueError,'UNEXPECTED_CONFIGURATION_ERROR'):local_ip.start_saved()
    def frame(self,kind='TELEMETRY',source='IP-MASTER',body=None):
        if body is None:body={'valid':True,'parameters':{'temperature':25.5,'humidity':55.0}}
        return device_api.packet(kind,source,'GATEWAY',body)
    def send(self,frame,identity='IP-MASTER',key=None,nonce=None,raw=None):
        key=key or self.key
        if nonce is None:
            challenge=self.peer.get('/api/v1/device/local-challenge',headers={'X-Device-ID':identity})
            if challenge.status_code!=200:return challenge
            nonce=challenge.json['nonce']
            self.assertEqual(challenge.json['signature'],local_ip.signature(key,'LOCALIP1-TIME',identity,nonce,str(challenge.json['unix_time']).encode()))
        body=raw or json.dumps(frame,separators=(',',':')).encode()
        response=self.peer.post('/api/v1/device/local-exchange',data=body,content_type='application/json',headers={'X-Device-ID':identity,'X-Local-Nonce':nonce,'X-Local-Signature':local_ip.signature(key,'LOCALIP1',identity,nonce,body)})
        if response.status_code==200:self.assertEqual(response.headers['X-Local-Signature'],local_ip.signature(key,'LOCALIP1-REPLY',identity,nonce,response.data))
        return response
    def test_master_sensor_persistence_and_cross_transport_duplicate(self):
        frame=self.frame();r=self.send(frame);self.assertEqual(r.status_code,200);self.assertEqual(r.json['receipt'],'PERSISTED')
        with local_ip.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM telemetry_values WHERE node_id='IP-MASTER' AND source='local-ip'").fetchone()[0],2)
        self.assertTrue(self.send(frame).json['duplicate'])
        self.assertTrue(device_api.ingest('IP-MASTER',frame)['duplicate'])
        changed=copy.deepcopy(frame);changed['sequence_number']+=1
        self.assertEqual(self.send(changed).status_code,400)
    def test_committed_readings_emit_browser_parameter_records(self):
        socket=server.socketio.test_client(server.app,flask_test_client=self.client)
        try:
            socket.get_received()
            frame=self.frame()
            self.assertEqual(self.send(frame).status_code,200)
            event=next(e['args'][0] for e in socket.get_received() if e['name']=='telemetry_update')
            self.assertEqual(event['node_id'],'IP-MASTER')
            self.assertIn('received_at',event)
            self.assertIsInstance(event['parameters'],list)
            readings={p['parameter_id']:p for p in event['parameters']}
            self.assertEqual(readings['temperature']['value'],25.5)
            self.assertEqual(readings['humidity']['value'],55)
            self.assertIn('timestamp',readings['temperature'])
            self.assertIn('alarm_status',readings['temperature'])
            self.assertTrue(self.send(frame).json['duplicate'])
            self.assertFalse(any(e['name']=='telemetry_update' for e in socket.get_received()))
        finally:socket.disconnect()

    def test_unknown_wrong_proof_replay_and_expired_nonce(self):
        self.assertEqual(self.send(self.frame(),identity='UNKNOWN').status_code,401)
        nonce=self.peer.get('/api/v1/device/local-challenge',headers={'X-Device-ID':'IP-MASTER'}).json['nonce']
        self.assertEqual(self.send(self.frame(),nonce=nonce,key=b'wrong').status_code,401)
        self.assertEqual(self.send(self.frame(),nonce=nonce).status_code,401)
        nonce=self.peer.get('/api/v1/device/local-challenge',headers={'X-Device-ID':'IP-MASTER'}).json['nonce']
        self.service.nonces[nonce]=('IP-MASTER',time.monotonic()-31)
        self.assertEqual(self.send(self.frame(),nonce=nonce).status_code,401)
    def test_invalid_duplicate_json_oversize_version_age_and_crc(self):
        frame=self.frame()
        for patch in ({'protocol_version':2},{'timestamp':int(time.time())-301},{'timestamp':int(time.time())+60},{'payload_crc32':0},{'source':'OTHER'},{'extra':True},{'ttl':True}):
            value={**frame,**patch};self.assertIn(self.send(value).status_code,(400,403))
        self.assertEqual(self.send(frame,raw=b'{"x":1,"x":2}').status_code,400)
        self.assertEqual(self.peer.post('/api/v1/device/local-exchange',data=b'x'*4097).status_code,413)
    def test_direct_node_requires_permission_and_individual_credential(self):
        device_api.enroll('IP-NODE','IP Node','NODE','IP-MASTER')
        frame=self.frame(source='IP-NODE')
        self.assertEqual(self.send(frame,identity='IP-NODE').status_code,401)
        node_key=hashlib.sha256(b'fixture-node-token-not-deployment').digest()
        local_ip.save_credential('IP-NODE','fixture-node-token-not-deployment')
        with local_ip.connection() as db:
            db.execute("UPDATE nodes SET device_token_hash=? WHERE node_id='IP-NODE'",(node_key.hex(),))
            db.execute("INSERT INTO local_ip_permissions VALUES('IP-NODE',1)")
        self.assertEqual(self.send(frame,'IP-NODE',node_key).status_code,200)
        other=self.frame(source='IP-MASTER');self.assertEqual(self.send(other,'IP-NODE',node_key).status_code,403)
        self.assertTrue(device_api.ingest('IP-MASTER',frame)['duplicate'])
    def test_command_only_reaches_authorized_node_and_completes_on_response(self):
        command=self.client.post('/api/v1/commands',json={'node_id':'IP-MASTER','command_type':'PING','payload':{}})
        self.assertEqual(command.status_code,201)
        result=self.send(self.frame());packet=result.json['commands'][0]
        self.assertEqual(packet['destination'],'IP-MASTER');cid=packet['message_id']
        ack=device_api.packet('ACK','IP-MASTER','GATEWAY',{'command_id':cid,'status':'RECEIVED'},correlation_id=cid)
        self.assertEqual(self.send(ack).status_code,200)
        response=device_api.packet('RESPONSE','IP-MASTER','GATEWAY',{'command_id':cid,'status':'SUCCESS','data':{'ok':True}},correlation_id=cid)
        self.assertEqual(self.send(response).status_code,200)
        import command_manager
        self.assertEqual(command_manager.get_command(cid)['state'],'COMPLETED')
    def test_api_login_csrf_revision_persistence_and_private_bind(self):
        self.assertEqual(server.app.test_client().get('/api/local-ip').status_code,401)
        value=self.client.get('/api/local-ip').json['settings'];payload=dict(enabled=False,bind_address='127.0.0.1',port=5001,expected_revision=value['revision'])
        self.assertEqual(self.client.post('/api/local-ip',json=payload,headers={'X-CSRF-Token':'wrong'}).status_code,403)
        self.assertEqual(self.client.post('/api/local-ip',json=payload).status_code,200)
        self.assertEqual(self.client.post('/api/local-ip',json=payload).status_code,409)
        for address in ('0.0.0.0','8.8.8.8','224.0.0.1','169.254.1.1'):
            payload.update(bind_address=address,expected_revision=self.service.settings()['revision'])
            self.assertEqual(self.client.post('/api/local-ip',json=payload).status_code,400)
        self.assertEqual(self.service.settings()['bind_address'],'127.0.0.1')
    def test_secret_never_in_public_status_or_response(self):
        result=self.send(self.frame());status=self.service.status()
        text=json.dumps(status)+result.data.decode()
        self.assertNotIn(self.token,text);self.assertNotIn(self.key.hex(),text)
        self.assertNotIn('device_token_hash',text)
    def test_protected_credential_missing_corrupted_and_verifier(self):
        with local_ip.connection() as db:
            verifier=db.execute("SELECT key_hash FROM local_ip_credentials WHERE device_id='IP-MASTER'").fetchone()[0]
        self.assertEqual(verifier,hashlib.sha256(self.key).hexdigest())
        self.assertNotEqual(verifier,self.key.hex())
        path=local_ip.credential_file('IP-MASTER');protected=path.read_bytes()
        path.unlink()
        self.assertEqual(self.send(self.frame()).status_code,401)
        path.write_bytes(b'corrupted')
        self.assertEqual(self.send(self.frame()).status_code,401)
        path.write_bytes(protected)
        self.assertEqual(self.send(self.frame()).status_code,200)
        with local_ip.connection() as db:
            db.execute("UPDATE local_ip_credentials SET key_hash=? WHERE device_id='IP-MASTER'",(self.key.hex(),))
        self.assertIsNone(self.service.peer('IP-MASTER'))
        self.service.migrate()
        self.assertIsNotNone(self.service.peer('IP-MASTER'))

    def test_dedicated_local_credential_preserves_legacy_hash(self):
        dedicated=hashlib.sha256(b'fixture-dedicated-local-token').digest()
        with local_ip.connection() as db:
            before=db.execute("SELECT device_token_hash FROM nodes WHERE node_id='IP-MASTER'").fetchone()[0]
            db.execute("DELETE FROM local_ip_credentials WHERE device_id='IP-MASTER'")
        local_ip.save_credential('IP-MASTER','fixture-dedicated-local-token')
        self.assertEqual(self.send(self.frame(),key=dedicated).status_code,200)
        with local_ip.connection() as db:self.assertEqual(db.execute("SELECT device_token_hash FROM nodes WHERE node_id='IP-MASTER'").fetchone()[0],before)
        self.assertNotIn(dedicated.hex(),json.dumps(self.service.status()))

if __name__=='__main__':unittest.main(verbosity=2)
