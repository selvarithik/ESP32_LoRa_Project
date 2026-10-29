"""Compile and execute the firmware's portable canonical serializer against Python."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import mqtt_contract as contract

gateway=Path(__file__).resolve().parents[1]
firmware=gateway.parent/'ESP32_LoRa_ESP32_Firmware'
expected='2ab672c11966684547bda89f0b2022bb461e6e34584b0834450a625a53d9d183'
raw=(firmware/'CONFIG_CONTRACT.md').read_bytes()
assert raw==(gateway/'CONFIG_CONTRACT.md').read_bytes()
assert hashlib.sha256(raw).hexdigest()==expected
compiler=Path.home()/'.platformio/packages/toolchain-gccmingw32/bin/g++.exe'
executable=firmware/'.pio/digest_host.exe'
environment=dict(os.environ);environment['PATH']=str(compiler.parent)+os.pathsep+environment['PATH']
subprocess.run([str(compiler),'-std=c++11','-static',str(firmware/'test/digest_host.cpp'),'-o',str(executable)],check=True,env=environment)
p=json.loads((gateway/'deployment/profile.example.json').read_text(encoding='utf-8'))
cases=[p,{**p,'host':p['host'].upper()},{**p,'port':65535},{**p,'topic_prefix':'test/Another'},
       {**p,'gateway_id':'Other_2'},{**p,'client_id':'independent-client','password':'local-only-secret'}]
for i,profile in enumerate(cases):
    snap=contract.snapshot(profile,i);v=snap['values']
    output=subprocess.check_output([str(executable),profile['host'],str(profile['port']),profile['topic_prefix'],profile['gateway_id'],str(i),*v['ca_fingerprints']]).decode('ascii')
    assert output==contract.canonical(snap),(i,'canonical bytes differ')
    assert hashlib.sha256(output.encode()).hexdigest()==contract.digest(snap)
print(f'PASS: identical contract {expected}; {len(cases)} executed C++/Python canonical-byte and SHA-256 parity vectors')
print('Scope: production serialization core on host; physical ESP32 execution and certificate parser parity still require device tests.')
