"""Explicit, bounded physical sensor acceptance; never provisions secrets or starts MQTT."""
import argparse,json,sqlite3,sys,time
from pathlib import Path
from datetime import datetime,timedelta
root=Path(__file__).resolve().parents[1];fw=root.parent/'ESP32_LoRa_ESP32_Firmware'
sys.path[:0]=[str(root/'backend'),str(fw/'tools'),str(Path.home()/'.platformio/penv/Lib/site-packages')]
def main():
 p=argparse.ArgumentParser();p.add_argument('--live',required=True,action='store_true');p.add_argument('--commands',action='store_true');a=p.parse_args()
 from device_acceptance import usb
 state=usb({'op':'status'});identity=state['device_id'];sensor=state.get('sensors',[]);report=dict(scope='Physical COM8 ESP32 + DHT11 + INA219 + signed LAN + actual Gateway SQLite; MQ135 disconnected; no MQTT connectivity claim',device_id=identity,station_ip=state.get('station_ip'),sensors=sensor,commands=[])
 connection=sqlite3.connect((root/'data/gateway.db').as_uri()+'?mode=ro',uri=True);connection.row_factory=sqlite3.Row
 try:
  row=connection.execute('SELECT firmware_version,configuration_revision,latest_status,last_seen FROM nodes WHERE node_id=?',(identity,)).fetchone();report['gateway_device']=dict(row);report['gateway_device']['latest_status']=json.loads(row['latest_status'])
  report['persisted_measurements']=[dict(r) for r in connection.execute("SELECT t.parameter_id,t.value,t.timestamp,t.source FROM telemetry_values t JOIN (SELECT parameter_id,MAX(id) AS id FROM telemetry_values WHERE node_id=? AND source='local-ip' GROUP BY parameter_id) newest ON newest.id=t.id",(identity,))]
  public=json.loads(connection.execute('SELECT document FROM mqtt_configuration WHERE id=1').fetchone()[0]);report['gateway_mqtt_revision']=public['revision'];report['gateway_mqtt_client_id']=public['active']['client_id']
 finally:connection.close()
 if a.commands:
  import command_manager
  for kind in ('PING','GET_TELEMETRY'):
   cmd=command_manager.create_command(identity,kind,{},timeout_seconds=25);end=time.monotonic()+25
   while time.monotonic()<end:
    outcome=command_manager.get_command(cmd['command_id'])
    if outcome['state'] in ('COMPLETED','FAILED','TIMEOUT'):break
    time.sleep(.5)
   report['commands'].append(dict(command=kind,command_id=cmd['command_id'],state=outcome['state'],events=[e['event'] if 'event' in e else e.get('state',e.get('event_type')) for e in command_manager.get_command_events(cmd['command_id'])]))
 expected={'temperature','humidity','bus_voltage','shunt_voltage'};measurements=report['persisted_measurements'];recent=(datetime.now()-timedelta(seconds=60)).isoformat();actual={m['parameter_id'] for m in measurements if m['timestamp']>=recent}
 ina=next((s for s in sensor if s['sensor_type']=='INA219'),{})
 if ina.get('shunt_milliohms',0)>0:expected|={'current','power'}
 report['passed']=expected<=actual and report['gateway_device']['firmware_version']=='1.1.0-software' and all(x['state']=='COMPLETED' for x in report['commands']) and len(sensor)==3 and not state.get('mq135_enabled',True)
 report['mqtt_revision_preserved']=state.get('mqtt',{}).get('revision')==53;report['mqtt_active_fingerprint_preserved']=state.get('mqtt',{}).get('active_fingerprint')=='2c327b3f89115315111e80b0461e5b6c8ee21d499452ca08eed8447a05af7ee3'
 for project in (root,fw):(project/'docs/SENSOR_PHYSICAL_EVIDENCE.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
