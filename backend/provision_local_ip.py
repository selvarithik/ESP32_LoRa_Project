"""Owner-run local-IP commissioning: DPAPI storage and USB only, never network secrets."""
import argparse,hashlib,json,secrets,sys
from pathlib import Path
import database,local_ip
from mqtt_store import SecretFile

def main():
 p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--gateway-ip',required=True);p.add_argument('--gateway-port',type=int,default=5001);p.add_argument('--dht-gpio',type=int,default=4);p.add_argument('--apply',action='store_true');a=p.parse_args()
 with local_ip.connection() as db:
  row=db.execute('SELECT device_role,device_enrolled,enabled FROM nodes WHERE node_id=?',(a.id,)).fetchone()
 if not row or not row['device_enrolled'] or not row['enabled']:raise ValueError('ENROLLED_DEVICE_REQUIRED')
 if not a.apply:print('Preview only: preserve existing MQTT/legacy credentials; provision dedicated local-IP credential by USB.');return
 local_ip.service.migrate()
 folder=database.DATA_DIR;path=folder/('local-ip-token-'+hashlib.sha256(a.id.encode()).hexdigest()+'.bin')
 with local_ip.connection() as db:old=db.execute('SELECT key_hash FROM local_ip_credentials WHERE device_id=?',(a.id,)).fetchone()
 if path.exists():
  value=json.loads(SecretFile.protect(path.read_bytes(),True));token=value['local_ip_token']
  key=hashlib.sha256(token.encode()).digest()
  if value['device_id']!=a.id or (old and old['key_hash'] not in (key.hex(),hashlib.sha256(key).hexdigest())):raise ValueError('STORED_IDENTITY_DIFFERS')
 else:
  if old:raise ValueError('PROTECTED_CREDENTIAL_FILE_REQUIRED')
  token=secrets.token_hex(32);temporary=path.with_suffix('.tmp');temporary.write_bytes(SecretFile.protect(json.dumps({'device_id':a.id,'local_ip_token':token}).encode()));temporary.replace(path)
 sys.path.append(str(Path.home()/'.platformio/penv/Lib/site-packages'))
 sys.path.append(str(Path(__file__).resolve().parents[2]/'ESP32_LoRa_ESP32_Firmware/tools'))
 from device_acceptance import usb
 state=usb({'op':'status'})
 if state.get('device_id')!=a.id:raise ValueError('USB_IDENTITY_DIFFERS')
 result=usb({'op':'config','config':{'local_ip_token':token,'local_ip_enabled':True,'server_host':a.gateway_ip,'server_port':a.gateway_port,'server_https':False,'dht_enabled':True,'dht_pin':a.dht_gpio}})
 if not result.get('ok'):raise ValueError('USB_CONFIG_REJECTED')
 local_ip.save_credential(a.id,token)
 print('Dedicated local-IP credential USB-provisioned. MQTT and legacy credentials preserved. Restart the board and Gateway listener.')

if __name__=='__main__':
 try:main()
 except Exception:raise SystemExit('Local-IP provisioning failed or incomplete; inspect identity and saved state. No secret details displayed.')
