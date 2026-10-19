"""One bounded MQTT worker; broker PUBACK is separate from device delivery."""
from contextlib import contextmanager
import json
import queue
import secrets
import ssl
import socket
import threading
import time
import uuid
import paho.mqtt.client as mqtt
import mqtt_contract as contract
import device_api

@contextmanager
def device_connection():
    db=device_api.connect()
    try:
        with db:yield db
    finally:db.close()

def message(profile,master_id,kind,data,message_id=None,correlation_id=None):
    now=int(time.time())
    result={'schema_version':1,'message_id':message_id or str(uuid.uuid4()),'gateway_id':profile['gateway_id'],
            'master_id':master_id,'device_id':'GATEWAY','message_type':kind,'timestamp':now,'data':data,'expires_at':now+120}
    if correlation_id:result['correlation_id']=correlation_id
    return result

def client_for(profile, client_id=None):
    contract.validate_profile(profile,True)
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id=client_id or profile['client_id'],protocol=mqtt.MQTTv311,clean_session=True)
    client.username_pw_set(profile['username'],profile['password'])
    client.tls_set_context(contract.tls_context(profile))
    client.connect_timeout=profile['timeout_s']
    client.max_queued_messages_set(24);client.max_inflight_messages_set(8);client.reconnect_delay_set(1,60)
    return client

class Service:
    SUBSCRIPTIONS=('telemetry','status','command_ack','config','events','discovery','chat/message','chat/ack','chat/status')
    def __init__(self,store,trust_acl=False,client_factory=None):
        self.store=store;self.trust_acl=trust_acl;self.client_factory=client_factory or client_for;self.client=None;self.profile=None
        self.incoming=queue.Queue(32);self.outgoing=queue.Queue(24);self.stop_event=threading.Event()
        self.lock=threading.RLock();self.lifecycle=threading.RLock();self.shutdown_requested=False;self.thread=None;self.pending={};self.peer={};self.last_compare=0
        self.state='disconnected';self.last_error=None;self.reconnect_count=0;self.dropped=0;self.pubacks=0
        self.outbox_check=0
        self.subscriptions={};self.subscriptions_ready=set();self.last_connected_at=None
        self.last_received_at=None;self.last_persisted_at=None;self.last_puback_at=None
        self.testing_thread=None;self.candidate_client=None;self.candidate_profile=None
    def status(self):
        with self.lock:
            comparison={'status':'UNKNOWN','fields':[],'message':'No fresh authorized Master snapshot'}
            state=self.store.read()
            if self.profile and len(self.peer)==1:
                _,(snap,received)=next(iter(self.peer.items()))
                comparison=contract.compare(contract.snapshot(self.profile,state['shared_revision']),snap,received)
            return {'state':self.state,'last_error':self.last_error,'reconnect_count':self.reconnect_count,
                    'queue_length':self.outgoing.qsize(),'incoming_queue_length':self.incoming.qsize(),
                    'dropped':self.dropped,'pubacks':self.pubacks,'comparison':comparison,
                    'subscription_state':'UNKNOWN' if self.state!='connected' else 'READY' if len(self.subscriptions_ready)==len(self.SUBSCRIPTIONS) else 'SUBSCRIPTION_PENDING',
                    'last_connected_at':self.last_connected_at,'last_broker_frame_received_at':self.last_received_at,
                    'last_database_persisted_at':self.last_persisted_at,'last_broker_puback_at':self.last_puback_at,
                    'tls_verification_required':True,'tls_state':'VERIFIED' if self.state=='connected' else 'UNKNOWN',
                    'authentication_state':'ACCEPTED' if self.state=='connected' else 'AUTH_FAILED' if self.last_error=='AUTH_FAILED' else 'UNKNOWN',
                    'acl_status':'OPERATOR_ASSERTED' if self.trust_acl else 'UNVERIFIED'}
    def start(self):
        with self.lifecycle:
            self.shutdown_requested=False
            self._start()
    def _start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():return
            self.profile=self.store.profile()
            if not self.profile:return
            if not self.trust_acl:self.last_error='ACL_CONFIRMATION_REQUIRED';return
            self.client=self.client_factory(self.profile);self.stop_event.clear()
            self.client.on_connect=self.on_connect;self.client.on_disconnect=self.on_disconnect
            self.client.on_message=self.on_message;self.client.on_publish=self.on_publish
            self.client.on_subscribe=self.on_subscribe
            self.state='connecting'

            if self.store.read()["transaction"].get("decision")=="COMMIT" and self.store.read().get("pending"):
                threading.Thread(target=self.recover_commit,daemon=True).start()
            self.thread=threading.Thread(target=self.run,name='canonical-mqtt-worker',daemon=True);self.thread.start()
    def stop(self):
        with self.lifecycle:
            self.shutdown_requested=True
            self._stop()
    def _stop(self):
        self.stop_event.set()
        if self.client:self.client.disconnect();self.client.loop_stop()
        if self.thread and self.thread is not threading.current_thread():self.thread.join(timeout=5)
        self.state='disconnected'
    def on_connect(self,client,userdata,flags,reason,properties):
        if reason!=0:
            authentication=getattr(reason,'value',reason) in (4,5,134,135)
            self.state='authentication failure' if authentication else 'disconnected'
            self.last_error='AUTH_FAILED' if authentication else 'CONNECTION_REFUSED';return
        self.state='connected';self.last_error=None
        self.last_connected_at=int(time.time());self.subscriptions.clear();self.subscriptions_ready.clear()
        for kind in self.SUBSCRIPTIONS:
            result,mid=client.subscribe(contract.topic(self.profile,kind),qos=1)
            if result==mqtt.MQTT_ERR_SUCCESS:self.subscriptions[mid]=kind
            else:self.last_error='SUBSCRIPTION_FAILED'
    def on_subscribe(self,client,userdata,mid,reasons,properties):
        kind=self.subscriptions.get(mid)
        if not kind:return
        if len(reasons)==1 and getattr(reasons[0],'value',reasons[0])==1:self.subscriptions_ready.add(kind)
        else:self.last_error='SUBSCRIPTION_REJECTED'
    def on_disconnect(self,client,userdata,flags,reason,properties):
        self.state='disconnected';self.reconnect_count+=1;self.subscriptions_ready.clear()
    def on_message(self,client,userdata,msg):
        self.last_received_at=int(time.time())
        if len(msg.payload)>6144 or msg.qos!=1:self.dropped+=1;return
        try:self.incoming.put_nowait((msg.topic,bytes(msg.payload),msg.retain))
        except queue.Full:self.dropped+=1;self.last_error='QUEUE_FULL'
    def on_publish(self,client,userdata,mid,reason,properties):
        with self.lock:
            self.pubacks+=1
            self.last_puback_at=int(time.time())
            message_id=self.pending.pop(mid,None)
            if message_id:self.chat_state(message_id,'BROKER_ACCEPTED')
    def enqueue(self,envelope):
        try:self.outgoing.put_nowait(envelope);return 'QUEUED'
        except queue.Full:self.dropped+=1;raise contract.ContractError('QUEUE_FULL') from None
    @staticmethod
    def authorized(master_id,device_id):
        with device_connection() as db:
            master=db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_role='MASTER' AND enabled=1 AND device_enrolled=1",(master_id,)).fetchone()
            node=db.execute("SELECT 1 FROM nodes WHERE node_id=? AND enabled=1 AND device_enrolled=1 AND (node_id=? OR master_id=?)",(device_id,master_id,master_id)).fetchone()
        return bool(master and node)
    def handle(self,received_topic,raw,retain=False):
        d=contract.envelope(raw,received_topic,self.profile,retained=retain)
        if d['device_id']=='GATEWAY':return
        contract.require(self.authorized(d['master_id'],d['device_id']),code='UNAUTHORIZED')
        fingerprint=contract.digest(d);key=(d['master_id'],d['device_id'],d['message_id'])
        with self.store.connect() as db:
            old=db.execute('SELECT fingerprint,outcome FROM mqtt_receipts WHERE master_id=? AND device_id=? AND message_id=?',key).fetchone()
        if old:
            contract.require(old['fingerprint']==fingerprint,code='DUPLICATE_CONFLICT')
            if old['outcome']!='{}':self.enqueue(json.loads(old['outcome']))
            return
        data=d['data'];kind=d['message_type'];response=None
        if kind in ('telemetry','status','command_ack','events','discovery') and 'packet' in data:
            packet=data['packet'];source=packet.get('source');contract.require(source==d['device_id'] or (d['device_id']==d['master_id'] and self.authorized(d['master_id'],source)),code='UNAUTHORIZED')
            allowed={'telemetry':('TELEMETRY',),'status':('HELLO','HEARTBEAT','STATUS'),'discovery':('HELLO','HEARTBEAT','STATUS'),'command_ack':('ACK','RESPONSE'),'events':('EVENT','ALARM','DIAGNOSTIC')}
            contract.require(packet.get('type') in allowed[kind] and packet.get('destination')=='GATEWAY','packet')
            device_api.ingest(d['master_id'],packet,transport='mqtt')
            self.last_persisted_at=int(time.time())
            response=message(self.profile,d['master_id'],'config',{'op':'PERSISTED','received_message_id':packet['message_id'],'status':'PERSISTED'},correlation_id=d['message_id'])
            for command in device_api.pending_commands(d['master_id']):self.enqueue(message(self.profile,d['master_id'],'command',{'packet':command},message_id=command['message_id']))
        elif kind=='config':
            contract.require(d['device_id']==d['master_id'],code='UNAUTHORIZED')
            op=data['op']
            if op=='COMPARE':
                own=contract.snapshot(self.profile,self.store.read()['shared_revision'])
                result=contract.compare(own,data['snapshot'],time.time())
                contract.require(result['status'] not in ('UNKNOWN','INCOMPATIBLE'),'snapshot')
                self.peer[d['master_id']]=(data['snapshot'],time.time())
            elif op=='PROBE' and data['participant']=='MASTER':
                response=message(self.profile,d['master_id'],'config',{**data,'op':'PROBE_ACK','participant':'GATEWAY'},correlation_id=d['message_id'])
            elif op=='SWITCH_COMMITTED':
                state=self.store.read();transaction=state['transaction']
                contract.require(transaction.get('master_id')==d['master_id'] and transaction.get('transaction_id')==data['transaction_id'],code='UNAUTHORIZED')
                committed=transaction.get('state')=='COMMITTED'
                expected_revision=state['shared_revision']+(0 if committed else 1)
                expected=contract.digest(contract.snapshot(self.store.profile('active' if committed else 'pending'),expected_revision))
                contract.require(data['participant']=='MASTER' and data['digest']==expected and data['shared_revision']==expected_revision,code='TRANSACTION_CONFLICT')
                self.store.committed(data['transaction_id'])
            else:contract.require(op in ('PROBE_ACK','SWITCH_READY'),'op')
        elif kind=='chat/ack':
            with device_connection() as db:
                row=db.execute('SELECT * FROM chat_messages WHERE message_id=?',(data['received_message_id'],)).fetchone()
            contract.require(row is not None and row['conversation_id']==data['conversation_id'] and self.authorized(d['master_id'],row['receiver_node_id']),code='UNAUTHORIZED')
            # A Master must not claim a Node read/delivery without a supported recipient path.
            contract.require(data['state'] not in ('DELIVERED','READ') or row['receiver_node_id']==d['device_id'],code='UNAUTHORIZED')
            self.chat_state(data['received_message_id'],data['state'])
        elif kind=='chat/message':
            contract.require(data['sender_id']==d['device_id'] and data['recipient_id']=='GATEWAY',code='UNAUTHORIZED')
            expected=':'.join(sorted(('GATEWAY',d['device_id'])))
            contract.require(data['conversation_id']==expected,'conversation_id')
            from datetime import datetime
            now=datetime.now().isoformat()
            with device_connection() as db:
                db.execute('INSERT OR IGNORE INTO chat_conversations(conversation_id,node_a,node_b,created_at,updated_at) VALUES (?,?,?,?,?)',(expected,min('GATEWAY',d['device_id']),max('GATEWAY',d['device_id']),now,now))
                db.execute("INSERT OR IGNORE INTO chat_messages(message_id,conversation_id,sender_node_id,receiver_node_id,message_text,status,created_at,delivered_at,delivery_semantics) VALUES (?,?,?,?,?,'DELIVERED',?,?,'MQTT')",(d['message_id'],expected,d['device_id'],'GATEWAY',data['text'],now,now))
            device_api._emit('chat_message', {'sender_node_id': d['device_id'], 'receiver_node_id': 'GATEWAY', 'message_id': d['message_id']})
            response=message(self.profile,d['master_id'],'chat/ack',{'received_message_id':d['message_id'],'conversation_id':expected,'state':'DELIVERED'},correlation_id=d['message_id'])
        elif kind=='chat/status':pass
        elif kind=='status':pass
        else:raise contract.ContractError('NOT_AVAILABLE')
        with self.store.connect() as db:
            db.execute('INSERT INTO mqtt_receipts VALUES (?,?,?,?,?,?)',(*key,fingerprint,contract.canonical(response or {}),time.time()))
            db.execute('DELETE FROM mqtt_receipts WHERE rowid IN (SELECT rowid FROM mqtt_receipts ORDER BY received_at DESC LIMIT -1 OFFSET 4096)')
        if response:self.enqueue(response)
    @staticmethod
    def chat_state(message_id,state):
        with device_connection() as db:
            row=db.execute('SELECT status FROM chat_messages WHERE message_id=?',(message_id,)).fetchone()
            if not row:return
            order={'QUEUED':0,'PUBLISHED':1,'BROKER_ACCEPTED':2,'STORED':3,'DELIVERED':4,'READ':5,'FAILED':6,'EXPIRED':6,'UNKNOWN':6}
            if order.get(state,-1)<order.get(row['status'],-1) and not (row['status']=='UNKNOWN' and state in ('DELIVERED','READ')):return
            db.execute('UPDATE chat_messages SET status=? WHERE message_id=?',(state,message_id))
            db.execute('UPDATE mqtt_chat_outbox SET state=? WHERE message_id=?',(state,message_id))
            recipients=db.execute('SELECT sender_node_id,receiver_node_id FROM chat_messages WHERE message_id=?',(message_id,)).fetchone()
        device_api._emit('chat_message',dict(recipients))
    def queue_chat(self,row):
        contract.require(row['sender_node_id']=='GATEWAY',code='UNAUTHORIZED')
        with device_connection() as db:
            node=db.execute('SELECT * FROM nodes WHERE node_id=? AND enabled=1 AND device_enrolled=1',(row['receiver_node_id'],)).fetchone()
        if not node or not self.profile:self.chat_state(row['message_id'],'FAILED');return 'FAILED'
        master=node['node_id'] if node['device_role']=='MASTER' else node['master_id']
        data={'conversation_id':row['conversation_id'],'sender_id':'GATEWAY','recipient_id':row['receiver_node_id'],'text':row['message_text']}
        d=message(self.profile,master,'chat/message',data,message_id=row['message_id'])
        with self.store.connect() as db:
            count=db.execute("SELECT count(*) FROM mqtt_chat_outbox WHERE state IN ('QUEUED','PUBLISHED','BROKER_ACCEPTED')").fetchone()[0]
            contract.require(count<24,code='QUEUE_FULL')
            db.execute('INSERT INTO mqtt_chat_outbox(message_id,envelope,expires_at,next_attempt,state) VALUES (?,?,?,?,?)',(row['message_id'],contract.canonical(d),d['expires_at'],0,'QUEUED'))
        return 'QUEUED'
    def run(self):
        delay=1
        while not self.stop_event.is_set():
            try:
                self.client.connect(self.profile['host'],self.profile['port'],self.profile['keepalive_s'])
                if self.stop_event.is_set():self.client.disconnect();return
                self.client.loop_start();break
            except ssl.SSLError:self.state='TLS failure';self.last_error='TLS_FAILED'
            except socket.gaierror:self.state='disconnected';self.last_error='DNS_FAILED'
            except OSError:self.state='disconnected';self.last_error='CONNECTION_FAILED'
            self.reconnect_count+=1
            if self.stop_event.wait(delay):return
            delay=min(60,delay*2)
        while not self.stop_event.wait(.05):
            try:
                try:item=self.incoming.get_nowait()
                except queue.Empty:item=None
                if item:self.handle(*item)
                if time.monotonic()-self.outbox_check>=1:
                    self.outbox_check=time.monotonic();self.drain_chat()
                transaction=self.store.read()['transaction']
                if transaction['state'] in ('TESTING','READY_TO_CONFIRM','COMMITTING') and transaction.get('deadline',time.time()+1)<time.time():
                    self.store.recover()
                    if self.candidate_client:self.candidate_client.disconnect();self.candidate_client.loop_stop();self.candidate_client=None
                if self.state!='connected':continue
                try:d=self.outgoing.get_nowait()
                except queue.Empty:d=None
                if d:
                    if d.get('expires_at',0)<time.time():self.chat_state(d['message_id'],'EXPIRED');continue
                    with self.lock:
                        info=self.client.publish(contract.topic(self.profile,d['message_type']),contract.canonical(d),qos=1,retain=False)
                        if info.rc==mqtt.MQTT_ERR_SUCCESS:
                            self.pending[info.mid]=d['message_id'];self.chat_state(d['message_id'],'PUBLISHED')
                        else:self.chat_state(d['message_id'],'UNKNOWN');self.last_error='PUBLISH_FAILED'
                if time.monotonic()-self.last_compare>30:
                    self.last_compare=time.monotonic();state=self.store.read();snap=contract.snapshot(self.profile,state['shared_revision'])
                    with device_connection() as db:masters=db.execute("SELECT node_id FROM nodes WHERE device_role='MASTER' AND enabled=1 AND device_enrolled=1").fetchall()
                    for master in masters:self.enqueue(message(self.profile,master['node_id'],'config',{'op':'COMPARE','snapshot':snap,'digest':contract.digest(snap)}))
            except contract.ContractError as e:self.last_error=e.code;self.dropped+=1
            except Exception:self.last_error='PROCESSING_FAILED';self.dropped+=1
    def test_candidate(self,revision,master_id):
        contract.require(self.authorized(master_id,master_id),code='UNAUTHORIZED')
        with self.lock:
            contract.require(not self.testing_thread or not self.testing_thread.is_alive(),code='TRANSACTION_BUSY')
            state=self.store.testing(revision,master_id);tx=state['transaction']['transaction_id']
            self.testing_thread=threading.Thread(target=self._test,args=(tx,master_id),daemon=True,name='mqtt-candidate-test');self.testing_thread.start()
        return state
    def _test(self,tx,master_id):
        profile=self.store.profile('pending');shared_revision=self.store.read()['shared_revision']+1;expected_digest=contract.digest(contract.snapshot(profile,shared_revision));proofs={};error=None;nonce=secrets.token_hex(16);done=threading.Event();subscribed=threading.Event();published=threading.Event()
        client=None
        try:
            client=client_for(profile,profile['client_id'][:40]+':test:'+tx[:8])
            def connected(c,u,f,r,p):
                nonlocal error
                if r!=0:error='AUTH_FAILED';done.set();return
                proofs.update(tls=True,connack=True);c.subscribe(contract.topic(profile,'config'),qos=1)
            def subscription(c,u,mid,codes,p):
                if codes and all(code==1 for code in codes):proofs['suback']=True;subscribed.set()
            def received(c,u,msg):
                try:
                    d=contract.envelope(msg.payload,msg.topic,profile,retained=msg.retain);data=d['data']
                    if d['master_id']!=master_id or d['device_id']!=master_id or data.get('transaction_id')!=tx:return
                    if data['op']=='PROBE_ACK' and data['nonce']==nonce and data['participant']=='MASTER':proofs['peer_probe']=True
                    if data['op']=='PROBE' and data['participant']=='MASTER':
                        reply=message(profile,master_id,'config',{**data,'op':'PROBE_ACK','participant':'GATEWAY'},correlation_id=d['message_id'])
                        c.publish(contract.topic(profile,'config'),contract.canonical(reply),qos=1)
                    if data['op']=='SWITCH_READY' and data['participant']=='MASTER' and data['digest']==expected_digest and data['shared_revision']==shared_revision:proofs['peer_ready']=True
                    if proofs.get('peer_probe') and proofs.get('peer_ready'):done.set()
                    if data['op']=='SWITCH_COMMITTED' and data['participant']=='MASTER' and data['digest']==expected_digest and data['shared_revision']==shared_revision:
                        self.store.committed(tx)
                        threading.Thread(target=self.reload,daemon=True).start()
                except contract.ContractError:pass
            client.on_connect=connected;client.on_subscribe=subscription;client.on_message=received
            self.candidate_client=client;self.candidate_profile=profile
            self.enqueue(message(self.profile,master_id,'config',{'op':'SWITCH_PREPARE','transaction_id':tx,'shared_revision':shared_revision,'digest':expected_digest,'participant':'GATEWAY','deadline':self.store.read()['transaction']['deadline']}))
            client.connect(profile['host'],profile['port'],profile['keepalive_s']);client.loop_start()
            deadline=time.monotonic()+min(50,profile['timeout_s']+20)
            while time.monotonic()<deadline and not done.is_set():
                if subscribed.wait(.1):
                    probe=message(profile,master_id,'config',{'op':'PROBE','transaction_id':tx,'nonce':nonce,'participant':'GATEWAY'})
                    for _ in range(3):
                        info=client.publish(contract.topic(profile,'config'),contract.canonical(probe),qos=1);info.wait_for_publish(timeout=5)
                        if info.is_published():proofs['puback']=True
                        if done.wait(5):break
                    # A physical peer may finish TLS/NVS after the last bounded probe.
                    done.wait(max(0,deadline-time.monotonic()))
                    break
            if not proofs.get('peer_probe') and not error:error='COORDINATION_REQUIRED'
        except ssl.SSLError:error='TLS_FAILED'
        except (OSError,ValueError):error='CONNECTION_FAILED'
        finally:
            if client and (error or not proofs.get("peer_ready")):client.disconnect();client.loop_stop();self.candidate_client=None
            try:self.store.test_result(tx,proofs,error)
            except contract.ContractError:pass # Cancellation or newer revision wins.

    def confirm(self,revision,transaction_id):
        contract.require(self.candidate_client is not None and self.candidate_client.is_connected(),code='COORDINATION_REQUIRED')
        state=self.store.confirm(revision,transaction_id)
        data={'op':'SWITCH_CONFIRM','transaction_id':transaction_id,'shared_revision':state['shared_revision']+1,
              'digest':contract.digest(contract.snapshot(self.candidate_profile,state['shared_revision']+1)),'participant':'GATEWAY'}
        d=message(self.candidate_profile,state['transaction']['master_id'],'config',data)
        info=self.candidate_client.publish(contract.topic(self.candidate_profile,'config'),contract.canonical(d),qos=1)
        if info.rc!=mqtt.MQTT_ERR_SUCCESS:self.store.recover()
        return self.store.public()
    def reload(self):
        with self.lifecycle:
            if self.shutdown_requested:return
            self._stop()
            if self.candidate_client:self.candidate_client.disconnect();self.candidate_client.loop_stop();self.candidate_client=None
            self._start()

    def cancel(self,revision,transaction_id):
        state=self.store.read();candidate=self.store.profile('pending')
        result=self.store.cancel(revision,transaction_id)
        if candidate and state['transaction'].get('master_id'):
            data={'op':'SWITCH_ROLLBACK','transaction_id':transaction_id,'shared_revision':state['shared_revision']+1,'digest':contract.digest(contract.snapshot(candidate,state['shared_revision']+1)),'participant':'GATEWAY'}
            d=message(candidate,state['transaction'].get('master_id') or 'UNKNOWN','config',data)
            # The active channel remains the recovery path if candidate TLS failed.
            try:self.enqueue(message(self.profile,state['transaction']['master_id'],'config',data))
            except contract.ContractError:self.last_error='PEER_ROLLBACK_UNCONFIRMED'
            if self.candidate_client:self.candidate_client.publish(contract.topic(candidate,'config'),contract.canonical(d),qos=1)
        return result
    def recover_commit(self):
        state=self.store.read();tx=state['transaction'];profile=self.store.profile('pending')
        if not profile or not tx.get('master_id'):return
        client=None;done=threading.Event()
        try:
            client=client_for(profile,profile['client_id'][:40]+':recover:'+tx['transaction_id'][:8])
            digest=contract.digest(contract.snapshot(profile,state['shared_revision']+1))
            def connected(c,u,f,r,p):
                if r==0:c.subscribe(contract.topic(profile,'config'),qos=1)
            def received(c,u,msg):
                try:
                    d=contract.envelope(msg.payload,msg.topic,profile,retained=msg.retain);data=d['data']
                    if d['master_id']==tx['master_id'] and d['device_id']==tx['master_id'] and data.get('op')=='SWITCH_COMMITTED' and data.get('participant')=='MASTER' and data.get('transaction_id')==tx['transaction_id'] and data.get('digest')==digest and data.get('shared_revision')==state['shared_revision']+1:
                        self.store.committed(tx['transaction_id']);done.set()
                except contract.ContractError:pass
            client.on_connect=connected;client.on_message=received;client.connect(profile['host'],profile['port'],profile['keepalive_s']);client.loop_start()
            for _ in range(6):
                if self.stop_event.is_set():break
                if client.is_connected():
                    data={'op':'SWITCH_CONFIRM','transaction_id':tx['transaction_id'],'digest':digest,'shared_revision':state['shared_revision']+1,'participant':'GATEWAY'}
                    client.publish(contract.topic(profile,'config'),contract.canonical(message(profile,tx['master_id'],'config',data)),qos=1)
                if done.wait(5):break
        except (OSError,ValueError):self.last_error='RECOVERY_REQUIRED'
        finally:
            if client:client.disconnect();client.loop_stop()
        if done.is_set():self.reload()

    def drain_chat(self):
        now=time.time()
        with self.store.connect() as db:
            rows=db.execute("SELECT * FROM mqtt_chat_outbox WHERE state IN ('QUEUED','PUBLISHED','BROKER_ACCEPTED') AND next_attempt<=? LIMIT 24",(now,)).fetchall()
        for row in rows:
            if row['expires_at']<now:self.chat_state(row['message_id'],'EXPIRED');continue
            if self.state!='connected':continue
            if row['attempts']>=3:self.chat_state(row['message_id'],'UNKNOWN');continue
            self.enqueue(json.loads(row['envelope']))
            with self.store.connect() as db:db.execute('UPDATE mqtt_chat_outbox SET attempts=attempts+1,next_attempt=? WHERE message_id=?',(now+5,row['message_id']))
