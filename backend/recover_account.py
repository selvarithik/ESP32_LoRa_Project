"""Deliberate local account bootstrap/recovery. Default is preview; never run by server."""
import argparse
from pathlib import Path
import sqlite3
from werkzeug.security import generate_password_hash
from account_backup import backup

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,default=Path(__file__).resolve().parents[1]/'data/accounts.sqlite3')
    parser.add_argument('--user',default='admin')
    parser.add_argument('--bootstrap',action='store_true')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();path=args.database
    protected=Path(__file__).resolve().parents[1]/'data'
    if path.resolve() in {(protected/name).resolve() for name in ('gateway.db','mqtt-secrets.bin','session.key')}:
        raise SystemExit('Recovery target is protected application data, not the account database.')
    exists=path.exists();count=0;row=None
    if exists:
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
        try:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            if tables and 'accounts' not in tables:raise SystemExit('Selected file is not an account database; no changes made.')
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='accounts'").fetchone():
                count=db.execute('SELECT count(*) FROM accounts').fetchone()[0]
                row=db.execute('SELECT id,role FROM accounts WHERE username=?',(args.user,)).fetchone()
        finally:db.close()
    if args.bootstrap and count:raise SystemExit('Bootstrap rejected: existing accounts preserved.')
    if not args.bootstrap and not row:raise SystemExit('Existing account required for recovery; role and other accounts are preserved.')
    print('Will '+('create initial creator' if args.bootstrap else 'replace only selected account credential')+' and require password change; unrelated account/data/MQTT stores remain unchanged.')
    if not args.apply:print('Preview only. Add --apply to deliberately perform this operation.');return
    if exists:backup(path)
    path.parent.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(path)
    try:
        db.execute('CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY,username TEXT UNIQUE COLLATE NOCASE NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL,password_hash TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,must_change INTEGER NOT NULL DEFAULT 0)')
        if 'must_change' not in {r[1] for r in db.execute('PRAGMA table_info(accounts)')}:db.execute('ALTER TABLE accounts ADD COLUMN must_change INTEGER NOT NULL DEFAULT 0')
        if args.bootstrap:db.execute("INSERT INTO accounts(username,name,role,password_hash,must_change) VALUES(?,?,'creator',?,1)",(args.user,'Gateway administrator',generate_password_hash('admin')))
        else:db.execute('UPDATE accounts SET password_hash=?,must_change=1,version=version+1 WHERE id=?',(generate_password_hash('admin'),row[0]))
        db.commit()
    finally:db.close()
    print('Completed local operation. Temporary bootstrap access must be replaced through Account Settings.')

if __name__=='__main__':main()
