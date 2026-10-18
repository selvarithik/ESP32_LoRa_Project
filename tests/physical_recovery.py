"""Explicit EN-reset fault injection after staging; does not claim a power-cut test."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
FIRMWARE=ROOT.parent/'ESP32_LoRa_ESP32_Firmware'
sys.path.append(r'C:\Users\Admin\.platformio\penv\Lib\site-packages')
sys.path.append(str(FIRMWARE/'tools'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true',required=True)
    parser.parse_args()
    from device_acceptance import usb,wait_ready
    import serial
    initial=wait_ready()
    old=initial['mqtt']
    if old['pending_configured']:raise SystemExit('Existing candidate preserved; test not started')
    profile=json.loads((FIRMWARE/'deployment/profile.example.json').read_text(encoding='utf-8'))
    profile.update(client_id=old['active_client_id'],password='',profile_name='EN-reset acceptance candidate')
    request={'op':'mqtt_action','action':'candidate','request':{'expected_revision':old['revision'],'profile':profile}}
    payload=json.dumps(request,separators=(',',':')).encode()
    port=serial.Serial(port=None,baudrate=115200,timeout=.2)
    port.dtr=False;port.rts=False;port.port='COM8'
    try:
        port.open()
        for offset in range(0,len(payload),64):port.write(payload[offset:offset+64]);time.sleep(.03)
        port.write(b'\n');port.flush();time.sleep(.010)
        port.rts=True;time.sleep(.15);port.rts=False
        time.sleep(4)
    finally:port.close()
    after=usb({'op':'status'})['mqtt']
    evidence={'fault':'EN reset requested 10 ms after staging dispatch; exact flash-write overlap unverified',
              'active_preserved':after.get('active_configured') and after.get('active_fingerprint')==old['active_fingerprint'],
              'journal_state_after_reset':after['transaction']['state'],
              'power_cut_tested':False}
    if after['pending_configured']:
        usb({'op':'mqtt_action','action':'cancel','request':{'expected_revision':after['revision'],'transaction_id':after['transaction']['transaction_id']}})
    final=wait_ready()['mqtt']
    evidence['cleaned']=not final['pending_configured']
    evidence['passed']=evidence['active_preserved'] and evidence['cleaned'] and final['active_configured']
    (ROOT/'docs/PHYSICAL_RECOVERY_EVIDENCE.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(evidence,indent=2))
    return 0 if evidence['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
