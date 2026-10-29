"""One-time legacy environment reader. Migration stages; it never activates."""
import json
from pathlib import Path
from runtime_paths import resource_root
import mqtt_contract as c

def migrate(store,environment):
    state=store.read()
    if state.get('active') or state.get('pending') or state['transaction'].get('migration_checked') or not environment.get('GATEWAY_MQTT_HOST'):
        return
    try:
        profile=json.loads((resource_root()/'deployment/profile.example.json').read_text(encoding='utf-8'))
        profile.update(host=environment['GATEWAY_MQTT_HOST'],port=int(environment.get('GATEWAY_MQTT_PORT','8883')),
                       username=environment.get('GATEWAY_MQTT_USER',''),password=environment.get('GATEWAY_MQTT_PASSWORD',''),
                       ca_cert=Path(environment['GATEWAY_MQTT_CA']).read_text(encoding='utf-8'))
        c.validate_profile(profile,True)
        reference=store.secrets.put(profile['password']);profile['password']=''
        staged=store.stage(profile,state['revision'])
        def apply(s):
            s['pending_secret_ref']=reference;s['secret_revision']+=1
            s['transaction'].update(migration_checked=True,reason='MIGRATION_REQUIRED')
        store.change(staged['revision'],apply)
    except (ValueError,OSError,KeyError):
        def rejected(s):s['transaction'].update(migration_checked=True,reason='MIGRATION_REQUIRED')
        store.change(state['revision'],rejected)
