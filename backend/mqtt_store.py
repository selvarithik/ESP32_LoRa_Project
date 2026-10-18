"""Additive SQLite journal. Recoverable secrets live outside database/export data."""
import base64
import copy
import ctypes
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
import uuid
import mqtt_contract as contract

class SecretFile:
    def __init__(self,path):self.path=Path(path);self.lock=threading.RLock()
    @staticmethod
    def protect(raw, decrypt=False):
        if os.name!='nt':return raw
        class Blob(ctypes.Structure):
            _fields_=[('size',ctypes.c_ulong),('data',ctypes.POINTER(ctypes.c_ubyte))]
        buffer=ctypes.create_string_buffer(raw);source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
        api=ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
        if not api(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):
            raise contract.ContractError('STORAGE_FAILED')
        try:return ctypes.string_at(target.data,target.size)
        finally:ctypes.windll.kernel32.LocalFree(target.data)
    def read(self):
        if not self.path.exists():return {}
        try:return json.loads(self.protect(self.path.read_bytes(),True).decode())
        except Exception:raise contract.ContractError('SECRET_STORAGE_UNAVAILABLE') from None
    def get(self,key):
        with self.lock:return self.read().get(key,'')
    def put(self,value):
        with self.lock:
            values=self.read();key=secrets.token_hex(16);values[key]=value
            self.path.parent.mkdir(parents=True,exist_ok=True)
            tmp=self.path.with_suffix('.tmp')
            fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
            with os.fdopen(fd,'wb') as f:
                f.write(self.protect(json.dumps(values).encode()));f.flush();os.fsync(f.fileno())
            os.replace(tmp,self.path)
            return key

class Connection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

class Store:
    def __init__(self, database, secret_file):
        self.database=Path(database);self.secrets=SecretFile(secret_file)
        self.database.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS mqtt_configuration (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, document TEXT NOT NULL)')
            initial={'schema_version':1,'revision':0,'shared_revision':0,'secret_revision':0,'transaction':{'state':'IDLE'}}
            db.execute('INSERT OR IGNORE INTO mqtt_configuration VALUES (1,0,?)',(json.dumps(initial),))
            db.execute('CREATE TABLE IF NOT EXISTS mqtt_chat_outbox (message_id TEXT PRIMARY KEY,envelope TEXT NOT NULL,expires_at INTEGER NOT NULL,next_attempt REAL NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,state TEXT NOT NULL)')
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='chat_messages'").fetchone():
                columns={row[1] for row in db.execute('PRAGMA table_info(chat_messages)')}
                if 'delivery_semantics' not in columns:db.execute("ALTER TABLE chat_messages ADD COLUMN delivery_semantics TEXT NOT NULL DEFAULT 'LEGACY_LOCAL_STORAGE'")
            db.execute('CREATE TABLE IF NOT EXISTS mqtt_receipts (master_id TEXT, device_id TEXT, message_id TEXT, fingerprint TEXT NOT NULL, outcome TEXT NOT NULL, received_at REAL NOT NULL, PRIMARY KEY(master_id,device_id,message_id))')
    def connect(self):
        db=sqlite3.connect(self.database,timeout=5,factory=Connection);db.row_factory=sqlite3.Row;return db
    def read(self):
        with self.connect() as db:return json.loads(db.execute('SELECT document FROM mqtt_configuration WHERE id=1').fetchone()[0])
    def public(self):
        state=self.read()
        state['secret_state']={'password_configured':bool(state.get('active_secret_ref')),'pending_password_configured':bool(state.get('pending_secret_ref'))}
        for k in ('active_secret_ref','pending_secret_ref','previous_secret_ref'):state.pop(k,None)
        for k in ('active','pending','previous'):
            if k in state:state[k].pop('password',None)
        return state
    def profile(self,which='active'):
        state=self.read();profile=state.get(which)
        if profile is None:return None
        profile['password']=self.secrets.get(state.get(which+'_secret_ref',''));return profile
    def change(self,revision,operation):
        contract.require(contract.integer(revision),'expected_revision','REVISION_CONFLICT')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE');state=json.loads(db.execute('SELECT document FROM mqtt_configuration WHERE id=1').fetchone()[0])
            contract.require(state['revision']==revision and revision<0xffffffff,'expected_revision','REVISION_CONFLICT')
            before=copy.deepcopy(state);operation(state)
            if state!=before:
                state['revision']+=1
                db.execute('UPDATE mqtt_configuration SET revision=?,document=? WHERE id=1',(state['revision'],contract.canonical(state)))
        return self.public()
    def commission(self,profile,revision=0):
        profile=contract.validate_profile(profile,True);reference=self.secrets.put(profile.pop('password'))
        def apply(s):
            contract.require('active' not in s,code='STAGED_SWITCH_REQUIRED')
            s.update(active=profile,active_secret_ref=reference,secret_revision=s['secret_revision']+1)
        return self.change(revision,apply)
    def stage(self,profile,revision):
        profile=dict(profile);contract.require(contract.preserved(profile.get('password')), 'password','PROTECTED_PROVISIONING_REQUIRED')
        profile['password']='';contract.validate_profile(profile);profile.pop('password')
        def apply(s):
            if s.get('pending')==profile:return
            contract.require('pending' not in s,code='TRANSACTION_BUSY')
            s.update(pending=profile,pending_secret_ref=s.get('active_secret_ref',''))
            s['transaction']={'transaction_id':str(uuid.uuid4()),'state':'PENDING','deadline':None,'proofs':{}}
        return self.change(revision,apply)
    def cancel(self,revision,transaction_id):
        def apply(s):
            t=s['transaction'];contract.require(t.get('transaction_id')==transaction_id,code='TRANSACTION_CONFLICT')
            contract.require(t.get('decision')!='COMMIT',code='RECOVERY_REQUIRED')
            if t['state']=='ROLLED_BACK':return
            s.pop('pending',None);s.pop('pending_secret_ref',None);t['state']='ROLLED_BACK';t['reason']='CANCELLED'
        return self.change(revision,apply)
    def testing(self,revision,master_id=None):
        def apply(s):
            contract.require(s['transaction']['state']=='PENDING' and 'pending' in s,code='TRANSACTION_CONFLICT')
            contract.require(s['shared_revision']<0xffffffff,code='REVISION_CONFLICT')
            contract.require(s.get('pending_secret_ref'),code='PROTECTED_PROVISIONING_REQUIRED')
            s['transaction']['master_id']=master_id
            s['transaction'].update(state='TESTING',deadline=int(time.time())+120,test_deadline=int(time.time())+60,proofs={})
        return self.change(revision,apply)
    def test_result(self,transaction_id,proofs,error=None):
        def apply(s):
            t=s['transaction'];contract.require(t.get('transaction_id')==transaction_id and t['state']=='TESTING',code='TRANSACTION_CONFLICT')
            if time.time()>t['test_deadline']:error_code='TIMEOUT'
            else:error_code=error
            t['proofs']=proofs
            if error_code:t.update(state='FAILED',reason=error_code)
            elif all(proofs.get(k) is True for k in ('tls','connack','suback','puback','peer_probe','peer_ready')):t['state']='READY_TO_CONFIRM'
            else:t.update(state='FAILED',reason='COORDINATION_REQUIRED')
        return self.change(self.read()['revision'],apply)
    def confirm(self,revision,transaction_id):
        def apply(s):
            t=s['transaction'];contract.require(t.get('transaction_id')==transaction_id and t['state']=='READY_TO_CONFIRM',code='TRANSACTION_CONFLICT')
            contract.require(time.time()<=t['deadline'],code='TIMEOUT')
            contract.require(all(t['proofs'].get(k) is True for k in ('tls','connack','suback','puback','peer_probe','peer_ready')),code='COORDINATION_REQUIRED')
            # Durable decision precedes network announcement. Activation awaits peer persistence.
            t.update(state='COMMITTING',decision='COMMIT');s['previous']=s.get('active');s['previous_secret_ref']=s.get('active_secret_ref','')
        return self.change(revision,apply)
    def committed(self,transaction_id):
        def apply(s):
            t=s['transaction'];contract.require(t.get('transaction_id')==transaction_id and t.get('decision')=='COMMIT',code='TRANSACTION_CONFLICT')
            if t['state']=='COMMITTED':return
            s['active']=s.pop('pending');s['active_secret_ref']=s.pop('pending_secret_ref');s['shared_revision']+=1;t['state']='COMMITTED'
        return self.change(self.read()['revision'],apply)
    def recover(self,now=None):
        now=time.time() if now is None else now
        def apply(s):
            t=s['transaction']
            if t['state'] not in ('TESTING','READY_TO_CONFIRM','COMMITTING','RECOVERY_REQUIRED'):return
            if t.get('decision')=='COMMIT' or now<1700000000:t.update(state='RECOVERY_REQUIRED',reason='COMMIT_OUTCOME_UNKNOWN')
            elif t.get('deadline',0)<now:
                s.pop('pending',None);s.pop('pending_secret_ref',None);t.update(state='ROLLED_BACK',reason='TIMEOUT')
            else:t.update(state='RECOVERY_REQUIRED',reason='INTERRUPTED_TEST')
        return self.change(self.read()['revision'],apply)
