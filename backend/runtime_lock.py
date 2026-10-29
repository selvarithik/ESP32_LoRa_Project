"""OS-released single-instance lock; a stale PID file never owns the service."""
import os
from pathlib import Path
class AlreadyRunning(RuntimeError):pass
class InstanceLock:
 def __init__(self,folder,name='gateway.lock'):
  if Path(name).name!=name:raise ValueError('INVALID_LOCK_NAME')
  self.path=Path(folder)/'runtime'/name;self.file=None
 def acquire(self):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  f=open(self.path,'a+b');f.seek(0,2)
  if f.tell()==0:f.write(b'0');f.flush()
  f.seek(0)
  try:
   if os.name=='nt':
    import msvcrt
    msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
   else:
    import fcntl
    fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except OSError:f.close();raise AlreadyRunning('GATEWAY_ALREADY_RUNNING') from None
  self.file=f;return self
 def close(self):
  if not self.file:return
  self.file.seek(0)
  if os.name=='nt':
   import msvcrt
   msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
  else:
   import fcntl
   fcntl.flock(self.file.fileno(),fcntl.LOCK_UN)
  self.file.close();self.file=None
 def __enter__(self):return self.acquire()
 def __exit__(self,*args):self.close()
