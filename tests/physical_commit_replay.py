"""Replay an already committed decision while a fresh ESP32 draft exists.

No profile activation, new decision, credential change or device command occurs.
"""
import argparse
import json
from pathlib import Path
import sys
import threading
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
FIRMWARE=ROOT.parent/'ESP32_LoRa_ESP32_Firmware'
sys.path.insert(0,str(ROOT/'backend'))
sys.path.append(r'C:\Users\Admin\.platformio\penv\Lib\site-packages')
sys.path.append(str(FIRMWARE/'tools'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true',required=True);parser.parse_args()
    from device_acceptance import usb,wait_ready
    from mqtt_store import Store
    from mqtt_service import client_for,message
    import mqtt_contract as contract
    store=Store(ROOT/'data/gateway.db',ROOT/'data/mqtt-secrets.bin')
    journal=store.read();profile=store.profile();before=wait_ready();state=before['mqtt']
    if journal['transaction']['state']!='COMMITTED' or state.get('pending_configured') or state['shared_revision']!=journal['shared_revision']:
        raise SystemExit('Existing state unsuitable; no test changes made')
    candidate=json.loads((FIRMWARE/'deployment/profile.example.json').read_text(encoding='utf-8'))
    candidate.update(client_id=state['active_client_id'],password='')
    staged=usb({'op':'mqtt_action','action':'candidate','request':{'expected_revision':state['revision'],'profile':candidate}})
    if not staged.get('pending'):raise SystemExit('Draft staging rejected')
    draft_id=staged['transaction']['transaction_id']
    client=client_for(profile,'REPLAY_DIAG_'+uuid.uuid4().hex[:10])
    subscribed=threading.Event();ack=threading.Event()
    old_id=journal['transaction']['transaction_id']
    def connected(c,u,f,reason,properties):
        if reason==0:c.subscribe(contract.topic(profile,'config'),1)
    def received(c,u,msg):
        try:
            d=contract.envelope(bytes(msg.payload),msg.topic,profile,retained=msg.retain)
            data=d['data']
            if d['master_id']==before['device_id'] and data.get('op')=='SWITCH_COMMITTED' and data.get('participant')=='MASTER' and data.get('transaction_id')==old_id and data.get('shared_revision')==journal['shared_revision']:
                ack.set()
        except contract.ContractError:pass
    client.on_connect=connected;client.on_subscribe=lambda *args:subscribed.set();client.on_message=received
    result={'prior_commit_acknowledged':False,'fresh_draft_preserved':False,'active_preserved':False,'cancelled':False}
    try:
        client.connect(profile['host'],profile['port'],60);client.loop_start()
        if subscribed.wait(15):
            data={'op':'SWITCH_CONFIRM','transaction_id':old_id,'digest':contract.digest(contract.snapshot(profile,journal['shared_revision'])),
                  'shared_revision':journal['shared_revision'],'participant':'GATEWAY'}
            d=message(profile,before['device_id'],'config',data)
            client.publish(contract.topic(profile,'config'),contract.canonical(d),qos=1)
            result['prior_commit_acknowledged']=ack.wait(15)
        after=usb({'op':'status'})['mqtt']
        result['fresh_draft_preserved']=after['transaction']['transaction_id']==draft_id and after['transaction']['state']=='PENDING' and not after['transaction'].get('decision')
        result['active_preserved']=after['active_fingerprint']==state['active_fingerprint'] and after['shared_revision']==state['shared_revision']
    finally:
        current=usb({'op':'status'})['mqtt']
        if current.get('pending_configured') and current['transaction']['transaction_id']==draft_id:
            usb({'op':'mqtt_action','action':'cancel','request':{'expected_revision':current['revision'],'transaction_id':draft_id}})
        result['cancelled']=not usb({'op':'status'})['mqtt'].get('pending_configured')
        client.disconnect();client.loop_stop()
    result['passed']=all(result.values())
    (ROOT/'docs/PHYSICAL_COMMIT_REPLAY_EVIDENCE.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2));return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
