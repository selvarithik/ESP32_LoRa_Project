"""Bounded real ESP32 acceptance. Requires explicit --live; never starts MQTT."""
import argparse,json,sqlite3,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--live',required=True,action='store_true');p.add_argument('--commands',action='store_true');a=p.parse_args()
 root=Path(__file__).resolve().parents[1];fw=root.parent/'ESP32_LoRa_ESP32_Firmware'
 sys.path.insert(0,str(root/'backend'));sys.path.append(str(Path.home()/'.platformio/penv/Lib/site-packages'));sys.path.append(str(fw/'tools'))
 from device_acceptance import usb
 import command_manager
 state=usb({'op':'status'});identity=state['device_id'];mqtt=state['mqtt']
 report=dict(scope='PHYSICAL ESP32 + GPIO4 DHT11 + signed HTTP over LAN + actual Gateway SQLite; no MQTT test',device_id=identity,station_ip=state['station_ip'],role=state.get('role'),local_ip=state.get('local_ip'),dht_enabled=state.get('dht_enabled'),dht_pin=state.get('dht_pin'),mqtt_revision=mqtt['revision'],mqtt_shared_revision=mqtt['shared_revision'],mqtt_client_id=mqtt['active_client_id'],mqtt_active_fingerprint=mqtt.get('active_fingerprint'),commands=[])
 with sqlite3.connect((root/'data/gateway.db').as_uri()+'?mode=ro',uri=True) as db:
  db.row_factory=sqlite3.Row
  report['measurements']=[dict(r) for r in db.execute("SELECT parameter_id,timestamp,value,source FROM telemetry_values WHERE node_id=? AND source='local-ip' ORDER BY id DESC LIMIT 2",(identity,))]
  public=json.loads(db.execute('SELECT document FROM mqtt_configuration WHERE id=1').fetchone()[0]);report['gateway_mqtt_revision']=public['revision'];report['gateway_mqtt_client_id']=public['active']['client_id']
 if a.commands:
  for kind in ('PING','GET_TELEMETRY'):
   cmd=command_manager.create_command(identity,kind,{},timeout_seconds=45);end=time.monotonic()+40
   while time.monotonic()<end:
    outcome=command_manager.get_command(cmd['command_id'])
    if outcome['state'] in ('COMPLETED','FAILED','TIMEOUT'):break
    time.sleep(.5)
   payload=outcome.get('response_payload') or outcome.get('response') or outcome.get('result') or {}
   if isinstance(payload,str):
    try:payload=json.loads(payload)
    except ValueError:payload={}
   # These two command results contain only an OK flag or sensor measurements.
   report['commands'].append(dict(command=kind,command_id=cmd['command_id'],state=outcome['state'],result={k:payload[k] for k in ('ok','valid','status','parameters','sensor_type') if k in payload}))
 report['passed']=bool(report['local_ip']['enabled'] and report['local_ip']['last_success_uptime_ms'] and len(report['measurements'])==2 and all(c['state']=='COMPLETED' for c in report['commands']))
 for project in (root,fw):(project/'docs/LOCAL_IP_PHYSICAL_EVIDENCE.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
