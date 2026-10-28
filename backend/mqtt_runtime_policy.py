"""Local non-secret proofs bound to verified MQTT deployment scopes."""
import json,hashlib
import mqtt_contract as contract

def binding(store):
 state=store.read();profile=state.get('active')
 if not isinstance(profile,dict):return None
 return {'profile_digest':contract.digest({k:v for k,v in profile.items() if k!='password'}),'secret_binding':hashlib.sha256(state.get('active_secret_ref','').encode()).hexdigest()}

def authorized(store):
 try:
  proof=json.loads((store.database.parent/'mqtt-telemetry-authorization.json').read_text(encoding='utf-8'))
  return (proof.get('schema_version')==1 and proof.get('scope')=='TELEMETRY_ONLY' and proof.get('tls_verified') is True and proof.get('telemetry_persisted') is True and proof.get('status_persisted') is True and proof.get('config_reply_puback') is True and proof.get('suback_qos1') is True and proof.get('binding')==binding(store))
 except (OSError,ValueError,TypeError,AttributeError):return False


def command_authorized(store):
 """Extend only the verified active telemetry profile to device commands."""
 if not authorized(store):return False
 try:
  proof=json.loads((store.database.parent/'mqtt-command-authorization.json').read_text(encoding='utf-8'))
  return (proof.get('schema_version')==1 and proof.get('scope')=='TELEMETRY_COMMANDS'
          and proof.get('binding')==binding(store) and proof.get('tls_verified') is True
          and proof.get('command_puback') is True and proof.get('command_ack_suback_qos1') is True
          and proof.get('master_ack_persisted') is True and proof.get('master_response_persisted') is True)
 except (OSError,ValueError,TypeError,AttributeError):return False
