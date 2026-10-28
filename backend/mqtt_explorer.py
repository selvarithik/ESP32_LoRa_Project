"""Read-only observations of validated permanent-worker traffic; scoped probes only."""
from collections import deque
import threading,time,uuid
from flask import request,jsonify
import mqtt_contract as contract
import device_api

class Feed:
 def __init__(self):self.lock=threading.RLock();self.rows=deque(maxlen=200);self.sequence=0
 def record(self,profile,envelope):
  # Headers and a strict summary allowlist, never arbitrary raw payload/strings.
  packet=envelope.get('data',{}).get('packet',{});payload=packet.get('payload',{})
  if isinstance(payload,str):
   try:payload=contract.loads(payload.encode(),4096)
   except (ValueError,TypeError):payload={}
  summary={k:payload[k] for k in ('command_id','status','sensor_id') if isinstance(payload,dict) and k in payload and isinstance(payload[k],str) and len(payload[k])<=128}
  with self.lock:
   self.sequence+=1;self.rows.append(dict(sequence=self.sequence,received_at=time.time(),topic=contract.topic(profile,envelope['message_type']),message_type=envelope['message_type'],message_id=envelope['message_id'],device_id=envelope['device_id'],qos=1,summary=summary))
 def read(self,after=0):
  with self.lock:return {'sequence':self.sequence,'messages':[dict(row) for row in self.rows if row['sequence']>after],'capacity':200,'payload_policy':'VALIDATED_HEADERS_AND_ALLOWLISTED_SUMMARY_ONLY'}

def install(app,service):
 @app.get('/api/mqtt/explorer')
 @device_api.require_admin
 def read():
  try:after=int(request.args.get('after','0'));contract.require(0<=after<=2**53,code='INVALID_CURSOR')
  except (ValueError,contract.ContractError):return jsonify(error='INVALID_CURSOR'),400
  current=service();profile=current.profile
  result=current.explorer.read(after);result['connection_state']=current.state
  result['topics']={kind:contract.topic(profile,kind) for kind in current.SUBSCRIPTIONS if not kind.startswith('chat/')} if profile else {}
  result['publish_types']=['config'] if current.commands_only and current.trust_acl else []
  return jsonify(result)
 @app.post('/api/mqtt/explorer/probe')
 @device_api.require_admin
 def probe():
  data,error=device_api.json_body(1024)
  if error:return error
  try:
   contract.require(set(data)=={'master_id','expected_revision'})
   current=service();contract.require(current.commands_only and current.trust_acl,code='ACL_CONFIRMATION_REQUIRED');contract.require(current.state=='connected' and set(current.SUBSCRIPTIONS)<=current.subscriptions_ready,code='NOT_CONNECTED')
   contract.require(type(data['expected_revision']) is int and data['expected_revision']==current.store.read()['revision'],code='REVISION_CONFLICT')
   contract.require(current.authorized(data['master_id'],data['master_id']),code='UNAUTHORIZED')
   from mqtt_service import message
   envelope=message(current.profile,data['master_id'],'config',{'op':'PROBE','participant':'GATEWAY','nonce':uuid.uuid4().hex,'transaction_id':str(uuid.uuid4())})
   current.enqueue(envelope)
   return jsonify(state='QUEUED',message_id=envelope['message_id'],topic=contract.topic(current.profile,'config'),delivery='NOT_YET_ACKNOWLEDGED'),202
  except (contract.ContractError,TypeError) as e:return jsonify(error=getattr(e,'code','INVALID_REQUEST')),409
