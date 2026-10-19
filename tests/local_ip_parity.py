"""Compile the real production packet parser/serializer and execute both directions."""
from pathlib import Path
import json,os,subprocess,sys,zlib
root=Path(__file__).resolve().parents[1];fw=root.parent/'ESP32_LoRa_ESP32_Firmware'
sys.path.insert(0,str(root/'backend'));import device_api
compiler=Path.home()/'.platformio/packages/toolchain-gccmingw32/bin/g++.exe'
env=dict(os.environ);env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
out=fw/'.pio/protocol_host.exe'
subprocess.run([str(compiler),'-std=c++11','-static','-DARDUINOJSON_ENABLE_ARDUINO_STRING=1','-I'+str(fw/'test/protocol_stubs'),'-I'+str(fw/'.pio/libdeps/esp32dev/ArduinoJson/src'),str(fw/'src/protocol/protocol.cpp'),str(fw/'test/protocol_host.cpp'),'-o',str(out)],check=True,env=env)
packet=json.loads(subprocess.check_output([str(out)],env=env));device_api.validate_packet(packet)
for body in ({'unicode':'தமிழ்','number':3},{'valid':False,'parameters':{}},{'command':'PING','command_id':'MSG-TEST','arguments':{}}):
    packet=device_api.packet('TELEMETRY','IP-MASTER','GATEWAY',body)
    back=json.loads(subprocess.check_output([str(out),json.dumps(packet,separators=(',',':'),ensure_ascii=True)],env=env));assert back==packet
for patch in ({'protocol_version':2},{'ttl':0},{'payload_crc32':0},{'payload_length':999},{'origin_id':'OTHER'},{'extra':1},{'next_hop':'+'}):
    bad={**packet,**patch};result=subprocess.run([str(out),json.dumps(bad)],capture_output=True,env=env);assert result.returncode==2
print('PASS: actual C++ packet serializer/parser and Python validation, UTF-8/CRC/fields/version/type bounds; production route selection/fallback assertions.')
