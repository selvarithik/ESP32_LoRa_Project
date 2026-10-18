"""Authenticated dashboard adapter; existing server middleware enforces account/CSRF."""
import atexit
import os
import json
import threading
from pathlib import Path
from flask import jsonify, request, render_template
import database
import mqtt_contract as contract
from mqtt_store import Store
from mqtt_service import Service

_service=None
_lock=threading.RLock()

def service():
    global _service
    with _lock:
        path=Path(database.DATABASE)
        if _service is None or _service.store.database!=path:
            if _service:_service.stop()
            _service=Service(Store(path,path.parent/'mqtt-secrets.bin'),os.environ.get('GATEWAY_MQTT_TRUST_ACL')=='1')
        return _service

def start():
    from mqtt_migration import migrate
    current=service();migrate(current.store,os.environ);current.store.recover();current.start();atexit.register(current.stop);return current

def install(app):
    service() # Additive schema migration; does not start a broker connection.
    @app.get('/mqtt')
    def mqtt_page():return render_template('mqtt.html')

    @app.get('/api/mqtt')
    def mqtt_state():
        current=service();result=current.store.public();result['runtime']=current.status();result['comparison']=result['runtime']['comparison'];result['defaults']=json.loads((Path(__file__).resolve().parents[1]/'deployment/profile.example.json').read_text(encoding='utf-8'));result['defaults'].pop('password',None);return jsonify(result)

    @app.post('/api/mqtt/<operation>')
    def mqtt_action(operation):
        try:
            contract.require(request.is_json and (request.content_length or 0)<=8192)
            data=contract.loads(request.get_data(),8192);current=service()
            fields={'candidate':{'expected_revision','profile'},'cancel':{'expected_revision','transaction_id'},
                    'test':{'expected_revision','master_id'},'confirm':{'expected_revision','transaction_id'}}
            contract.require(operation in fields and set(data)==fields[operation])
            if operation=='candidate':result=current.store.stage(data['profile'],data['expected_revision'])
            elif operation=='cancel':result=current.cancel(data['expected_revision'],data['transaction_id'])
            elif operation=='test':
                contract.require(current.trust_acl,code='ACL_CONFIRMATION_REQUIRED')
                result=current.test_candidate(data['expected_revision'],data['master_id'])
            else:
                # Do not persist a decision without a running coordinator transport.
                contract.require(current.state=='connected',code='COORDINATION_REQUIRED')
                result=current.confirm(data['expected_revision'],data['transaction_id'])
            return jsonify(result),202 if operation=='test' else 200
        except contract.ContractError as e:
            return jsonify(ok=False,error={'code':e.code,'message':'Operation not applied; inspect the current state','field':e.field}),409 if e.code not in ('INVALID_REQUEST','INVALID_PROFILE') else 400
        except Exception:
            return jsonify(ok=False,error={'code':'STORAGE_FAILED','message':'Operation outcome unknown; reload state'}),503
