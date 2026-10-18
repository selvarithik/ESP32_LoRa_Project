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
    args = parser.parse_args()
    database.initialize_database()
    device_api.migrate()
    if args.rotate_token:
        import secrets,hashlib
        token=secrets.token_hex(32)
        with database.get_connection() as db:
            row=db.execute("SELECT 1 FROM nodes WHERE node_id=? AND device_role='MASTER' AND device_enrolled=1",(args.id,)).fetchone()
            if not row:raise SystemExit('Master is not enrolled; nothing changed')
            device_api.store_local_token(args.id,token)
            db.execute("UPDATE nodes SET device_token_hash=? WHERE node_id=?",(hashlib.sha256(token.encode()).hexdigest(),args.id))
    else:
        token = device_api.enroll(args.id, args.name, args.role, args.master_id, args.node_address)
    print('Enrolled:', args.id)
    if token:
        print('Master credential saved to a local protected device-token file; use USB provisioning.')
