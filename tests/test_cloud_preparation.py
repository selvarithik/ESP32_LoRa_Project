"""Offline candidate templates; never instantiate service/store or connect to broker."""
import sys,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
import cloud_profile_preparation as prep,mqtt_contract as contract
class CloudPreparationTests(unittest.TestCase):
 def templates(self):return {p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'deployment/prepared').glob('*.json') if p.name!='preparation.json'}
 def test_exact_profiles_and_distinct_identities(self):
  profiles=self.templates();self.assertEqual(len(profiles),4)
  for provider in prep.BROKERS:
   clients=[]
   for side,(username,client) in prep.IDENTITIES.items():
    p=profiles[provider.lower()+'-'+side.lower()];contract.validate_profile(p);self.assertEqual(set(p),set(contract.FIELDS));self.assertEqual(p['username'],username);self.assertEqual(p['client_id'],client);self.assertEqual(p['host'],prep.BROKERS[provider]['host']);self.assertEqual(p['password'],'');self.assertTrue(p['tls']);self.assertEqual(p['qos_default'],1);clients.append(client)
   self.assertEqual(len(set(clients)),2)
 def test_templates_identical_both_repos_and_no_private_key(self):
  firmware=ROOT.parent/'ESP32_LoRa_ESP32_Firmware'
  for p in (ROOT/'deployment/prepared').glob('*'):
   self.assertEqual(p.read_bytes(),(firmware/'deployment/prepared'/p.name).read_bytes());self.assertNotIn(b'PRIVATE KEY',p.read_bytes())
 def test_no_connection_side_effect_or_activation(self):
  profiles=self.templates();cas={provider:profiles[provider.lower()+'-master']['ca_cert'] for provider in prep.BROKERS}
  with patch('socket.create_connection',side_effect=AssertionError('Network prohibited')),patch('socket.socket',side_effect=AssertionError('Network prohibited')):
   output,manifest=prep.prepare(cas)
  self.assertEqual(len(output),4);self.assertEqual(manifest['activation'],'NOT_ACTIVATED');self.assertTrue(all(not x['broker_chain_verified'] for x in manifest['certificates'].values()))
 def test_ca_role_and_fail_closed_validation(self):
  profiles=self.templates();p=next(iter(profiles.values()));self.assertTrue(prep.certificate_info(p['ca_cert'])[0]['is_ca'])
  for update in ({'tls':False},{'ca_cert':'not a CA'},{'mqtt_version':'5.0'},{'qos_default':0}):
   with self.assertRaises(contract.ContractError):contract.validate_profile(dict(p,**update))
 def test_topic_registry_not_changed(self):
  for p in self.templates().values():
   for kind in contract.TYPES:self.assertEqual(contract.topic(p,kind),'/'.join(('selvarithik/gateway','GW001',kind)))
if __name__=='__main__':unittest.main()
