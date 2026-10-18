"""Bounded physical candidate proofs and cancellation; never confirms a broker change."""
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
    args=parser.parse_args()
    from device_acceptance import usb,wait_ready
    from mqtt_store import Store
    from mqtt_service import client_for
    import mqtt_contract as contract
    actual=Store(ROOT/'data/gateway.db',ROOT/'data/mqtt-secrets.bin');profile=actual.profile();shared_revision=actual.read()['shared_revision']
    before=wait_ready()
    while before['uptime_ms']<65000:
        time.sleep(1);before=usb({'op':'status'})
    state=before['mqtt']
    if state.get('shared_revision',0)!=shared_revision:raise SystemExit('Actual peer revisions differ; no test started')
    if state.get('pending_configured'):raise SystemExit('Existing candidate preserved; test not started')
    master=before['device_id']
    candidate=json.loads((FIRMWARE/'deployment/profile.example.json').read_text(encoding='utf-8'));candidate['client_id']=state['active_client_id'];candidate['password']='';candidate['profile_name']='Physical candidate validation'
    staged=usb({'op':'mqtt_action','action':'candidate','request':{'expected_revision':state['revision'],'profile':candidate}})
    if not staged.get('pending'):raise SystemExit('Physical staging rejected')
    from gateway_fixture import seed
    seed()
    import device_api,mqtt_api
    device_api.enroll(master,'Physical candidate Master','MASTER')
    service=mqtt_api.service();service.store.commission(profile);service.store.change(service.store.read()['revision'],lambda s:s.update(shared_revision=shared_revision));service.profile=profile
    pending=dict(profile);pending['password']='';pending['profile_name']='Physical candidate validation'
    draft=service.store.stage(pending,service.store.read()['revision'])
    client=client_for(profile,'CANDIDATE_DIAG_'+uuid.uuid4().hex[:10])
    errors=[]
    def connected(c,u,f,reason,properties):
        service.state='connected' if reason==0 else 'disconnected'
        if reason==0:c.subscribe(contract.topic(profile,'config'),1)
    def received(c,u,msg):
        try:service.handle(msg.topic,bytes(msg.payload),msg.retain)
        except contract.ContractError as error:
            if error.code not in errors:errors.append(error.code)
    client.on_connect=connected;client.on_message=received
    report={'ready_to_confirm':False,'old_profile_preserved':False,'cancelled':False,'errors':errors}
    try:
        client.connect(profile['host'],profile['port'],60);client.loop_start()
        deadline=time.monotonic()+50
        while service.state!='connected' and time.monotonic()<deadline:time.sleep(.1)
        service.test_candidate(draft['revision'],master)
        while time.monotonic()<deadline:
            while not service.outgoing.empty():
                d=service.outgoing.get_nowait()
                client.publish(contract.topic(profile,d['message_type']),contract.canonical(d),qos=1)
            phase=service.store.read()['transaction']['state']
            if phase in ('READY_TO_CONFIRM','FAILED','ROLLED_BACK'):break
            time.sleep(.1)
        result=service.store.read()
        physical=usb({'op':'status'})
        report.update(ready_to_confirm=result['transaction']['state']=='READY_TO_CONFIRM',
                      coordinator_state=result['transaction']['state'],physical_state=physical['mqtt']['transaction']['state'],
                      candidate_runtime=physical['mqtt'].get('candidate_runtime'),
                      proofs=result['transaction'].get('proofs',{}),
                      old_profile_preserved=bool(physical['mqtt']['active_fingerprint']) and physical['mqtt']['active_fingerprint']==state['active_fingerprint'],
                      free_heap=physical.get('free_heap'),minimum_free_heap=physical.get('minimum_free_heap'))
        if result.get('pending'):service.cancel(result['revision'],result['transaction']['transaction_id'])
        time.sleep(1)
    finally:
        current=usb({'op':'status'})['mqtt']
        if current.get('pending_configured'):
            usb({'op':'mqtt_action','action':'cancel','request':{'expected_revision':current['revision'],'transaction_id':current['transaction']['transaction_id']}})
        current=usb({'op':'status'})['mqtt']
        report['cancelled']=not current.get('pending_configured') and current['active_fingerprint']==state['active_fingerprint']
        if service.candidate_client:service.candidate_client.disconnect();service.candidate_client.loop_stop()
        client.disconnect();client.loop_stop()
    report['passed']=report['ready_to_confirm'] and report.get('physical_state')=='READY_TO_CONFIRM' and report['old_profile_preserved'] and report['cancelled']
    (ROOT/'docs/PHYSICAL_CANDIDATE_EVIDENCE.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
