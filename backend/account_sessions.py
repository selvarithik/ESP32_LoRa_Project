"""Process-local, revocable sessions. Restart invalidates all browser sessions."""
import hashlib
import secrets
import threading
import time

IDLE_SECONDS=900
_sessions={}
_lock=threading.RLock()
invalidator=None

def _drop(key):
    if _sessions.pop(key,None) is not None and invalidator:invalidator(key)

def expire():
    with _lock:
        for key,value in list(_sessions.items()):
            if time.monotonic()-value[3]>=IDLE_SECONDS:_drop(key)

def create(account_id,version,database):
    token=secrets.token_urlsafe(32)
    with _lock:
        now=time.monotonic()
        for key,value in list(_sessions.items()):
            if now-value[3]>=IDLE_SECONDS:_drop(key)
        if len(_sessions)>=1024:_drop(min(_sessions,key=lambda key:_sessions[key][3]))
        _sessions[hashlib.sha256(token.encode()).hexdigest()]=(account_id,version,str(database),now)
    return token

def valid(token,account_id,version,database):
    if not isinstance(token,str):return False
    key=hashlib.sha256(token.encode()).hexdigest()
    with _lock:
        value=_sessions.get(key)
        if not value:return False
        if value[:3]!=(account_id,version,str(database)) or time.monotonic()-value[3]>=IDLE_SECONDS:
            _drop(key);return False
        _sessions[key]=(*value[:3],time.monotonic());return True

def revoke(token):
    if isinstance(token,str):
        with _lock:_drop(hashlib.sha256(token.encode()).hexdigest())

def revoke_account(account_id,database):
    with _lock:
        for key,value in list(_sessions.items()):
            if value[0]==account_id and value[2]==str(database):_drop(key)
