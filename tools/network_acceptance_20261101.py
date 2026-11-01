"""Bounded physical Master LAN test; no configuration writes or command dispatch."""
import argparse,hashlib,json,socket,sys,time,urllib.request
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'tools')]
from observe_master_live import usb,connection
sys.path.append(str(ROOT.parent/'ESP32_LoRa_ESP32_Firmware/tools'))
from radio_inspect import exchange
import serial,local_ip,device_api

def stored_hash():
 with connection() as db:
  return {table:hashlib.sha256(db.execute('SELECT document FROM '+table+' WHERE id=1').fetchone()[0].encode()).hexdigest() for table in ['local_ip_settings','mqtt_configuration']}

def control(port,identity,host,number,seconds):
 p=serial.Serial(port=None,baudrate=115200,timeout=.2,write_timeout=2);p.dtr=False;p.rts=False;p.port=port
 try:
  p.open();s=exchange(p,{'op':'status'});assert s['device_id']==identity and s['role']=='MASTER'
  result=exchange(p,{'op':'ip_backup','confirm_device_id':identity,'host':host,'port':number,'timeout_seconds':seconds})
  if not result.get('ok'):raise RuntimeError('BOUNDED_IP_BACKUP_REJECTED')
 finally:p.close()

def main():
 a=argparse.ArgumentParser();a.add_argument('--host',required=True);a.add_argument('--port',type=int,default=5501);a.add_argument('--live',action='store_true',required=True);a.add_argument('--hold-seconds',type=int,choices=range(0,61),default=0);args=a.parse_args()
 identity='ESP32-10777D842178';before=usb('COM8');assert before['device_id']==identity and before['role']=='MASTER'
 protected=stored_hash();service=local_ip.Service();report={'test':'Physical Master temporary authenticated LAN listener; commands suppressed','host':args.host,'port':args.port,'before_station_ip':before['station_ip'],'probes':{}}
 folder=ROOT/'data/network-acceptance-20261101';folder.mkdir(parents=True,exist_ok=True)
 for name,url in [('gateway_http','http://127.0.0.1:5000/login'),('master_http','http://'+before['station_ip']+'/login')]:
  try:
   with urllib.request.urlopen(url,timeout=4) as response:report['probes'][name]={'status':response.status,'content_type':response.headers.get('Content-Type')}
  except Exception as error:report['probes'][name]={'error':type(error).__name__}
 requested=False
 try:
  with patch.object(device_api,'pending_commands',return_value=[]):
   service.start({'enabled':True,'bind_address':args.host,'port':args.port})
   control('COM8',identity,args.host,args.port,90 if args.hold_seconds else 50);requested=True
   started=time.monotonic();observations=[]
   while time.monotonic()-started<max(35,args.hold_seconds):
    state=usb('COM8');status=state['local_ip'];observations.append({'uptime_ms':state.get('uptime_ms'),'network_stack_free_min_bytes':state.get('network_stack_free_min_bytes'),**{k:status.get(k) for k in ['state','successful_exchanges','failed_exchanges','last_failure_stage','last_failure_code']}})
    if service.accepted>=2 and time.monotonic()-started>=args.hold_seconds:break
    time.sleep(3)
   report['observed_seconds']=round(time.monotonic()-started,2);report['observations']=observations;report['reset_observed']=any(o['uptime_ms']<before['uptime_ms'] for o in observations)
   report['physical_listener']={'accepted':service.accepted,'rejected':service.rejected,'last_packet_error':service.last_packet_error,'last_database_persisted_at':service.last_persisted_at,'result':'PERSISTENCE_RECEIPTS_VERIFIED' if service.accepted>=2 else 'NOT_VERIFIED'}
   service.stop()
 except Exception as error:report['error']=type(error).__name__+': '+str(error)
 finally:
  if requested:
   try:control('COM8',identity,args.host,args.port,0);report['temporary_backup_cancelled']=True
   except Exception as error:report['cancel_error']=type(error).__name__
  service.stop()
 report['saved_gateway_and_mqtt_documents_unchanged']=protected==stored_hash()
 try:
  after=usb('COM8');report['firmware_mqtt_profile_unchanged']=all(before['mqtt'].get(k)==after['mqtt'].get(k) for k in ['active_fingerprint','revision','active_client_id']);report['sensor_enable_flags_unchanged']=all(before.get(k)==after.get(k) for k in ['dht_enabled','dht_pin','ina219_enabled','mq135_enabled']);report['saved_local_ip_fields_unchanged']=all(before['local_ip'].get(k)==after['local_ip'].get(k) for k in ['saved_enabled','gateway_host','gateway_port','routing_policy'])
 except Exception as error:report['final_usb_status_error']=type(error).__name__

 (folder/('stability-result.json' if args.hold_seconds else 'result.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':main()
