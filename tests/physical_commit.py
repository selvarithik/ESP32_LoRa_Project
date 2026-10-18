"""Explicit live identical-profile commit using the actual Gateway journal and ESP32.

No broker endpoint, credential or client ID is changed. Shared revision advances on
both peers through the real transaction. No device commands are published.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
FIRMWARE=ROOT.parent/'ESP32_LoRa_ESP32_Firmware'
sys.path.insert(0,str(ROOT/'backend'))
sys.path.append(r'C:\Users\Admin\.platformio\penv\Lib\site-packages')
sys.path.append(str(FIRMWARE/'tools'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true',required=True)
    parser.add_argument('--confirm-identical-profile',action='store_true',required=True)
    parser.parse_args()
    from device_acceptance import usb,wait_ready
    from mqtt_store import Store
    from mqtt_service import Service,client_for
    import database,device_api,mqtt_contract as contract
    physical=wait_ready()
    while physical['uptime_ms']<65000:time.sleep(1);physical=usb({'op':'status'})
    before=physical['mqtt'];master=physical['device_id']
    store=Store(ROOT/'data/gateway.db',ROOT/'data/mqtt-secrets.bin')
    original=store.profile();journal=store.read()
    if before['pending_configured'] or journal.get('pending'):raise SystemExit('Existing candidate preserved; commit test not started')
    if before.get('shared_revision',0)!=journal['shared_revision']:raise SystemExit('Shared revisions differ; no commit test started')
    profile=json.loads((FIRMWARE/'deployment/profile.example.json').read_text(encoding='utf-8'))
    profile.update(client_id=before['active_client_id'],password='')
    # The identity was physically read from COM8; preserve any existing enrolled record.
    database.initialize_database();device_api.migrate()
    db=device_api.connect()
    try:existing=db.execute('SELECT * FROM nodes WHERE node_id=?',(master,)).fetchone()
    finally:db.close()
    if existing and (not existing['enabled'] or (existing['device_enrolled'] and existing['device_role']!='MASTER')):
        raise SystemExit('Existing registration differs; no user settings overwritten')
    if not existing or not existing['device_enrolled']:
        device_api.enroll(master,existing['name'] if existing else master,'MASTER')
    if not Service.authorized(master,master):raise SystemExit('Master is not authorized')
    staged=usb({'op':'mqtt_action','action':'candidate','request':{'expected_revision':before['revision'],'profile':profile}})
    if not staged.get('pending'):raise SystemExit('Physical staging rejected')
    service=Service(store,False);service.profile=original
    candidate=dict(original);candidate['password']=''
    draft=store.stage(candidate,journal['revision'])
    client=client_for(original,'COMMIT_DIAG_'+uuid.uuid4().hex[:10])
    errors=[]
    def connected(c,u,f,reason,properties):
        service.state='connected' if reason==0 else 'disconnected'
        if reason==0:
            for kind in ('config','status','events'):c.subscribe(contract.topic(original,kind),1)
    def received(c,u,msg):
        try:service.handle(msg.topic,bytes(msg.payload),msg.retain)
        except contract.ContractError as error:
            if error.code not in errors:errors.append(error.code)
    client.on_connect=connected;client.on_message=received
    evidence={'ready':False,'committed':False,'same_profile_preserved':False,'errors':errors,
              'scope':'Actual Gateway journal and physical ESP32; identical-profile commit only'}
    decision=False
    try:
        client.connect(original['host'],original['port'],60);client.loop_start()
        deadline=time.monotonic()+55
        while service.state!='connected' and time.monotonic()<deadline:time.sleep(.1)
        service.test_candidate(draft['revision'],master)
        while time.monotonic()<deadline:
            while not service.outgoing.empty():
                d=service.outgoing.get_nowait()
                if d['message_type']=='config':client.publish(contract.topic(original,'config'),contract.canonical(d),qos=1)
            state=store.read()
            if state['transaction']['state'] in ('READY_TO_CONFIRM','FAILED'):break
            time.sleep(.1)
        state=store.read();evidence['ready']=state['transaction']['state']=='READY_TO_CONFIRM'
        if evidence['ready']:
            service.confirm(state['revision'],state['transaction']['transaction_id']);decision=True
            deadline=time.monotonic()+35
            while time.monotonic()<deadline and store.read()['transaction']['state']!='COMMITTED':time.sleep(.1)
            evidence['committed']=store.read()['transaction']['state']=='COMMITTED'
            if evidence['committed']:
                time.sleep(5) # The Master activates the durable profile with its defined reboot.
                after=wait_ready()
                evidence.update(master_state=after['mqtt']['transaction']['state'],
                                master_shared_revision=after['mqtt']['shared_revision'],
                                gateway_shared_revision=store.read()['shared_revision'],
                                same_profile_preserved=after['mqtt']['active_fingerprint']==before['active_fingerprint'] and store.profile()==original)
        evidence['passed']=evidence['committed'] and evidence.get('master_state')=='COMMITTED' and evidence.get('master_shared_revision')==evidence.get('gateway_shared_revision') and evidence['same_profile_preserved']
    finally:
        if not decision:
            state=store.read()
            if state.get('pending'):service.cancel(state['revision'],state['transaction']['transaction_id'])
            q=usb({'op':'status'})['mqtt']
            if q['pending_configured']:usb({'op':'mqtt_action','action':'cancel','request':{'expected_revision':q['revision'],'transaction_id':q['transaction']['transaction_id']}})
        # A durable COMMIT is retained for recovery; it is never cancelled here.
        service.stop()
        if service.candidate_client:service.candidate_client.disconnect();service.candidate_client.loop_stop()
        client.disconnect();client.loop_stop()
    (ROOT/'docs/PHYSICAL_COMMIT_EVIDENCE.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(evidence,indent=2))
    return 0 if evidence['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
