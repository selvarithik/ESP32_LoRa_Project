"""Local operator enrollment. Stores Master tokens in a local protected file; never enrolls demo devices."""
import argparse
import database
import device_api

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--role', choices=['MASTER', 'NODE'], required=True)
    parser.add_argument('--master-id', default='')
    parser.add_argument('--node-address', default='')
    parser.add_argument('--rotate-token', action='store_true')
    parser.add_argument('--local-token', action='store_true', help='Explicitly provision a missing direct-Node credential; preserve an existing token')
    args = parser.parse_args()
    database.initialize_database()
    device_api.migrate()
    if args.local_token:
        import secrets,hashlib
        with database.get_connection() as db:
            row=db.execute('SELECT device_token_hash FROM nodes WHERE node_id=? AND device_enrolled=1',(args.id,)).fetchone()
            if not row:raise SystemExit('Device not enrolled; no credential changed')
            if row['device_token_hash']:raise SystemExit('Existing credential preserved; no credential changed')
            token=secrets.token_hex(32)
            device_api.store_local_token(args.id,token)
            db.execute('UPDATE nodes SET device_token_hash=? WHERE node_id=?',(hashlib.sha256(token.encode()).hexdigest(),args.id))
    elif args.rotate_token:
        import secrets,hashlib
        token=secrets.token_hex(32)
        with database.get_connection() as db:
            row=db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_role='MASTER' AND device_enrolled=1",(args.id,)).fetchone()
            if not row:raise SystemExit('Master is not enrolled; nothing changed')
            device_api.store_local_token(args.id,token)
            db.execute("UPDATE nodes SET device_token_hash=? WHERE node_id=?",(hashlib.sha256(token.encode()).hexdigest(),args.id))
    else:
        token = device_api.enroll(args.id, args.name, args.role, args.master_id, args.node_address)
        if token:device_api.store_local_token(args.id,token)
    print('Enrolled:', args.id)
    if token:
        print('Master credential saved to a local protected device-token file; use USB provisioning.')
