"""Bounded physical status ingestion into the actual Gateway database.

No commands, profile changes, chat messages or ACL assertions are sent.
"""
import argparse
import json
from pathlib import Path
import queue
import sys
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
sys.path.append(r'C:\Users\Admin\.platformio\penv\Lib\site-packages')
sys.path.append(str(ROOT.parent/'ESP32_LoRa_ESP32_Firmware'/'tools'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true',required=True);parser.parse_args()
    from device_acceptance import wait_ready
    from mqtt_store import Store
    from mqtt_service import Service,client_for,message
    import mqtt_contract as contract
    import database,device_api
    physical=wait_ready();master=physical['device_id']
    store=Store(ROOT/'data/gateway.db',ROOT/'data/mqtt-secrets.bin');profile=store.profile()
    database.initialize_database();device_api.migrate()
    if not Service.authorized(master,master):raise SystemExit('Actual Master enrollment unavailable; no changes made')
    db=device_api.connect()
    try:
        pending=db.execute("SELECT count(*) FROM commands c JOIN nodes n ON c.node_id=n.node_id WHERE n.master_id=? AND n.device_enrolled=1 AND n.enabled=1 AND c.state NOT IN ('COMPLETED','FAILED','CANCELLED','TIMEOUT')",(master,)).fetchone()[0]
    finally:db.close()
    if pending:raise SystemExit('Existing commands preserved; bounded diagnostic not started')
    service=Service(store,False);service.profile=profile
    client=client_for(profile,'SERVER_CHECK_'+uuid.uuid4().hex[:10]);received=queue.Queue(32)
    report={'scope':'Physical ESP32, live verified-TLS broker, actual Gateway DB; bounded diagnostic only',
            'server_http_reachable':False,'connack':False,'suback':False,'physical_packets_persisted':0,
            'persistence_puback':False,'shared_digest_match':False,'errors':[],
            'permanent_worker':'ACL_CONFIRMATION_REQUIRED'}
    def connected(c,u,f,reason,properties):
        report['connack']=reason==0
        if reason==0:c.subscribe([(contract.topic(profile,'status'),1),(contract.topic(profile,'config'),1)],qos=1)
    def incoming(c,u,msg):
        try:received.put_nowait((msg.topic,bytes(msg.payload),msg.retain))
        except queue.Full:report['errors'].append('DIAGNOSTIC_QUEUE_FULL')
    client.on_connect=connected;client.on_subscribe=lambda *a:report.update(suback=True);client.on_message=incoming
    try:
        with urllib.request.urlopen('http://127.0.0.1:5000/',timeout=10) as response:
            report['server_http_reachable']=response.status==200
        client.connect(profile['host'],profile['port'],profile['keepalive_s']);client.loop_start()
        deadline=time.monotonic()+50;comparison_sent=False
        while time.monotonic()<deadline:
            if report['suback'] and not comparison_sent:
                snap=contract.snapshot(profile,store.read()['shared_revision'])
                d=message(profile,master,'config',{'op':'COMPARE','snapshot':snap,'digest':contract.digest(snap)})
                client.publish(contract.topic(profile,'config'),contract.canonical(d),qos=1);comparison_sent=True
            try:
                topic,raw,retained=received.get(timeout=.2)
                d=contract.envelope(raw,topic,profile,retained=retained)
                if d['device_id']!=master:continue
                # Only process ordinary comparison and status. No switch decisions.
                if d['message_type']=='config' and d['data'].get('op')!='COMPARE':continue
                service.handle(topic,raw,retained)
                if d['message_type']=='status' and 'packet' in d['data']:
                    report['physical_packets_persisted']+=1
            except queue.Empty:pass
            except contract.ContractError as error:
                if error.code not in report['errors']:report['errors'].append(error.code)
            while not service.outgoing.empty():
                d=service.outgoing.get_nowait()
                # Handler may enqueue pre-existing commands; this diagnostic never publishes them.
                if d['message_type']!='config' or d['data'].get('op')!='PERSISTED':continue
                info=client.publish(contract.topic(profile,'config'),contract.canonical(d),qos=1)
                info.wait_for_publish(timeout=5);report['persistence_puback']|=info.is_published()
            report['shared_digest_match']=service.status()['comparison']['status']=='MATCH'
            if report['shared_digest_match'] and report['physical_packets_persisted'] and report['persistence_puback']:break
        db=device_api.connect()
        try:
            row=db.execute('SELECT last_seen,latest_status FROM nodes WHERE node_id=?',(master,)).fetchone()
            report['actual_database_status_present']=bool(row and row['last_seen'] and row['latest_status'])
        finally:db.close()
    finally:
        client.disconnect();client.loop_stop()
    report['passed']=all(report.get(key) for key in ('server_http_reachable','connack','suback','physical_packets_persisted','persistence_puback','shared_digest_match','actual_database_status_present')) and not report['errors']
    for project in (ROOT,ROOT.parent/'ESP32_LoRa_ESP32_Firmware'):
        (project/'docs/PHYSICAL_SERVER_LINK_EVIDENCE.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
