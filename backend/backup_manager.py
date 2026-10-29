"""Encrypted, verified SQLite online snapshots. Never exports plaintext secrets."""
import io,json,os,re,sqlite3,hashlib,zipfile,uuid,time,threading
from pathlib import Path
from datetime import datetime,timezone
from runtime_lock import InstanceLock
MAX_TOTAL=256*1024*1024
class BackupError(RuntimeError):pass

def atomic_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2),encoding='utf-8');os.replace(tmp,path)

def allowed(name):
 return Path(name).name==name and name not in ('.','..','manifest.json') and bool(re.fullmatch(r'[A-Za-z0-9_.-]+',name)) and (Path(name).suffix in ('.db','.sqlite','.sqlite3','.bin','.key','.json'))

def codec(raw,decrypt=False):
 try:
  if decrypt:
   kind,raw=raw[:6],raw[6:]
   if kind==b'SGWB1D' and os.name=='nt':
    from mqtt_store import SecretFile
    return SecretFile.protect(raw,True)
   if kind!=b'SGWB1F':raise ValueError()
  if os.name=='nt' and not decrypt:
   from mqtt_store import SecretFile
   return b'SGWB1D'+SecretFile.protect(raw)
  from cryptography.fernet import Fernet
  key=os.environ.get('GATEWAY_BACKUP_KEY','').encode()
  if not key:raise BackupError('BACKUP_KEY_REQUIRED_ON_NON_WINDOWS')
  f=Fernet(key)
  return f.decrypt(raw) if decrypt else b'SGWB1F'+f.encrypt(raw)
 except BackupError:raise
 except Exception:raise BackupError('BACKUP_ENCRYPTION_OR_IDENTITY_FAILED') from None

def sqlite_bytes(path):
 original=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=5);copy=sqlite3.connect(':memory:');deadline=time.monotonic()+30
 try:
  def progress(*_):
   if time.monotonic()>deadline:raise BackupError('BACKUP_DATABASE_BUSY')
  original.backup(copy,pages=128,progress=progress,sleep=.01)
  if copy.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise BackupError('BACKUP_INTEGRITY_FAILED')
  raw=bytearray(copy.serialize())
  # SQLite deserialize requires rollback-mode header bytes for standalone WAL snapshots.
  # The online backup already contains committed WAL pages; source journal mode is untouched.
  raw[18:20]=b"\x01\x01"
  return bytes(raw)
 finally:original.close();copy.close()

def verify_sqlite(raw):
 db=sqlite3.connect(':memory:')
 try:
  db.deserialize(raw)
  if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise BackupError('BACKUP_INTEGRITY_FAILED')
 finally:db.close()

class Backups:
 def __init__(self,folder,keep=7):self.root=Path(folder).resolve();self.folder=self.root/'backups';self.keep=keep;self.status={'state':'NOT_RUN'};self.stop_event=threading.Event();self.thread=None
 def source_files(self):
  return sorted(p for p in self.root.iterdir() if p.is_file() and not p.is_symlink() and allowed(p.name))
 def unpack(self,path):
  try:
   path=Path(path)
   if path.stat().st_size>MAX_TOTAL*2:raise ValueError()
   raw=codec(path.read_bytes(),True)
   if len(raw)>MAX_TOTAL:raise ValueError()
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    infos=z.infolist()
    if not 1<=len(infos)<=65 or sum(i.file_size for i in infos)>MAX_TOTAL or len(set(i.filename for i in infos))!=len(infos):raise ValueError()
    manifest=json.loads(z.read('manifest.json'));entries=manifest['files']
    if manifest['schema']!=1 or not isinstance(entries,dict) or set(z.namelist())!=set(entries)|{'manifest.json'}:raise ValueError()
    result={}
    for name,meta in entries.items():
     if not allowed(name):raise ValueError()
     content=z.read(name)
     if len(content)!=meta['bytes'] or hashlib.sha256(content).hexdigest()!=meta['sha256']:raise ValueError()
     if meta['sqlite']:verify_sqlite(content)
     result[name]=content
   return manifest,result
  except BackupError:raise
  except Exception:raise BackupError('INVALID_OR_CORRUPT_BACKUP') from None
 def verify(self,path):
  m,_=self.unpack(path);return {'verified':True,'created_at':m['created_at'],'files':len(m['files']),'encrypted':True}
 def create(self,protected=()):
  if (self.root/'restore.pending.json').exists():raise BackupError('RESTORE_IN_PROGRESS')
  self.folder.mkdir(parents=True,exist_ok=True)
  with InstanceLock(self.root,'backup.lock'):
   try:
    files={};manifest={'schema':1,'created_at':datetime.now(timezone.utc).isoformat(),'files':{}};total=0
    for p in self.source_files():
     if p.stat().st_size>MAX_TOTAL:raise BackupError('BACKUP_SIZE_LIMIT')
     is_db=p.suffix in ('.db','.sqlite','.sqlite3');raw=sqlite_bytes(p) if is_db else p.read_bytes();total+=len(raw)
     if total>MAX_TOTAL:raise BackupError('BACKUP_SIZE_LIMIT')
     manifest['files'][p.name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'sqlite':is_db};files[p.name]=raw
    if not files:raise BackupError('NO_DATA_TO_BACK_UP')
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as z:
     for name,content in files.items():z.writestr(name,content)
     z.writestr('manifest.json',json.dumps(manifest))
    target=self.folder/('gateway-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]+'.sgwb');tmp=target.with_suffix('.pending')
    try:
     with open(tmp,'xb') as f:f.write(codec(memory.getvalue()));f.flush();os.fsync(f.fileno())
     self.verify(tmp);os.replace(tmp,target)
    finally:
     if tmp.exists():tmp.unlink()
    self.status={'state':'VERIFIED','last_success':manifest['created_at'],'file':target.name,'files':len(files)};atomic_json(self.folder/'status.json',self.status)
    # Only archives created by this module are eligible; retain corrupt files for inspection.
    archives=sorted(self.folder.glob('gateway-backup-*.sgwb'),key=lambda p:p.stat().st_mtime,reverse=True)
    valid=[]
    for item in archives:
     try:self.verify(item);valid.append(item)
     except BackupError:continue
    for old in valid[self.keep:]:
     if old.resolve() not in {Path(p).resolve() for p in protected}:old.unlink()
    return target
   except Exception:
    self.status={'state':'FAILED','error':'BACKUP_FAILED'};raise
 def due(self,hours):
  for path in sorted(self.folder.glob('gateway-backup-*.sgwb'),key=lambda p:p.stat().st_mtime,reverse=True):
   try:
    verification=self.verify(path)
    self.status={'state':'VERIFIED','last_success':verification['created_at'],'file':path.name,'files':verification['files']}
    if time.time()-path.stat().st_mtime<hours*3600:return False
   except BackupError:continue
  return True
 def start(self,hours):
  if self.thread and self.thread.is_alive():return
  self.stop_event.clear()
  def run():
   while not self.stop_event.is_set():
    try:
     if self.due(hours):self.create()
    except Exception:self.status={'state':'FAILED','error':'BACKUP_FAILED'}
    self.stop_event.wait(60)
  self.thread=threading.Thread(target=run,name='gateway-backup',daemon=True);self.thread.start()
 def stop(self):
  self.stop_event.set()
  if self.thread:self.thread.join(timeout=10)
 def restore(self,path,apply=False):
  manifest,files=self.unpack(path)
  preview={'verified':True,'files':sorted(files),'applied':False,'accounts_sessions_invalidated_on_restart':True}
  if not apply:return preview
  with InstanceLock(self.root):
   pending=self.root/'restore.pending.json';digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
   if pending.exists() and json.loads(pending.read_text())['archive_sha256']!=digest:raise BackupError('INTERRUPTED_RESTORE_REQUIRES_SAME_ARCHIVE')
   if not pending.exists() and self.source_files():self.create(protected=(path,))
   old={};touched=[]
   atomic_json(pending,{'schema':1,'archive_sha256':digest,'state':'IN_PROGRESS'})
   try:
    for name,content in files.items():
     target=self.root/name
     if target.is_symlink():raise BackupError('SYMLINK_RESTORE_REJECTED')
     old[name]=target.read_bytes() if target.exists() else None
     for suffix in ('-wal','-shm','-journal') if manifest['files'][name]['sqlite'] else ():
      side=self.root/(name+suffix)
      if side.is_symlink():raise BackupError('SYMLINK_RESTORE_REJECTED')
      if side.exists():old[name+suffix]=side.read_bytes();side.unlink();touched.append(name+suffix)
     temporary=target.with_suffix(target.suffix+'.restore-tmp');temporary.write_bytes(content);os.replace(temporary,target);touched.append(name)
    pending.unlink();preview['applied']=True;return preview
   except Exception:
    try:
     for name in reversed(touched):
      target=self.root/name
      if old[name] is None:target.unlink(missing_ok=True)
      else:target.write_bytes(old[name])
     pending.unlink()
    except Exception:pass
    raise BackupError('RESTORE_FAILED_CHECK_RECOVERY_MARKER') from None
