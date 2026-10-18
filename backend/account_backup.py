"""Consistent SQLite backups, verified before account migrations/recovery."""
from datetime import datetime,timezone
from pathlib import Path
import sqlite3
import uuid

def backup(source):
    source=Path(source)
    folder=source.parent/'account-backups';folder.mkdir(exist_ok=True)
    target=folder/(source.stem+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]+'.sqlite3')
    original=sqlite3.connect(source);copy=sqlite3.connect(target)
    try:
        original.backup(copy)
        if copy.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Account backup verification failed')
        if original.execute("SELECT 1 FROM sqlite_master WHERE name='accounts'").fetchone():
            if original.execute('SELECT count(*) FROM accounts').fetchone()[0]!=copy.execute('SELECT count(*) FROM accounts').fetchone()[0]:raise RuntimeError('Account backup count differs')
    finally:original.close();copy.close()
    return target
