"""Writes non-secret templates only; does not touch active profiles, databases or secrets."""
import sys,ssl,json,warnings
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from cryptography import x509
from cryptography.utils import CryptographyDeprecationWarning
from cryptography.hazmat.primitives.serialization import Encoding
from cloud_profile_preparation import prepare

def main():
 roots=[]
 for der,kind,trust in ssl.enum_certificates('ROOT'):
  if kind!='x509_asn':continue
  try:
   with warnings.catch_warnings():
    warnings.simplefilter('error',CryptographyDeprecationWarning)
    c=x509.load_der_x509_certificate(der)
  except (ValueError,CryptographyDeprecationWarning):continue
  if any(a.value=='ISRG Root X1' for a in c.subject):roots.append(c.public_bytes(Encoding.PEM).decode())
 if not roots:raise RuntimeError('ISRG Root X1 not in local ROOT store; supply a reviewed HiveMQ CA before preparing profiles')
 profiles,manifest=prepare({'EMQX':(ROOT/'deployment/broker-ca.pem').read_text(encoding='utf-8'),'HIVEMQ':roots[0]})
 for project in (ROOT,ROOT.parent/'ESP32_LoRa_ESP32_Firmware'):
  if not project.is_dir():raise RuntimeError('Existing project unavailable')
  output=project/'deployment/prepared';output.mkdir(parents=True,exist_ok=True)
  for key,profile in profiles.items():(output/(key+'.json')).write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
  (output/'preparation.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('Prepared four canonical profiles in both repositories. No credentials, active revisions, database or connections changed. Broker chains remain unverified.')
if __name__=='__main__':main()
