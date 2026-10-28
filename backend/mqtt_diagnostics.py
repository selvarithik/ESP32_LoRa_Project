"""Bounded active-profile probes. Never activates, stages or edits a broker profile."""
import copy
import json
import secrets
import socket
import ssl
import threading
import time
import uuid
from flask import jsonify, request
import mqtt_contract as contract
from mqtt_service import client_for, message
import mqtt_api
import database
import account_settings

class Diagnostics:
    def __init__(self):
        self.lock=threading.RLock();self.thread=None;self.result={'state':'IDLE','scope':'BROKER_PROBE_ONLY','acl_status':'UNVERIFIED'}
    def status(self):
        with self.lock:return copy.deepcopy(self.result)
    def start(self,profile,revision,master_id,operation):
        with self.lock:
            if self.thread and self.thread.is_alive():raise contract.ContractError('DIAGNOSTIC_BUSY')
            self.result={'state':'RUNNING','operation':operation,'profile_revision':revision,'scope':'BROKER_PROBE_ONLY','acl_status':'UNVERIFIED','started_at':int(time.time()),'tls_verified':False,'connack':False,'suback':False,'puback':False,'loopback_received':False,'master_delivery':'NOT_TESTED','client_id_mode':'UNIQUE_DIAGNOSTIC_SUFFIX','authentication_note':'Refusal can indicate credentials or Client-ID authentication policy; no profile is changed','error':None}
            self.thread=threading.Thread(target=self.run,args=(profile,revision,master_id,operation),name='bounded-mqtt-diagnostic',daemon=True);self.thread.start()
            return self.status()
    def update(self,**values):
        with self.lock:self.result.update(values)
    def run(self,profile,revision,master_id,operation):
        client=None;started=time.monotonic();connected=threading.Event();subscribed=threading.Event();echo=threading.Event()
        try:
            contract.validate_profile(profile,True)
            context=contract.tls_context(profile)
            with socket.create_connection((profile['host'],profile['port']),timeout=min(8,profile['timeout_s'])) as raw:
                with context.wrap_socket(raw,server_hostname=profile['host']) as tls:
                    self.update(tls_verified=True,tls_version=tls.version(),certificate_expires=tls.getpeercert().get('notAfter'))
            if operation=='tls':self.update(state='PASSED');return
            diagnostic_id=str(uuid.uuid4());nonce=secrets.token_hex(16)
            envelope=message(profile,master_id,'config',{'op':'PROBE','transaction_id':diagnostic_id,'nonce':nonce,'participant':'GATEWAY'})
            topic=contract.topic(profile,'config')
            client=client_for(profile,profile['client_id'][:36]+':diag:'+uuid.uuid4().hex[:8]);client.connect_timeout=min(8,profile['timeout_s'])
            def on_connect(c,u,f,reason,properties):
                if reason!=0:self.update(error='AUTH_FAILED' if getattr(reason,'value',reason) in (4,5,134,135) else 'BROKER_REFUSED');connected.set();return
                self.update(connack=True);connected.set()
                if operation=='roundtrip':c.subscribe(topic,qos=1)
            def on_subscribe(c,u,mid,codes,properties):
                granted=len(codes)==1 and getattr(codes[0],'value',codes[0])==1
                self.update(suback=granted,error=None if granted else 'SUBSCRIPTION_REJECTED');subscribed.set()
            def on_message(c,u,packet):
                # Never return unsolicited broker payloads. Preview only our own validated probe.
                try:
                    parsed=contract.envelope(packet.payload,packet.topic,profile,retained=packet.retain)
                    if parsed['message_id']==envelope['message_id'] and parsed['device_id']=='GATEWAY' and parsed['data'].get('nonce')==nonce:
                        self.update(loopback_received=True,received_at=int(time.time()),received_preview={'message_type':'config','op':'PROBE','participant':'GATEWAY','message_id':envelope['message_id']});echo.set()
                except (contract.ContractError,ValueError,TypeError):pass
            client.on_connect=on_connect;client.on_subscribe=on_subscribe;client.on_message=on_message
            client.connect(profile['host'],profile['port'],profile['keepalive_s']);client.loop_start()
            if not connected.wait(8):self.update(error='CONNACK_TIMEOUT');return
            if not self.status()['connack']:return
            if operation=='broker':self.update(state='PASSED');return
            if not subscribed.wait(6) or not self.status()['suback']:self.update(error='SUBSCRIPTION_REJECTED_OR_TIMEOUT');return
            info=client.publish(topic,contract.canonical(envelope),qos=1,retain=False);info.wait_for_publish(timeout=5)
            self.update(puback=info.is_published(),publish_topic=topic)
            if not echo.wait(5):self.update(error='LOOPBACK_NOT_RECEIVED');return
            self.update(state='PASSED' if self.status()['puback'] else 'FAILED',error=None if self.status()['puback'] else 'PUBACK_TIMEOUT')
        except ssl.SSLError:self.update(error='TLS_VERIFICATION_FAILED')
        except contract.ContractError as error:self.update(error=error.code)
        except (OSError,ValueError,RuntimeError):self.update(error='NETWORK_OR_BROKER_FAILED')
        except Exception:self.update(error='DIAGNOSTIC_FAILED')
        finally:
            if client:
                try:client.disconnect();client.loop_stop()
                except Exception:pass
            result=self.status()
            if result['state']=='RUNNING':self.update(state='FAILED',error=result.get('error') or 'UNKNOWN_OUTCOME')
            self.update(finished_at=int(time.time()),duration_s=round(time.monotonic()-started,3))

diagnostics=Diagnostics()
def install(app):
    @app.route('/api/mqtt/diagnostics',methods=['GET','POST'])
    @account_settings.protected
    def broker_diagnostics(db,actor):
        if actor['must_change'] or actor['role'] not in ('creator','administrator'):return jsonify(error='ADMINISTRATOR_REQUIRED'),403
        if request.method=='GET':return jsonify(diagnostics.status())
        try:
            contract.require(request.is_json and 0<(request.content_length or 0)<=512)
            data=contract.loads(request.get_data(),512)
            contract.require(type(data) is dict)
            contract.require(set(data)=={'expected_revision','master_id','operation'} and data['operation'] in ('tls','broker','roundtrip'))
            contract.require(contract.safe_id(data['master_id']))
            store=mqtt_api.service().store;state=store.read()
            contract.require(type(data['expected_revision']) is int and data['expected_revision']==state['revision'],code='REVISION_CONFLICT')
            connection=database.get_connection()
            try:master=connection.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_role='MASTER' AND device_enrolled=1 AND enabled=1",(data['master_id'],)).fetchone()
            finally:connection.close()
            contract.require(master is not None,code='UNAUTHORIZED')
            profile=store.profile();contract.require(profile is not None,code='PROFILE_REQUIRED')
            return jsonify(diagnostics.start(profile,state['revision'],data['master_id'],data['operation'])),202
        except contract.ContractError as error:return jsonify(error={'code':error.code,'message':'Diagnostic not started; active profile unchanged'}),409
