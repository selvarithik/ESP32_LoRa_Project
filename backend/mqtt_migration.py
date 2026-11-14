"""One-time legacy environment reader. Migration stages; it never activates."""
import json
from pathlib import Path
from runtime_paths import resource_root
import mqtt_contract as c

def example_profile():
    path=resource_root()/'deployment/profile.example.json'
    if path.is_file():return json.loads(path.read_text(encoding='utf-8'))
    return dict(profile_name='Gateway TLS',provider='CUSTOM',host='broker.example.invalid',
                port=8883,mqtt_version='3.1.1',tls=True,ca_cert='',username='',password='',
                client_id='example-gateway',keepalive_s=60,timeout_s=10,qos_default=1,
                topic_prefix='example/gateway',gateway_id='LAB')

def migrate(store,environment):
    state=store.read()
    if state.get('active') or state.get('pending') or state['transaction'].get('migration_checked') or not environment.get('GATEWAY_MQTT_HOST'):
        return
    try:
        profile=example_profile()
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
