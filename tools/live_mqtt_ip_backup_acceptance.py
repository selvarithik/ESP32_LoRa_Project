"""Owner-invoked COM8 MQTT operations over an expiring authenticated IP backup.
No NVS settings, broker profiles or sensor configuration are written.
"""
import argparse,json,time,sys,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'tools')]
from observe_master_live import usb,fingerprint
import command_manager as cm
import serial

def main():
 a=argparse.ArgumentParser();a.add_argument('--live',required=True,action='store_true');a.add_argument('--confirm-device-id',required=True);args=a.parse_args()
 identity=args.confirm_device_id
 assert identity=='ESP32-10777D842178','EXPECTED_MASTER_REQUIRED'
 before=usb('COM8');assert before['device_id']==identity and before['role']=='MASTER'
 assert before['mqtt']['runtime']['tls_state']=='VERIFIED' and before['local_ip']['enabled'] is False,'PRIMARY_OR_TLS_DIFFERS'
 with sqlite3.connect(ROOT/'data/gateway.db') as db:
  profile=json.loads(db.execute('SELECT document FROM mqtt_configuration WHERE id=1').fetchone()[0])['active']
  listener=json.loads(db.execute('SELECT document FROM local_ip_settings WHERE id=1').fetchone()[0])
 assert profile['host']=='n1161c10.ala.eu-central-1.emqxsl.com' and profile['tls'] is True and profile['port']==8883
 assert listener['enabled'] and listener['bind_address']=='192.168.1.102' and listener['port']==5001,'LISTENER_DIFFERS'
 folder=ROOT/'data/mqtt-ip-backup-20261029';folder.mkdir(parents=True,exist_ok=True);(folder/'before.json').write_text(json.dumps(before));protected=fingerprint()
 report={'device_id':identity,'method':'owner local validated queue; physical IP ACK/RESPONSE plus real EMQX TLS runtime','commands':[],'observations':[]};path=folder/'result.json'
 def save():path.write_text(json.dumps(report,indent=2))
 def control(seconds):
  p=serial.Serial(port=None,baudrate=115200,timeout=.2,write_timeout=3);p.dtr=False;p.rts=False;p.port='COM8'
  try:
   p.open();p.reset_input_buffer();p.write((json.dumps({'op':'ip_backup','confirm_device_id':identity,'host':listener['bind_address'],'port':listener['port'],'timeout_seconds':seconds})+'\n').encode());end=time.monotonic()+5
   while time.monotonic()<end:
    line=p.readline()
    if line.startswith(b'[COMMISSION] '):
     r=json.loads(line[13:]);assert r.get('ok'),r.get('error','BACKUP_REJECTED');return
   raise TimeoutError('BACKUP_CONTROL_TIMEOUT')
  finally:p.close()
 def wait_state(predicate,seconds):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   s=usb('COM8');m=s['mqtt']['runtime'];row={'uptime_ms':s['uptime_ms'],'mqtt_state':m['state'],'tls':m['tls_state'],'subscription':m.get('subscription_state'),'recycles':m.get('tls_client_recycles'),'backup_remaining_seconds':s['local_ip'].get('backup_remaining_seconds'),'ip_successes':s['local_ip']['successful_exchanges']};report['observations'].append(row);save()
   if predicate(s):return s
   time.sleep(2)
  raise TimeoutError('EXPECTED_RUNTIME_STATE_NOT_OBSERVED')
 def command(kind,payload=None):
  c=cm.create_command(identity,kind,payload or {},timeout_seconds=120,response_timeout_seconds=120,expiry_seconds=180,max_retries=1,ack_timeout_seconds=8);end=time.monotonic()+130
  while time.monotonic()<end:
   c=cm.get_command(c['command_id'])
   if c['state'] in cm.TERMINAL_STATES:break
   time.sleep(.25)
  kept={k:c.get(k) for k in ['command_id','command_type','state','ack_status','created_at','ack_at','response_at','result','error']};report['commands'].append(kept);save();print(json.dumps({k:kept[k] for k in ['command_id','command_type','state','ack_status','error']}),flush=True)
  assert c['state']=='COMPLETED' and c.get('ack_status')=='ACCEPTED',kind+'_DID_NOT_COMPLETE'
  time.sleep(1.5);return c
 try:
  control(180);report['backup_requested']=True;save()
  wait_state(lambda s:s['local_ip']['state']=='CONNECTED' and s['local_ip']['successful_exchanges']>=2,25)
  first=command('PING',{'message':'Verified temporary IP return path'});assert first['result']['gateway_verified_transport']=='IP'
  c=command('MQTT_RECONNECT');assert c['result']['gateway_verified_transport']=='IP';assert c['result']['tls_client_recycles']>before['mqtt']['runtime']['tls_client_recycles'];assert c['result']['tls_state']=='VERIFIED' and c['result']['subscription_state']=='READY'
  c=command('MQTT_DISCONNECT',{'restore_after_seconds':15});assert c['result']['gateway_verified_transport']=='IP' and c['result']['automatic_restore_armed'] is True
  wait_state(lambda s:s['mqtt']['runtime']['state']=='paused',8);report['pause_physically_observed']=True
  wait_state(lambda s:s['mqtt']['runtime']['state']=='connected' and s['mqtt']['runtime']['tls_state']=='VERIFIED' and s['mqtt']['runtime']['subscription_state']=='READY',45);report['automatic_restore_verified']=True
 finally:
  if report.get('backup_requested'):
   control(0);report['backup_cancel_requested']=True;save()
 final=wait_state(lambda s:s['local_ip']['enabled'] is False and s['mqtt']['runtime']['state']=='connected' and s['mqtt']['runtime']['tls_state']=='VERIFIED',30)
 # The Gateway's IP preference expires 15 seconds after the last real receipt.
 for _ in range(9):time.sleep(2)
 ping=command('PING',{'message':'EMQX restored after bounded IP backup'});assert ping['result']['gateway_verified_transport']=='MQTT'
 command('GET_CONFIG')
 after=usb('COM8');(folder/'after.json').write_text(json.dumps(after));report['mqtt_profile_preserved']=all(before['mqtt'].get(k)==after['mqtt'].get(k) for k in ['active_fingerprint','active_client_id','revision','shared_revision','secret_revision']);report['sensor_snapshot_preserved']=all(before.get(k)==after.get(k) for k in ['dht_enabled','dht_pin','ina219_enabled','mq135_enabled']);report['gateway_config_and_secrets_preserved']=protected==fingerprint();report['saved_ip_fields_preserved']=all(before['local_ip'].get(k)==after['local_ip'].get(k) for k in ['saved_enabled','gateway_host','gateway_port','routing_policy']);report['completed']=True;save();print(json.dumps({k:v for k,v in report.items() if isinstance(v,bool)}),flush=True)

if __name__=='__main__':main()
