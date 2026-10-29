"""Owner-invoked local acceptance through the existing validated Gateway queue.

Does not start MQTT, forge a web session, edit configuration or synthesize results.
Actual ACKs/RESPONSES are received by the permanent worker and read from SQLite.
"""
import argparse,json,time,sys,sqlite3,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
import command_manager as cm
import device_control_contract as contract
sys.path.insert(0,str(ROOT/'tools'))
from observe_master_live import usb

def main():
 p=argparse.ArgumentParser();p.add_argument('--live',action='store_true',required=True);p.add_argument('--phase',choices=['recovery','operations'],required=True);p.add_argument('--confirm-device-id',required=True);a=p.parse_args();identity=a.confirm_device_id
 assert identity=='ESP32-10777D842178','EXPECTED_MASTER_REQUIRED'
 state=usb('COM8');assert state['device_id']==identity and state['role']=='MASTER','PHYSICAL_IDENTITY_DIFFERS'
 with sqlite3.connect((ROOT/'data/gateway.db').as_uri()+'?mode=ro',uri=True) as db:
  stored=json.loads(db.execute('SELECT document FROM mqtt_configuration WHERE id=1').fetchone()[0]);assert stored['active']['provider']=='EMQX' and stored['active']['host']=='n1161c10.ala.eu-central-1.emqxsl.com' and stored['active']['port']==8883 and stored['active']['tls'] is True,'EMQX_PROFILE_REQUIRED'
 assert state['mqtt']['runtime']['tls_state']=='VERIFIED' and state['mqtt']['runtime']['subscription_state']=='READY','VERIFIED_MASTER_CONNECTION_REQUIRED'
 folder=ROOT/'data/recovery-fix-20261029';folder.mkdir(parents=True,exist_ok=True);report={'phase':a.phase,'device_id':identity,'transport':'permanent EMQX worker','command_creation':'owner-authorized local validated queue; not a Dashboard/API click test','results':[]};path=folder/(a.phase+'.json')
 def save():path.write_text(json.dumps(report,indent=2))
 def submit(kind,payload=None):
  contract.validate_command(kind,payload or {});c=cm.create_command(identity,kind,payload or {},timeout_seconds=120,response_timeout_seconds=120,expiry_seconds=300,max_retries=1,ack_timeout_seconds=8);print(json.dumps({'queued':kind,'command_id':c['command_id']}),flush=True);return c['command_id']
 def wait(cid,ack=False,timeout=140):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   c=cm.get_command(cid)
   if (ack and c.get('ack_at')) or c['state'] in cm.TERMINAL_STATES:return c
   time.sleep(.2)
  return cm.get_command(cid)
 def record(c):
  kept={k:c.get(k) for k in ['command_id','command_type','state','ack_status','created_at','sent_at','ack_at','response_at','result','error']};report['results'].append(kept);save();print(json.dumps({k:kept[k] for k in ['command_type','state','ack_status','error']}),flush=True)
 def run(kind,payload=None):c=wait(submit(kind,payload));record(c);time.sleep(1.5);return c
 if a.phase=='recovery':
  run('WIFI_RECONNECT');run('PING',{'message':'After automatic Wi-Fi/MQTT recovery'})
  run('RESTART');run('PING',{'message':'After restart and final-response recovery'})
  run('GET_CAPABILITIES');run('GET_CONFIG')
 else:
  ref=run('PING',{'message':'Operational result-cache reference'})
  for kind,payload in [('SYNC_TIME',{'unix_time':int(time.time())}),('MQTT_CONNECT',{}),('MQTT_RECONNECT',{}),('MQTT_DISCONNECT',{'restore_after_seconds':10}),('MQTT_TEST',{}),('RADIO_INSPECT',{}),('DISCOVER_NODES',{'timeout_seconds':5}),('I2C_SCAN',{'confirm':True}),('GET_COMMAND_RESULT',{'command_id':ref['command_id']}),('RESET_DIAGNOSTIC_COUNTERS',{'scope':'NETWORK','confirm':True})]:run(kind,payload)
  sleeping=submit('SLEEP_NOW',{'duration_seconds':60,'mode':'LIGHT'});accepted=wait(sleeping,ack=True,timeout=15)
  # Exercise cancellation during the explicit five-second preparation grace.
  cancelled=submit('CANCEL_PENDING_SLEEP');record(wait(sleeping));record(wait(cancelled))
  run('GET_POWER_STATUS');run('GET_CONFIG');run('PING',{'message':'Operational acceptance final PING'})
 final=usb('COM8');report['final_tls']=final['mqtt']['runtime'];report['mqtt_snapshot_preserved']=all(state['mqtt'].get(k)==final['mqtt'].get(k) for k in ['active_fingerprint','active_client_id','revision','shared_revision','secret_revision']);report['sensor_snapshot_preserved']=all(state.get(k)==final.get(k) for k in ['dht_enabled','dht_pin','ina219_enabled','mq135_enabled']);save();print(json.dumps({'phase_complete':a.phase,'mqtt_preserved':report['mqtt_snapshot_preserved'],'sensor_snapshot_preserved':report['sensor_snapshot_preserved']}),flush=True)
if __name__=='__main__':main()
