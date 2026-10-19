import unittest,time
from contextlib import closing
from gateway_fixture import seed
import device_api,database,sensor_telemetry
class SensorTests(unittest.TestCase):
 def setUp(self):self.client=seed();device_api.enroll('SENSOR-MASTER','Sensor Master','MASTER')
 def send(self,kind,values,valid=True):return device_api.ingest('SENSOR-MASTER',device_api.packet('TELEMETRY','SENSOR-MASTER','GATEWAY',dict(sensor_type=kind,valid=valid,parameters=values)),transport='SIMULATED_LOCAL_IP')
 def test_all_sensor_types_persist_and_snapshot(self):
  for kind,values in [('DHT11',dict(temperature=25,humidity=50)),('INA219',dict(bus_voltage=12,shunt_voltage=10,current=0.1,power=1.2)),('MQ135',dict(mq135_adc_raw=1200,mq135_pin_mv=900))]:self.assertTrue(self.send(kind,values)['accepted'])
  with closing(database.get_connection()) as db:
   self.assertEqual(db.execute("SELECT count(*) FROM telemetry_values WHERE node_id='SENSOR-MASTER'").fetchone()[0],8)
   self.assertEqual(db.execute("SELECT decimal_places FROM sensor_parameters WHERE node_id='SENSOR-MASTER' AND parameter_id='current'").fetchone()[0],5)
  snapshot=self.client.get('/api/live/snapshot');self.assertEqual(snapshot.status_code,200);self.assertIn('bus_voltage',snapshot.get_data(as_text=True));self.assertIn('mq135_adc_raw',snapshot.get_data(as_text=True))
 def test_unknown_shunt_excludes_current_power(self):
  self.send('INA219',dict(bus_voltage=3.3,shunt_voltage=0))
  with closing(database.get_connection()) as db:self.assertEqual(db.execute("SELECT count(*) FROM telemetry_values WHERE node_id='SENSOR-MASTER'").fetchone()[0],2)
 def test_bad_samples_rejected_independently(self):
  for kind,values in [('DHT11',dict(temperature=True,humidity=50)),('INA219',dict(bus_voltage=40,shunt_voltage=0)),('MQ135',dict(mq135_adc_raw=4096,mq135_pin_mv=3301))]:
   with self.assertRaises(ValueError):self.send(kind,values)
  self.send('INA219',{},False);self.send('DHT11',dict(temperature=25,humidity=50))
  with closing(database.get_connection()) as db:self.assertEqual(db.execute("SELECT count(*) FROM telemetry_values WHERE node_id='SENSOR-MASTER'").fetchone()[0],2)
