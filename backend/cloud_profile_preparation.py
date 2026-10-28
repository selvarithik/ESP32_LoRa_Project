"""Offline profile preparation only: no sockets, store, Flask application or worker imports."""
from datetime import datetime,timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes
import mqtt_contract as contract
BROKERS={
 'EMQX':{'host':'n1161c10.ala.eu-central-1.emqxsl.com','mqtt_tls_port':8883,'wss_port':8084,'wss_path':'/mqtt'},
 'HIVEMQ':{'host':'3e56a5883e564276920c2d356aa34c94.s1.eu.hivemq.cloud','mqtt_tls_port':8883,'wss_port':8884,'wss_path':'/mqtt'}}
IDENTITIES={'MASTER':('ESP32_MASTER_01','CL_ID_ESP32_MASTER_01'),'GATEWAY':('ESP32GATEWAY','CL_ID_ESP32GATEWAY')}
def certificate_info(pem):
 certs=contract.certificates(pem);now=datetime.now(timezone.utc);result=[]
 for c in certs:
  if not c.not_valid_before_utc<=now<=c.not_valid_after_utc:raise ValueError('CA_OUTSIDE_VALIDITY')
  result.append({'subject':c.subject.rfc4514_string(),'issuer':c.issuer.rfc4514_string(),'is_ca':True,'not_after':c.not_valid_after_utc.isoformat(),'sha256':c.fingerprint(hashes.SHA256()).hex()})
 return result

def prepare(ca_by_provider):
 profiles={};manifest={'schema_version':1,'activation':'NOT_ACTIVATED','live_broker_tests':'NOT_APPROVED_NOT_RUN','brokers':BROKERS,'certificates':{},'profiles':[]}
 for provider,connection in BROKERS.items():
  ca=ca_by_provider[provider];manifest['certificates'][provider]={'certificates':certificate_info(ca),'broker_chain_verified':False}
  for side,(username,client_id) in IDENTITIES.items():
   key=provider.lower()+'-'+side.lower();profile=dict(profile_name=provider+'_'+side+'_PREPARED',provider=provider,host=connection['host'],port=8883,mqtt_version='3.1.1',tls=True,ca_cert=ca,username=username,password='',client_id=client_id,keepalive_s=60,timeout_s=10,qos_default=1,topic_prefix='selvarithik/gateway',gateway_id='GW001')
   contract.validate_profile(profile);profiles[key]=profile;manifest['profiles'].append({'file':key+'.json','side':side,'password_state':'PROTECTED_LOCAL_PROVISIONING_REQUIRED','broker_chain_verified':False})
 return profiles,manifest
