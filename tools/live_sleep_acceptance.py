"""Explicit owner-invoked real Master deep-sleep acceptance; preserves saved schedules."""
import sys,json,time
from pathlib import Path
sys.path.insert(0,'backend');sys.path.insert(0,'tools')
import command_manager as cm
from observe_master_live import usb

def main():
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument("--live",action="store_true",required=True)
 parser.add_argument("--confirm-device-id",required=True)
 args=parser.parse_args()
 if args.confirm_device_id!="ESP32-10777D842178":raise ValueError("EXPECTED_MASTER_REQUIRED")
 p=Path('data/final-pending-20261029');s=usb('COM8');assert s['device_id']=='ESP32-10777D842178' and s['mqtt']['runtime']['tls_state']=='VERIFIED'
 r={'mode':'DEEP','requested_duration_seconds':90,'samples':[]};out=p/'sleep.json'
 def save():out.write_text(json.dumps(r,indent=2))
 def cmd(k,payload):return cm.create_command(s['device_id'],k,payload,timeout_seconds=120,response_timeout_seconds=120,expiry_seconds=300,max_retries=1,ack_timeout_seconds=8)['command_id']
 def wait(cid,seconds=130):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   c=cm.get_command(cid)
   if c['state'] in cm.TERMINAL_STATES:return {k:c.get(k) for k in ['command_id','command_type','state','ack_status','created_at','ack_at','response_at','result','error']}
   time.sleep(.3)
  return {'state':'OBSERVER_TIMEOUT','command_id':cid}
 r['sleep_command']=wait(cmd('SLEEP_NOW',{'duration_seconds':90,'mode':'DEEP'}));print(json.dumps(r['sleep_command']),flush=True);save()
 start=time.monotonic();woke=False
 while time.monotonic()-start<200:
  try:
   v=usb('COM8');row={'seconds':round(time.monotonic()-start,1),'uptime_ms':v['uptime_ms'],'mqtt':v['mqtt']['runtime']['state'],'tls':v['mqtt']['runtime']['tls_state']};r['samples'].append(row)
   if v['uptime_ms']<s['uptime_ms'] and row['mqtt']=='connected' and row['tls']=='VERIFIED':woke=True;break
  except Exception as e:r['samples'].append({'seconds':round(time.monotonic()-start,1),'usb':type(e).__name__})
  save();print(json.dumps(r['samples'][-1]),flush=True);time.sleep(4)
 r['reboot_and_verified_reconnection_observed']=woke
 if woke:
  time.sleep(2);r['power_status']=wait(cmd('GET_POWER_STATUS',{}));time.sleep(2);r['ping']=wait(cmd('PING',{'message':'After timed deep sleep wake'}));v=usb('COM8');r['mqtt_profile_preserved']=all(s['mqtt'].get(k)==v['mqtt'].get(k) for k in ['revision','shared_revision','secret_revision','active_fingerprint','active_client_id']);r['sensor_flags_preserved']=all(s.get(k)==v.get(k) for k in ['dht_enabled','dht_pin','ina219_enabled','mq135_enabled']);(p/'after-sleep.json').write_text(json.dumps(v))
 save();print(json.dumps({'finished':True,'woke':woke,'power':r.get('power_status',{}).get('result'),'ping':r.get('ping',{}).get('state')}),flush=True)

if __name__=="__main__":main()
