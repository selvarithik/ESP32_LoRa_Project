"""Real disposable TLS broker tests. The Master participant is software, not hardware.
Run explicitly: .venv/Scripts/python.exe tests/integration_tls.py
"""
import asyncio
from datetime import datetime,timedelta,timezone
import json
import logging
from pathlib import Path
import socket
import ssl
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pwdlib import PasswordHash
from amqtt.broker import Broker
from gateway_fixture import seed
import mqtt_contract as c
from mqtt_service import client_for,message,Service
from mqtt_store import Store
import device_api
from test_mqtt_contract import profile

logging.getLogger('amqtt').setLevel(logging.CRITICAL)

def certificates(root):
    now=datetime.now(timezone.utc);key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Disposable Test CA')])
    ca=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=2)).add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True).sign(key,hashes.SHA256())
    server_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    leaf=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'broker.test')])).issuer_name(name).public_key(server_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName('broker.test')]),critical=False).add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True).sign(key,hashes.SHA256())
    pem=ca.public_bytes(serialization.Encoding.PEM).decode()
    (root/'server.pem').write_bytes(leaf.public_bytes(serialization.Encoding.PEM)+pem.encode())
    (root/'server.key').write_bytes(server_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    return pem

class BrokerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed();device_api.enroll('TLS-MASTER','TLS master','MASTER')
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name);ca=certificates(cls.root)
        cls.profile=profile();cls.profile.update(host='broker.test',ca_cert=ca,username='fixture',password='disposable-broker-password',client_id='fixture-server')
        (cls.root/'users').write_text('fixture:'+PasswordHash.recommended().hash(cls.profile['password'])+'\n',encoding='utf-8')
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));cls.port=sock.getsockname()[1]
        cls.profile['port']=cls.port;cls.loop=asyncio.new_event_loop();cls.thread=threading.Thread(target=cls.loop.run_forever,daemon=True);cls.thread.start()
        topics=[c.topic(cls.profile,k) for k in c.TYPES]
        async def start():
            cls.broker=Broker({'listeners':{'default':{'type':'tcp','bind':f'127.0.0.1:{cls.port}','ssl':True,'certfile':str(cls.root/'server.pem'),'keyfile':str(cls.root/'server.key')}},'plugins':{'amqtt.plugins.authentication.FileAuthPlugin':{'password_file':str(cls.root/'users')},'amqtt.plugins.topic_checking.TopicAccessControlListPlugin':{'acl':{'fixture':topics},'publish_acl':{'fixture':topics}}}})
            await cls.broker.start()
        asyncio.run_coroutine_threadsafe(start(),cls.loop).result(10)
        original=socket.getaddrinfo
        def resolve(host,*args,**kwargs):return original('127.0.0.1' if host in ('broker.test','wrong.test') else host,*args,**kwargs)
        cls.dns=patch('socket.getaddrinfo',resolve);cls.dns.start()
    @classmethod
    def tearDownClass(cls):
        cls.dns.stop();asyncio.run_coroutine_threadsafe(cls.broker.shutdown(),cls.loop).result(10);cls.loop.call_soon_threadsafe(cls.loop.stop);cls.thread.join(3);cls.loop.close();cls.temp.cleanup()
    def test_tls_chain_and_hostname_fail_closed(self):
        wrong=dict(self.profile);wrong['ca_cert']=profile()['ca_cert']
        for p in (wrong,{**self.profile,'host':'wrong.test'}):
            client=client_for(p,'invalid-cert-fixture')
            with self.assertRaises(ssl.SSLCertVerificationError):client.connect(p['host'],p['port'],60)
    def test_wrong_credentials_are_rejected(self):
        client=client_for({**self.profile,'password':'wrong-fixture-password'},'bad-auth-fixture');event=threading.Event();reasons=[]
        client.on_connect=lambda cl,u,f,r,p:(reasons.append(r),event.set())
        client.on_disconnect=lambda *args:event.set()
        client.connect(self.profile['host'],self.port,60);client.loop_start()
        try:
            self.assertTrue(event.wait(5));self.assertFalse(client.is_connected());self.assertFalse(reasons and reasons[0]==0)
        finally:client.disconnect();client.loop_stop()
    def test_two_broker_switch_with_independent_software_master(self):
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        candidate={**self.profile,'port':port}
        async def start_second():
            broker=Broker({'listeners':{'default':{'type':'tcp','bind':f'127.0.0.1:{port}','ssl':True,'certfile':str(self.root/'server.pem'),'keyfile':str(self.root/'server.key')}},'plugins':{'amqtt.plugins.authentication.FileAuthPlugin':{'password_file':str(self.root/'users')}}})
            await broker.start();return broker
        broker=asyncio.run_coroutine_threadsafe(start_second(),self.loop).result(10)
        store=Store(self.root/'switch.db',self.root/'switch-secrets.bin');store.commission(self.profile)
        service=Service(store,True);service.start();transaction={};peer_ready=threading.Event();old_ready=threading.Event()
        old=client_for(self.profile,'switch-old-master');peer=client_for(candidate,'switch-candidate-master')
        old.on_connect=lambda cl,u,f,r,p:cl.subscribe(c.topic(self.profile,'config'),qos=1)
        old.on_subscribe=lambda *args:old_ready.set()
        peer.on_connect=lambda cl,u,f,r,p:cl.subscribe(c.topic(candidate,'config'),qos=1)
        peer.on_subscribe=lambda *args:peer_ready.set()
        def publish(data,correlation=None):
            d=message(candidate,'TLS-MASTER','config',data,correlation_id=correlation);d['device_id']='TLS-MASTER'
            peer.publish(c.topic(candidate,'config'),c.canonical(d),qos=1)
        def on_old(cl,u,msg):
            d=c.envelope(msg.payload,msg.topic,self.profile)
            if d['data'].get('op')=='SWITCH_PREPARE':transaction.update(d['data'])
        def on_candidate(cl,u,msg):
            d=c.envelope(msg.payload,msg.topic,candidate);data=d['data']
            if d['device_id']!='GATEWAY' or data.get('transaction_id')!=transaction.get('transaction_id'):return
            if data['op']=='PROBE':
                publish({**data,'op':'PROBE_ACK','participant':'MASTER'},d['message_id'])
                publish({'op':'PROBE','transaction_id':data['transaction_id'],'nonce':'b'*32,'participant':'MASTER'})
            elif data['op']=='PROBE_ACK' and data['nonce']=='b'*32:
                publish({k:v for k,v in {**transaction,'op':'SWITCH_READY','participant':'MASTER'}.items() if k!='deadline'})
            elif data['op']=='SWITCH_CONFIRM':publish({**data,'op':'SWITCH_COMMITTED','participant':'MASTER'},d['message_id'])
        old.on_message=on_old;peer.on_message=on_candidate
        old.connect(self.profile['host'],self.port,60);old.loop_start();peer.connect(candidate['host'],port,60);peer.loop_start()
        try:
            self.assertTrue(old_ready.wait(5));self.assertTrue(peer_ready.wait(5))
            p={**candidate,'password':''};state=store.stage(p,1);service.test_candidate(state['revision'],'TLS-MASTER')
            until=time.monotonic()+25
            while store.read()['transaction']['state']=='TESTING' and time.monotonic()<until:time.sleep(.05)
            state=store.read();self.assertEqual(state['transaction']['state'],'READY_TO_CONFIRM',store.public())
            self.assertEqual(store.profile()['port'],self.port)
            service.confirm(state['revision'],state['transaction']['transaction_id'])
            until=time.monotonic()+5
            while store.read()['transaction']['state']!='COMMITTED' and time.monotonic()<until:time.sleep(.05)
            self.assertEqual(store.read()['transaction']['state'],'COMMITTED');self.assertEqual(store.profile()['port'],port)
            time.sleep(.3)
        finally:
            old.disconnect();old.loop_stop();peer.disconnect();peer.loop_stop();service.stop()
            asyncio.run_coroutine_threadsafe(broker.shutdown(),self.loop).result(10)
    def test_real_qos1_persistence_and_duplicate_receipts(self):
        store=Store(self.root/'worker.db',self.root/'worker-secrets.bin');store.commission(self.profile)
        service=Service(store,True);service.start()
        peer=client_for(self.profile,'independent-master-fixture');sub=threading.Event();receipt=threading.Event();received=[]
        peer.on_connect=lambda cl,u,f,r,p:cl.subscribe(c.topic(self.profile,'config'),qos=1)
        peer.on_subscribe=lambda *args:sub.set()
        def on_message(cl,u,msg):
            d=c.envelope(msg.payload,msg.topic,self.profile)
            if d['data'].get('op')=='PERSISTED':received.append(d);receipt.set()
        peer.on_message=on_message;peer.connect(self.profile['host'],self.port,60);peer.loop_start()
        try:
            self.assertTrue(sub.wait(5))
            until=time.monotonic()+5
            while service.state!='connected' and time.monotonic()<until:time.sleep(.05)
            self.assertEqual(service.state,'connected')
            while service.status()['subscription_state']!='READY' and time.monotonic()<until:time.sleep(.05)
            self.assertEqual(service.status()['subscription_state'],'READY')
            packet=device_api.packet('TELEMETRY','TLS-MASTER','GATEWAY',{'valid':True,'parameters':{'temperature':22,'humidity':45}})
            d=message(self.profile,'TLS-MASTER','telemetry',{'packet':packet},packet['message_id']);d['device_id']='TLS-MASTER'
            for _ in range(2):
                receipt.clear();info=peer.publish(c.topic(self.profile,'telemetry'),c.canonical(d),qos=1);info.wait_for_publish(5);self.assertTrue(info.is_published());self.assertTrue(receipt.wait(5),service.status())
            self.assertEqual(received[0],received[1]);self.assertEqual(received[0]['data']['status'],'PERSISTED')
            with store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM mqtt_receipts WHERE message_id=?',(d['message_id'],)).fetchone()[0],1)
        finally:peer.disconnect();peer.loop_stop();service.stop()

if __name__=='__main__':unittest.main(verbosity=2)
