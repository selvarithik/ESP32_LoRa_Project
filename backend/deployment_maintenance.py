"""Opt-in telemetry retention; dry run is the default. Never deletes settings/history."""
import sqlite3
from datetime import datetime,timedelta
from pathlib import Path
from runtime_lock import InstanceLock
from backup_manager import Backups

def retention(root,days,apply=False):
 if type(days) is not int or not 7<=days<=3650:raise ValueError('RETENTION_MUST_BE_7_TO_3650_DAYS')
 root=Path(root).resolve();path=root/'gateway.db';cutoff=(datetime.now()-timedelta(days=days)).isoformat()
 with InstanceLock(root):
  db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
  try:count=db.execute('SELECT count(*) FROM telemetry_values WHERE timestamp<?',(cutoff,)).fetchone()[0]
  finally:db.close()
  result={'applied':False,'telemetry_rows_eligible':count,'retention_days':days,'settings_and_commands_preserved':True}
  if apply and count:
   archive=Backups(root).create();db=sqlite3.connect(path,timeout=10)
   try:
    deleted=0
    while True:
     cursor=db.execute('DELETE FROM telemetry_values WHERE id IN (SELECT id FROM telemetry_values WHERE timestamp<? LIMIT 1000)',(cutoff,));db.commit();deleted+=cursor.rowcount
     if cursor.rowcount<1000:break
    result.update(applied=True,deleted=deleted,backup=archive.name)
   finally:db.close()
  return result
