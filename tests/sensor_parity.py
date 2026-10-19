"""Execute both production validators, not simulated measurements."""
import sys,os,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];fw=root.parent/'ESP32_LoRa_ESP32_Firmware'
sys.path.insert(0,str(root/'backend'));import sensor_telemetry
compiler=Path.home()/'.platformio/packages/toolchain-gccmingw32/bin/g++.exe';out=fw/'.pio/sensor_host.exe';env=dict(os.environ);env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
subprocess.run([str(compiler),'-std=c++11','-static','-DARDUINOJSON_ENABLE_ARDUINO_STRING=1','-I'+str(fw/'test/protocol_stubs'),'-I'+str(fw/'.pio/libdeps/esp32dev/ArduinoJson/src'),str(fw/'test/sensor_host.cpp'),'-o',str(out)],check=True,env=env)
cases=[]
for kind,values in [('DHT11',{'temperature':24.5,'humidity':56}),('INA219',{'bus_voltage':12,'shunt_voltage':-1}),('INA219',{'bus_voltage':12,'shunt_voltage':10,'current':0.1,'power':1.2}),('MQ135',{'mq135_adc_raw':1800,'mq135_pin_mv':1400})]:
 cases.append((dict(sensor_type=kind,valid=True,parameters=values),True))
 cases.append((dict(sensor_type=kind,valid=False,parameters={}),True))
 cases.append((dict(sensor_type=kind,valid=False,parameters=values),False))
 cases.append((dict(sensor_type=kind,valid=True,parameters={**values,'unexpected':1}),False))
 for key in values:
  for bad in (True,'2',1e12):cases.append((dict(sensor_type=kind,valid=True,parameters={**values,key:bad}),False))
cases.extend([(dict(sensor_type='OTHER',valid=True,parameters={}),False),(dict(sensor_type='INA219',valid=True,parameters={'bus_voltage':3,'shunt_voltage':320}),False)])
for bad_kind in ([],{},True,123,None):cases.append((dict(sensor_type=bad_kind,valid=True,parameters={'temperature':25,'humidity':50}),False))
for body,expected in cases:
 try:sensor_telemetry.validate(body);py=True
 except ValueError:py=False
 cpp=subprocess.run([str(out),json.dumps(body)],capture_output=True,text=True).returncode==0
 assert py==cpp==expected,(body,py,cpp,expected)
print(f'PASS {len(cases)} actual C++/Python sensor validation vectors; no physical readings generated')
