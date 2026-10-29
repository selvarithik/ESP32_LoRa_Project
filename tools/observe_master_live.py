"""Bounded read-only COM8/SQLite observer. Does not create commands or configure devices."""
import argparse,json,sqlite3,time,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.append('C:/Users/Admin/.platformio/penv/Lib/site-packages')
import serial
ROOT=Path(__file__).resolve().parents[1]
def usb(port):
 p=serial.Serial(port=None,baudrate=115200,timeout=.2,write_timeout=2);p.dtr=False;p.rts=False;p.port=port
 try:
  p.open();p.reset_input_buffer();p.write(b'{"op":"status"}\n');end=time.monotonic()+5
  while time.monotonic()<end:
   line=p.readline()
   if line.startswith(b'[COMMISSION] '):return json.loads(line[13:])
  raise TimeoutError('USB_STATUS_TIMEOUT')
 finally:p.close()
def connection():
 c=sqlite3.connect((ROOT/'data/gateway.db').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;return c
def fingerprint():
 with connection() as c:doc=c.execute('SELECT document FROM mqtt_configuration WHERE id=1').fetchone()[0]
 return {'mqtt_document':hashlib.sha256(doc.encode()).hexdigest(),**{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.bin')}}
def main():
 a=argparse.ArgumentParser();a.add_argument('--seconds',type=int,default=300);a.add_argument('--port',default='COM8');a.add_argument('--id',required=True);args=a.parse_args();assert 30<=args.seconds<=1800
 folder=ROOT/'data'/'live-master-20261029';folder.mkdir(parents=True,exist_ok=True)
 start=time.monotonic();stamp=datetime.now();before=fingerprint()
 with connection() as c:tid=c.execute('SELECT COALESCE(MAX(id),0) FROM telemetry_values').fetchone()[0];cid=c.execute('SELECT COALESCE(MAX(id),0) FROM commands').fetchone()[0]
 report={'scope':'Physical Master via permanent EMQX Gateway worker; read-only USB/DB observer','started_at':stamp.isoformat(),'device_id':args.id,'baseline_telemetry_id':tid,'baseline_command_id':cid,'samples':[],'usb_errors':[]};states=[]
 while time.monotonic()-start<args.seconds:
  try:
   state=usb(args.port);assert state['device_id']==args.id and state['role']=='MASTER','IDENTITY_MISMATCH';states.append(state);m=state['mqtt']['runtime']
   report['samples'].append({'elapsed_s':round(time.monotonic()-start,1),'uptime_ms':state.get('uptime_ms'),'free_8bit_heap':state.get('free_8bit_heap'),'largest_8bit_block':state.get('largest_8bit_block'),'mqtt':{k:m.get(k) for k in ['state','tls_state','certificate_verify_flags','authentication_state','subscription_state','reconnect_count','tls_client_recycles','dropped','pubacks']},'sensors':state.get('sensors')})
   print(json.dumps({'elapsed_s':report['samples'][-1]['elapsed_s'],'mqtt':m.get('state'),'tls':m.get('tls_state')}),flush=True)
  except Exception as e:report['usb_errors'].append(type(e).__name__)
  report['observed_seconds']=round(time.monotonic()-start,1);(folder/'progress.json').write_text(json.dumps(report,indent=2))
  time.sleep(min(20,max(0,args.seconds-(time.monotonic()-start))))
 with connection() as c:
  rows=[dict(r) for r in c.execute('SELECT id,parameter_id,timestamp,value,source FROM telemetry_values WHERE id>? AND node_id=? AND source=? ORDER BY id',(tid,args.id,'mqtt'))]
  report['commands']=[dict(r) for r in c.execute('SELECT command_id,command_type,state,created_at,sent_at,ack_at,ack_status,response_at,error,result FROM commands WHERE id>? AND node_id=? ORDER BY id',(cid,args.id))]
  prior={r['parameter_id']:r['timestamp'] for r in c.execute('SELECT parameter_id,MAX(timestamp) timestamp FROM telemetry_values WHERE node_id=? AND source=? GROUP BY parameter_id',(args.id,'mqtt'))}
 end=datetime.now();report['observed_seconds']=round(time.monotonic()-start,1);report['finished_at']=end.isoformat();report['new_mqtt_values']=len(rows);report['telemetry']={}
 for key in ['temperature','humidity','bus_voltage','shunt_voltage','current','power','mq135_adc_raw','mq135_pin_mv']:
  values=[r for r in rows if r['parameter_id']==key];times=[datetime.fromisoformat(r['timestamp']) for r in values];gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:])]
  report['telemetry'][key]={'new_values':len(values),'maximum_gap_s':max(gaps) if gaps else None,'last_value':values[-1]['value'] if values else None,'last_received_at':prior.get(key),'age_at_finish_s':round((end-datetime.fromisoformat(prior[key])).total_seconds(),1) if prior.get(key) else None}
 report['gateway_settings_and_protected_files_preserved']=fingerprint()==before
 if states:
  first,last=states[0],states[-1];report['master_mqtt_and_sensor_snapshot_preserved']=all(first.get(k)==last.get(k) for k in ['device_id','role','dht_enabled','dht_pin','ina219_enabled','mq135_enabled']) and all(first['mqtt'].get(k)==last['mqtt'].get(k) for k in ['revision','shared_revision','secret_revision','active_fingerprint','active_client_id']);report['observed_reboot']=any(b.get('uptime_ms',0)<a.get('uptime_ms',0) for a,b in zip(states,states[1:]));(folder/'usb-final.json').write_text(json.dumps(states[-1]))
 (folder/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps({'completed':True,'seconds':report['observed_seconds'],'new_mqtt_values':len(rows),'commands':len(report['commands'])}),flush=True)
if __name__=='__main__':main()
