import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
import uuid
from gateway_fixture import seed
import mqtt_contract as c
from mqtt_store import Store
import mqtt_api
from mqtt_service import message
import device_api

def profile():
    p=json.loads((Path(__file__).parents[1]/'deployment/profile.example.json').read_text(encoding='utf-8'))
    p['password']='fixture-secret-not-deployment'
    return p

class ContractTests(unittest.TestCase):
    def test_every_profile_field_typed_and_required(self):
        p=profile();self.assertEqual(set(c.validate_profile(p,True)),set(c.FIELDS))
        for field in c.FIELDS:
            with self.subTest(field=field):
                for bad in (None,{},[]):
                    q=copy.deepcopy(p);q[field]=bad
                    with self.assertRaises(c.ContractError):c.validate_profile(q)
                q=dict(p);del q[field]
                with self.assertRaises(c.ContractError):c.validate_profile(q)
        for key in ('port','keepalive_s','timeout_s','qos_default'):
            for bad in (True,1.0,'1',-1,0x100000000):
                with self.subTest(key=key,bad=bad):
                    q=dict(p);q[key]=bad
                    with self.assertRaises(c.ContractError):c.validate_profile(q)
    def test_profile_security_bounds(self):
        p=profile()
        for key,bad in [('host','LOCALHOST'),('host','127.0.0.2'),('host','https://example.com'),('tls',False),('ca_cert','bad'),('password','x\0y'),('topic_prefix','a//b'),('client_id','x/y'),('gateway_id','x/#'),('mqtt_version','5'),('password','x'*257)]:
            with self.subTest(key=key):
                q=dict(p);q[key]=bad
                with self.assertRaises(c.ContractError):c.validate_profile(q)
    def test_digest_local_shared_and_freshness(self):
        p=profile();snap=c.snapshot(p,4)
        for key in ('password','username','client_id','profile_name'):
            q=dict(p);q[key]='different';self.assertEqual(c.digest(snap),c.digest(c.snapshot(q,4)))
        q=dict(p);q['host']='other.example';diff=c.compare(snap,c.snapshot(q,4),100,100)
        self.assertEqual(diff['message'],'Master config differs');self.assertEqual(diff['fields'],['profile.host'])
        self.assertEqual(c.compare(snap,snap,100,221)['status'],'UNKNOWN')
        self.assertEqual(c.compare(snap,snap,100,100)['status'],'MATCH')
        self.assertNotIn(p['password'],c.canonical(snap))
    def test_strict_json(self):
        for raw in (b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":"\xff"}',b'{"x":"\\u0000"}',b'{"x":'+b'['*9+b'0'+b']'*9+b'}',b'x'*6145):
            with self.assertRaises(c.ContractError):c.loads(raw)
    def test_envelope_topics_expiry_controls(self):
        p=profile();m=message(p,'MASTER1','config',{'op':'PROBE','transaction_id':str(uuid.uuid4()),'nonce':'a'*32,'participant':'GATEWAY'})
        self.assertEqual(c.envelope(c.canonical(m),c.topic(p,'config'),p),m)
        for patch in ({'schema_version':True},{'expires_at':0},{'timestamp':int(time.time())+60},{'message_id':'bad/one'},{'unknown':1}):
            with self.assertRaises(c.ContractError):c.envelope(c.canonical({**m,**patch}),c.topic(p,'config'),p)
        with self.assertRaises(c.ContractError):c.envelope(c.canonical(m),c.topic(p,'telemetry'),p)
        with self.assertRaises(c.ContractError):c.topic(p,'invented')
    def test_tls_context(self):
        import ssl
        context=c.tls_context(profile());self.assertTrue(context.check_hostname);self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);self.store=Store(root/'store.db',root/'secrets.bin')
    def tearDown(self):self.temp.cleanup()
    def test_commission_stage_cancel_secret_storage(self):
        p=profile();self.store.commission(p)
        self.assertNotIn(p['password'].encode(),self.store.database.read_bytes())
        self.assertNotIn(p['password'],json.dumps(self.store.public()));self.assertEqual(self.store.profile(),p)
        q=dict(p);q['password']='********';q['host']='other.example';s=self.store.stage(q,1)
        self.assertEqual(self.store.profile()['host'],p['host']);self.assertIsNone(s['transaction']['deadline'])
        with self.assertRaises(c.ContractError):self.store.stage(q,1)
        s=self.store.cancel(s['revision'],s['transaction']['transaction_id']);self.assertEqual(s['transaction']['state'],'ROLLED_BACK')
    def test_real_secret_http_rejected(self):
        with self.assertRaises(c.ContractError):self.store.stage(profile(),0)
    def test_restart_and_timeout_recovery(self):
        self.store.commission(profile());p=profile();p['password']='';self.store.stage(p,1);s=self.store.testing(2,'MASTER1')
        recreated=Store(self.store.database,self.store.secrets.path)
        s=recreated.recover(now=s['transaction']['deadline']+1);self.assertEqual(s['transaction']['state'],'ROLLED_BACK');self.assertEqual(recreated.profile(),profile())
    def test_partial_proofs_cannot_confirm(self):
        self.store.commission(profile());p=profile();p['password']='';self.store.stage(p,1);s=self.store.testing(2,'MASTER1');tx=s['transaction']['transaction_id']
        s=self.store.test_result(tx,{'tls':True,'connack':True});self.assertEqual(s['transaction']['state'],'FAILED')
        with self.assertRaises(c.ContractError):self.store.confirm(s['revision'],tx)
    def test_shared_revision_exhaustion_fails_before_network_testing(self):
        self.store.commission(profile());p=profile();p['password']='';s=self.store.stage(p,1)
        s=self.store.change(s['revision'],lambda current:current.update(shared_revision=0xffffffff))
        with self.assertRaises(c.ContractError):self.store.testing(s['revision'],'MASTER1')
        self.assertEqual(self.store.read()['transaction']['state'],'PENDING')

    def test_durable_commit_never_silently_rolled_back(self):
        self.store.commission(profile());p=profile();p['password']='';self.store.stage(p,1);s=self.store.testing(2,'MASTER1');tx=s['transaction']['transaction_id']
        s=self.store.test_result(tx,dict.fromkeys(('tls','connack','suback','puback','peer_probe','peer_ready'),True))
        s=self.store.confirm(s['revision'],tx);s=self.store.recover(now=10**10)
        self.assertEqual(s['transaction']['state'],'RECOVERY_REQUIRED');self.assertIn('previous',s)
        with self.assertRaises(c.ContractError):self.store.cancel(s['revision'],tx)

class ApiTests(unittest.TestCase):
    def setUp(self):self.client=seed()
    def test_api_auth_csrf_and_no_secrets(self):
        import server
        self.assertEqual(server.app.test_client().get('/api/mqtt').status_code,401)
        s=self.client.get('/api/mqtt');self.assertEqual(s.status_code,200)
        self.assertNotIn('password',s.json.get('active',{}))
        self.assertEqual(self.client.post('/api/mqtt/candidate',json={},headers={'X-CSRF-Token':'bad'}).status_code,403)
        self.assertEqual(self.client.post('/api/mqtt/candidate',data='{"expected_revision":0,"expected_revision":1}',content_type='application/json').status_code,400)
        self.assertEqual(self.client.get('/mqtt').status_code,200)
    def test_enrollment_and_rotation_never_return_a_token(self):
        response=self.client.post('/api/v1/devices',json={'device_id':'SECRET-API-MASTER','device_name':'API test','role':'MASTER'})
        self.assertEqual(response.status_code,201,response.json)
        self.assertNotIn('gateway_token',response.json)
        with device_api.connect() as db:
            previous=db.execute("SELECT device_token_hash FROM nodes WHERE node_id='SECRET-API-MASTER'").fetchone()[0]
        response=self.client.post('/api/v1/devices/SECRET-API-MASTER/rotate-token',json={})
        self.assertEqual(response.status_code,409)
        self.assertNotIn('gateway_token',response.json)
        with device_api.connect() as db:
            self.assertEqual(previous,db.execute("SELECT device_token_hash FROM nodes WHERE node_id='SECRET-API-MASTER'").fetchone()[0])

    def test_staging_persists_after_request(self):
        p=profile();p['password']='';r=self.client.post('/api/mqtt/candidate',json={'expected_revision':0,'profile':p})
        self.assertEqual(r.status_code,200,r.json);self.assertEqual(self.client.get('/api/mqtt').json['pending']['host'],p['host'])
        self.assertEqual(self.client.post('/api/mqtt/candidate',json={'expected_revision':0,'profile':p}).status_code,409)

class WorkerTests(unittest.TestCase):
    def setUp(self):
        seed();device_api.enroll('MQTT-MASTER','MQTT master','MASTER');device_api.enroll('MQTT-NODE','MQTT node','NODE','MQTT-MASTER','1')
        self.service=mqtt_api.service();self.service.store.commission(profile());self.service.profile=profile()
        while not self.service.outgoing.empty():self.service.outgoing.get_nowait()
    def test_persistence_receipt_and_duplicate(self):
        packet=device_api.packet('TELEMETRY','MQTT-NODE','GATEWAY',{'valid':True,'parameters':{'temperature':21.5,'humidity':45}})
        d=message(profile(),'MQTT-MASTER','telemetry',{'packet':packet},packet['message_id']);d['device_id']='MQTT-NODE'
        raw=c.canonical(d);topic=c.topic(profile(),'telemetry')
        self.service.handle(topic,raw);reply=self.service.outgoing.get_nowait();self.assertEqual(reply['data']['op'],'PERSISTED')
        self.service.handle(topic,raw);self.assertEqual(self.service.outgoing.get_nowait(),reply)
        d['data']['packet']['timestamp']+=1
        with self.assertRaises(c.ContractError):self.service.handle(topic,c.canonical(d))
    def test_unauthorized_and_queue_pressure(self):
        d=message(profile(),'UNENROLLED','status',{'connection_state':'OFFLINE'});d['device_id']='UNENROLLED'
        with self.assertRaises(c.ContractError):self.service.handle(c.topic(profile(),'status'),c.canonical(d))
        for _ in range(24):self.service.enqueue(d)
        with self.assertRaises(c.ContractError):self.service.enqueue(d)
    def test_chat_offline_persistence_and_expiry(self):
        import chat_manager
        row=chat_manager.send_message('GATEWAY','MQTT-MASTER','offline text')['message']
        self.assertEqual(row['status'],'QUEUED');self.assertIsNone(row['delivered_at'])
        with self.service.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM mqtt_chat_outbox WHERE message_id=?',(row['message_id'],)).fetchone()[0],1)
            db.execute('UPDATE mqtt_chat_outbox SET expires_at=0 WHERE message_id=?',(row['message_id'],))
        self.service.drain_chat();self.assertEqual(chat_manager.get_message(row['message_id'])['status'],'EXPIRED')
    def test_chat_puback_is_not_delivery_and_device_ack_is_required(self):
        import chat_manager
        row=chat_manager.send_message('GATEWAY','MQTT-MASTER','recipient receipt test')['message'];mid=row['message_id']
        self.service.chat_state(mid,'BROKER_ACCEPTED');self.assertEqual(chat_manager.get_message(mid)['status'],'BROKER_ACCEPTED')
        with self.assertRaises(ValueError):chat_manager.mark_delivered(mid)
        data={'received_message_id':mid,'conversation_id':row['conversation_id'],'state':'DELIVERED'}
        d=message(profile(),'MQTT-MASTER','chat/ack',data);d['device_id']='MQTT-MASTER'
        self.service.handle(c.topic(profile(),'chat/ack'),c.canonical(d));self.service.handle(c.topic(profile(),'chat/ack'),c.canonical(d))
        self.assertEqual(chat_manager.get_message(mid)['status'],'DELIVERED')
    def test_master_cannot_forge_node_chat_delivery(self):
        import chat_manager
        row=chat_manager.send_message('GATEWAY','MQTT-NODE','node receipt test')['message']
        d=message(profile(),'MQTT-MASTER','chat/ack',{'received_message_id':row['message_id'],'conversation_id':row['conversation_id'],'state':'DELIVERED'});d['device_id']='MQTT-MASTER'
        with self.assertRaises(c.ContractError):self.service.handle(c.topic(profile(),'chat/ack'),c.canonical(d))
        self.assertEqual(chat_manager.get_message(row['message_id'])['status'],'QUEUED')
    def test_incoming_chat_persistence_and_duplicate(self):
        import chat_manager
        d=message(profile(),'MQTT-MASTER','chat/message',{'conversation_id':'GATEWAY:MQTT-MASTER','sender_id':'MQTT-MASTER','recipient_id':'GATEWAY','text':'from device'});d['device_id']='MQTT-MASTER'
        self.service.handle(c.topic(profile(),'chat/message'),c.canonical(d));self.service.handle(c.topic(profile(),'chat/message'),c.canonical(d))
        row=chat_manager.get_message(d['message_id']);self.assertEqual(row['message_text'],'from device');self.assertEqual(row['delivery_semantics'],'MQTT')

    def test_unknown_can_be_resolved_by_late_recipient_receipt(self):
        import chat_manager
        row=chat_manager.send_message('GATEWAY','MQTT-MASTER','late receipt')['message']
        self.service.chat_state(row['message_id'],'UNKNOWN')
        self.service.chat_state(row['message_id'],'DELIVERED')
        self.assertEqual(chat_manager.get_message(row['message_id'])['status'],'DELIVERED')
        self.service.chat_state(row['message_id'],'BROKER_ACCEPTED')
        self.assertEqual(chat_manager.get_message(row['message_id'])['status'],'DELIVERED')

    def test_stop_wins_over_late_configuration_reload(self):
        from unittest.mock import patch
        import threading
        service=self.service
        entered=threading.Event();release=threading.Event();starts=[]
        def stop_worker():
            entered.set();release.wait(2)
        with patch.object(service,'_stop',side_effect=stop_worker),patch.object(service,'_start',side_effect=lambda:starts.append('start')):
            reload_thread=threading.Thread(target=service.reload);reload_thread.start()
            self.assertTrue(entered.wait(1))
            stop_thread=threading.Thread(target=service.stop);stop_thread.start()
            release.set();reload_thread.join(2);stop_thread.join(2)
            self.assertFalse(reload_thread.is_alive());self.assertFalse(stop_thread.is_alive())
            before=len(starts);service.reload();self.assertEqual(len(starts),before)
            self.assertTrue(service.shutdown_requested)

    def test_only_target_master_can_commit_and_repeated_receipts_are_idempotent(self):
        from mqtt_service import message
        pending=profile();pending['password']=''
        state=self.service.store.stage(pending,1)
        state=self.service.store.testing(state['revision'],'MQTT-MASTER');tx=state['transaction']['transaction_id']
        state=self.service.store.test_result(tx,dict.fromkeys(('tls','connack','suback','puback','peer_probe','peer_ready'),True))
        state=self.service.store.confirm(state['revision'],tx)
        data={'op':'SWITCH_COMMITTED','transaction_id':tx,'digest':c.digest(c.snapshot(profile(),1)),'shared_revision':1,'participant':'MASTER'}
        device_api.enroll('MQTT-OTHER','Other Master','MASTER')
        wrong=message(profile(),'MQTT-OTHER','config',data);wrong['device_id']='MQTT-OTHER'
        with self.assertRaises(c.ContractError):self.service.handle(c.topic(profile(),'config'),c.canonical(wrong))
        self.assertEqual(self.service.store.read()['transaction']['state'],'COMMITTING')
        for _ in range(2):
            reply=message(profile(),'MQTT-MASTER','config',data);reply['device_id']='MQTT-MASTER'
            self.service.handle(c.topic(profile(),'config'),c.canonical(reply))
        self.assertEqual(self.service.store.read()['transaction']['state'],'COMMITTED')
        self.assertEqual(self.service.store.read()['shared_revision'],1)

    def test_cancel_relays_on_active_channel_when_candidate_is_unavailable(self):
        pending=profile();pending.update(password='',topic_prefix='other/gateway',gateway_id='GW002')
        state=self.service.store.stage(pending,1)
        state=self.service.store.testing(state['revision'],'MQTT-MASTER');tx=state['transaction']['transaction_id']
        result=self.service.cancel(state['revision'],tx)
        sent=self.service.outgoing.get_nowait()
        self.assertEqual(result['transaction']['state'],'ROLLED_BACK')
        self.assertEqual(sent['gateway_id'],'GW001')
        self.assertEqual(sent['data']['op'],'SWITCH_ROLLBACK')
        self.assertEqual(sent['data']['transaction_id'],tx)
        self.assertEqual(self.service.store.profile(),profile())
