"""Execute the actual C++ runtime core and Python schema, no device/network access."""
from pathlib import Path
import itertools,subprocess,sys
root=Path(__file__).resolve().parents[1];fw=root.parent/'ESP32_LoRa_ESP32_Firmware';sys.path.insert(0,str(root/'backend'))
import power_schedule,device_control_contract,radio_model
python=Path.home()/'.platformio/penv/Scripts/python.exe';subprocess.run([str(python),str(fw/'test/check_features.py')],check=True)
exe=fw/'.pio/features_host.exe';count=0
for address,mask,gateway in [('192.168.1.20','255.255.255.0','192.168.1.1'),('192.168.1.0','255.255.255.0','192.168.1.1'),('192.168.1.2','255.0.255.0','192.168.1.1'),('192.168.1.2','255.255.255.0','192.168.2.1'),('127.0.0.2','255.0.0.0','127.0.0.1')]:
 args=(address,mask,gateway,'1.1.1.1','8.8.8.8');cpp=subprocess.check_output([str(exe),'network',*args],text=True);assert int(cpp)==device_control_contract.static_network(*args);count+=1
for utc,start,duration,days,offset in itertools.product([1,1792411200,1792444800],[0,1380],[60,7200],[1,127],[-720,330]):
 config=dict(sleep_enabled=True,sleep_start_minute=start,sleep_duration_seconds=duration,sleep_days_mask=days,utc_offset_minutes=offset)
 cpp=subprocess.check_output([str(exe),'sleep',str(utc),'1',str(start),str(duration),str(days),str(offset)],text=True)
 assert int(cpp)==power_schedule.remaining(config,utc),(config,utc,cpp);count+=1
for payload in (b'PING',b'',bytes(range(128))):
 frame=radio_model.encode('SIM-MASTER','SIM-NODE-1',4,5,123,payload);cpp=subprocess.check_output([str(exe),'radio',frame.hex()],text=True);assert cpp==frame.hex();count+=1
print('PASS',count,'executed C++/Python network/schedule vectors, plus real C++ hardware mock/radio/drain-state assertions; no physical hardware.')
