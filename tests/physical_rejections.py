"""Explicit bounded physical TLS/auth rejection tests; active profile is preserved."""
import argparse
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import sys
import time
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT=Path(__file__).resolve().parents[1]
FIRMWARE=ROOT.parent/'ESP32_LoRa_ESP32_Firmware'
sys.path.append(r'C:\Users\Admin\.platformio\penv\Lib\site-packages')
sys.path.append(str(FIRMWARE/'tools'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true',required=True)
    parser.parse_args()
    from device_acceptance import usb,wait_ready
    before=wait_ready()['mqtt']
    if before['pending_configured']:raise SystemExit('Existing candidate preserved; tests not started')
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Untrusted physical test CA')])
    now=datetime.now(timezone.utc)
    ca=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True,path_length=None),True).sign(key,hashes.SHA256())
    outcomes=[]
    for mode,expected in (('untrusted_ca','TLS_FAILED'),('wrong_credentials','AUTH_FAILED')):
        state=usb({'op':'status'})['mqtt']
        profile=json.loads((FIRMWARE/'deployment/profile.example.json').read_text(encoding='utf-8'))
        profile.update(client_id=state['active_client_id'],profile_name='Physical rejection validation',password='')
        if mode=='untrusted_ca':profile['ca_cert']=ca.public_bytes(serialization.Encoding.PEM).decode()
        staged=usb({'op':'mqtt_action','action':'candidate','request':{'expected_revision':state['revision'],'profile':profile}})
        if not staged.get('pending'):raise SystemExit('Physical staging rejected; no active change requested')
        try:
            if mode=='wrong_credentials':
                profile['password']='public-invalid-test-credential'
                result=usb({'op':'mqtt','request':{'expected_revision':staged['revision'],'profile':profile}})
                if not result.get('ok'):raise RuntimeError('Test-only secret provisioning rejected')
            revision=usb({'op':'status'})['mqtt']['revision']
            usb({'op':'mqtt_action','action':'test','request':{'expected_revision':revision}})
            deadline=time.monotonic()+65
            while time.monotonic()<deadline:
                current=usb({'op':'status'})['mqtt']
                if current['transaction']['state'] in ('FAILED','ROLLED_BACK'):break
                time.sleep(.5)
            outcomes.append({'test':mode,'state':current['transaction']['state'],
                             'reason':current['transaction'].get('reason'),
                             'active_preserved':bool(current.get('active_fingerprint')) and current['active_fingerprint']==before['active_fingerprint'],
                             'passed':current['transaction']['state']=='FAILED' and current['transaction'].get('reason')==expected and current['active_fingerprint']==before['active_fingerprint']})
        finally:
            state=usb({'op':'status'})['mqtt']
            if state['pending_configured']:
                usb({'op':'mqtt_action','action':'cancel','request':{'expected_revision':state['revision'],'transaction_id':state['transaction']['transaction_id']}})
    evidence={'tests':outcomes,'passed':all(row['passed'] for row in outcomes)}
    (ROOT/'docs/PHYSICAL_REJECTION_EVIDENCE.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(evidence,indent=2))
    return 0 if evidence['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
