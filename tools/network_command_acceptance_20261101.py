"""Owner-authorized read-only MQTT command acceptance through existing permanent worker."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'tools')]
import command_manager as cm
from observe_master_live import connection,usb
identity='ESP32-10777D842178';before=usb('COM8');assert before['device_id']==identity and before['role']=='MASTER'
report={'scope':'Real Master, permanent EMQX Gateway worker, read-only commands','commands':[]}
for kind,args in [('PING',{'message':'Read-only network acceptance'}),('GET_NETWORK',{}),('GET_STATUS',{})]:
 command=cm.create_command(identity,kind,args,timeout_seconds=45,response_timeout_seconds=45,expiry_seconds=60,max_retries=1,ack_timeout_seconds=5);deadline=time.monotonic()+55
 while time.monotonic()<deadline:
  row=cm.get_command(command['command_id'])
  if row['state'] in cm.TERMINAL_STATES:break
  time.sleep(.4)
 result=row.get('result') or {};public={k:result.get(k) for k in ['ok','message','connected','station_ip','ip','rssi','dhcp','subnet','gateway','dns','internet_status','gateway_reachable','reset_reason','uptime_s','gateway_verified_transport'] if k in result}
 entry={k:row.get(k) for k in ['command_id','command_type','state','ack_status','ack_at','response_at','error']};entry['reported']=public;report['commands'].append(entry);print(json.dumps(entry),flush=True)
 if row['state']!='COMPLETED':break
folder=ROOT/'data/network-acceptance-20261101';folder.mkdir(parents=True,exist_ok=True);(folder/'read-only-commands.json').write_text(json.dumps(report,indent=2))
