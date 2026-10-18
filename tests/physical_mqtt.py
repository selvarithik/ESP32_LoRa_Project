"""Explicit bounded live acceptance against one physical Master; isolated Gateway DB."""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true',required=True)
    parser.add_argument('--master-id',required=True)
    args=parser.parse_args()
    from mqtt_store import Store
    sys.path.append(r'C:\Users\Admin\.platformio\penv\Lib\site-packages')
    sys.path.append(str(ROOT.parent/'ESP32_LoRa_ESP32_Firmware'/'tools'))
    from device_acceptance import wait_ready
    physical=wait_ready()
    actual=Store(ROOT/'data/gateway.db',ROOT/'data/mqtt-secrets.bin')
    profile=actual.profile();shared_revision=actual.read()['shared_revision']
    # The existing fixture redirects every model to a disposable database before server import.
    from gateway_fixture import seed
    seed()
    import device_api, mqtt_api, chat_manager, mqtt_contract as contract
    from mqtt_service import client_for, message
    device_api.enroll(args.master_id,'Physical acceptance Master','MASTER')
    service=mqtt_api.service()
    service.store.commission(profile)
    service.store.change(service.store.read()['revision'],lambda state:state.update(shared_revision=shared_revision))
    service.profile=profile
    client=client_for(profile,'PHYSICAL_'+uuid.uuid4().hex[:12])
    evidence={'usb_clock_seeded':physical['usb_clock_seeded'],'connack':False,'physical_compare':False,'physical_packets_persisted':0,
              'chat_state':'UNKNOWN','errors':[],'scope':'Physical ESP32 + live TLS broker + isolated Gateway database'}
    def connected(c,u,f,reason,properties):
        evidence['connack']=reason==0
        service.state='connected' if reason==0 else 'disconnected'
        if reason==0:
            for kind in ('config','status','events','command_ack','chat/ack'):
                c.subscribe(contract.topic(profile,kind),qos=1)
    def received(c,u,msg):
        try:
            data=contract.envelope(msg.payload,msg.topic,profile,retained=msg.retain)
            if data['device_id']!=args.master_id:return
            service.handle(msg.topic,bytes(msg.payload),msg.retain)
            if data['message_type']=='config' and data['data']['op']=='COMPARE':evidence['physical_compare']=True
            if 'packet' in data['data']:evidence['physical_packets_persisted']+=1
        except contract.ContractError as error:
            if error.code not in evidence['errors']:evidence['errors'].append(error.code)
        except Exception:
            evidence['errors'].append('HANDLER_FAILED')
    client.on_connect=connected
    client.on_message=received
    try:
        client.connect(profile['host'],profile['port'],60)
        client.loop_start()
        deadline=time.monotonic()+55
        while not evidence['connack'] and time.monotonic()<deadline:time.sleep(.1)
        row=chat_manager.send_message('GATEWAY',args.master_id,'Physical acceptance receipt check')['message']
        client.publish(contract.topic(profile,'config'),contract.canonical(message(profile,args.master_id,'config',
            {'op':'COMPARE','snapshot':contract.snapshot(profile,shared_revision),'digest':contract.digest(contract.snapshot(profile,shared_revision))})),qos=1)
        service.drain_chat()
        while time.monotonic()<deadline:
            service.drain_chat()
            while not service.outgoing.empty():
                envelope=service.outgoing.get_nowait()
                info=client.publish(contract.topic(profile,envelope['message_type']),contract.canonical(envelope),qos=1)
                info.wait_for_publish(timeout=5)
                if envelope['message_type']=='chat/message' and info.is_published():service.chat_state(envelope['message_id'],'BROKER_ACCEPTED')
            evidence['chat_state']=chat_manager.get_message(row['message_id'])['status']
            if evidence['physical_compare'] and evidence['physical_packets_persisted'] and evidence['chat_state']=='DELIVERED':break
            time.sleep(.1)
        evidence['physical_digest_match']=service.status()['comparison']['status']=='MATCH'
        evidence['passed']=evidence['physical_digest_match'] and evidence['connack'] and evidence['physical_compare'] and evidence['physical_packets_persisted']>0 and evidence['chat_state']=='DELIVERED' and not evidence['errors']
    finally:
        client.disconnect()
        client.loop_stop()
    (ROOT/'docs/PHYSICAL_MQTT_EVIDENCE.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(evidence,indent=2))
    return 0 if evidence['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
