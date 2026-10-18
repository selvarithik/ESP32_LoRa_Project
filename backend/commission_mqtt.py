"""Local console provisioning. Secret input is never echoed, logged or exported."""
import argparse
import getpass
import json
from pathlib import Path
from mqtt_store import Store
from mqtt_contract import ContractError, validate_profile
import database

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--revision',type=int,required=True)
    parser.add_argument('--pending-password',action='store_true')
    args=parser.parse_args()
    try:
        profile=json.loads(args.profile.read_text(encoding='utf-8'))
        profile['password']=getpass.getpass('MQTT password: ')
        store=Store(database.DATABASE,Path(database.DATABASE).parent/'mqtt-secrets.bin')
        if args.pending_password:
            validate_profile(profile,True)
            reference=store.secrets.put(profile.pop('password'))
            def apply(s):
                if s.get('pending')!=profile or s['transaction']['state']!='PENDING':raise ContractError('REVISION_CONFLICT')
                s['pending_secret_ref']=reference;s['secret_revision']+=1
            store.change(args.revision,apply)
        else:store.commission(profile,args.revision)
        print('Local commissioning saved. Verify ACLs before starting the MQTT service.')
    except (ContractError,ValueError,OSError):
        print('Commissioning rejected. Check profile, storage and current revision; no secret details displayed.')
        return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
