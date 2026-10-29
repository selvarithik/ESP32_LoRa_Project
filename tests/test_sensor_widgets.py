"""Feature coverage uses the fixture database, never production telemetry."""
import unittest
import json
from datetime import datetime, timedelta
from gateway_fixture import seed, server
import database
import account_settings

class SensorWidgetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=seed()
 def test_catalog_and_authorization(self):
  self.assertEqual(len(self.c.get("/api/sensor-catalog").json["templates"]),30)
  anon=server.app.test_client()
  self.assertEqual(anon.put("/api/nodes/TEST_001/parameters/temperature",json={"display_enabled":False}).status_code,401)
  no_token=server.app.test_client()
  with self.c.session_transaction() as s: actor=dict(s)
  with no_token.session_transaction() as s:s.update(actor)
  self.assertEqual(no_token.put("/api/nodes/TEST_001/parameters/temperature",json={"display_enabled":False}).status_code,403)
 def test_mapping_visibility_and_retention(self):
  path="/api/nodes/TEST_001/parameters"
  config={"source":"node_telemetry","source_field":"raw_pressure","scale":2,"offset":-1,"color":"#0D9488","icon":"gauge","widget_type":"numeric","category":"core","stale_timeout":20,"reporting_interval":3,"position":1}
  p={"parameter_id":"scaled","parameter_name":"Scaled pressure","parameter_type":"Pressure","data_type":"FLOAT","unit":"hPa","display_enabled":True,"widget_config":config}
  self.assertEqual(self.c.post(path,json=p).status_code,200)
  self.assertEqual(self.c.post(path,json=p).status_code,400)
  self.assertEqual(self.c.post("/api/telemetry",json={"node_id":"TEST_001","parameters":{"raw_pressure":5}}).status_code,200)
  latest=self.c.get(path+"/latest").json["parameters"]
  item=next(x for x in latest if x["parameter_id"]=="scaled")
  self.assertEqual(item["value"],9)
  self.assertEqual(item["widget_config"]["source_field"],"raw_pressure")
  self.assertEqual(self.c.put(path+"/scaled",json={"display_enabled":False}).status_code,200)
  self.assertFalse(next(x for x in self.c.get(path).json["parameters"] if x["parameter_id"]=="scaled")["display_enabled"])
  self.assertEqual(self.c.delete(path+"/scaled").status_code,409)
  self.assertEqual(self.c.post(path+"/scaled/enable",json={"enabled":False}).status_code,200)
  self.c.post("/api/telemetry",json={"node_id":"TEST_001","parameters":{"raw_pressure":7}})
  self.assertEqual(len(self.c.get("/api/nodes/TEST_001/telemetry/scaled").json["data"]),1)
  self.assertEqual(self.c.put(path+"/scaled",json={"widget_config":{"source":"mqtt"}}).status_code,400)
  self.assertEqual(self.c.put(path+"/scaled",json={"widget_config":{"color":"bad"}}).status_code,400)
  self.assertEqual(self.c.put(path+"/scaled",json={"min_value":10,"max_value":2}).status_code,400)
 def test_future_icons_validate_and_persist(self):
  icons=("fan","flame","cloud-rain","magnet","door","weight","ruler","volume","compass","beaker")
  path="/api/nodes/TEST_002/parameters"
  for icon in icons:
   with self.subTest(icon=icon):
    pid="future_icon_"+icon
    response=self.c.post(path,json={"parameter_id":pid,"parameter_name":"Future "+icon,"parameter_type":"Custom","data_type":"FLOAT","enabled":False,"display_enabled":False,"widget_config":{"icon":icon,"source":"node_telemetry","source_field":pid}})
    self.assertEqual(response.status_code,200,response.json)
    saved=next(p for p in self.c.get(path).json["parameters"] if p["parameter_id"]==pid)
    self.assertEqual(json.loads(saved["widget_config"])["icon"],icon)
    self.assertFalse(saved["enabled"])
    from sensor_widgets import ICON_COLORS,config
    self.assertEqual(config(saved)["color"],ICON_COLORS[icon])
    self.assertEqual(self.c.put(path+"/"+pid,json={"widget_config":{"color":"#112233"}}).status_code,200)
    saved=next(p for p in self.c.get(path).json["parameters"] if p["parameter_id"]==pid)
    self.assertEqual(config(saved)["color"],"#112233")
  self.assertEqual(self.c.post(path,json={"parameter_id":"bad_icon","parameter_name":"Bad","parameter_type":"Custom","data_type":"FLOAT","widget_config":{"icon":"not-an-icon"}}).status_code,400)
 def test_time_windows_and_negative_values(self):
  from telemetry_manager import save_value
  for hours,value in ((.2,-82),(2,-90),(25,-105),(200,-120)):
   save_value("TEST_001","rssi",value,timestamp=(datetime.now()-timedelta(hours=hours)).isoformat())
  for hours,expected in ((1,-82),(6,-90),(24,-90),(168,-105)):
   response=self.c.get("/api/nodes/TEST_001/telemetry/rssi?hours="+str(hours))
   self.assertEqual(response.status_code,200)
   data=response.json
   self.assertEqual(data["statistics"]["minimum"],min(expected,-89))
   self.assertTrue(all(datetime.fromisoformat(x["timestamp"])>=datetime.now()-timedelta(hours=hours,seconds=2) for x in data["data"]))
  self.assertEqual(self.c.get("/api/nodes/TEST_001/telemetry/rssi?hours=3").status_code,400)
  self.assertEqual(self.c.get("/api/nodes/TEST_001/telemetry/missing?hours=1").json["statistics"]["sample_count"],0)
 def test_state_and_future_custom_sensor(self):
  path="/api/nodes/TEST_002/parameters"
  payload={"parameter_id":"custom_motion","parameter_name":"Motion at door","parameter_type":"Motion Detection","data_type":"BOOL","unit":"","display_enabled":False,"widget_config":{"source":"node_telemetry","source_field":"motion","icon":"activity","color":"#7C3AED","category":"custom","widget_type":"state"}}
  self.assertEqual(self.c.post(path,json=payload).status_code,200)
  self.c.post("/api/telemetry",json={"node_id":"TEST_002","parameters":{"motion":"OPEN"}})
  latest=self.c.get(path+"/latest").json["parameters"]
  self.assertEqual(next(x for x in latest if x["parameter_id"]=="custom_motion")["text_value"],"OPEN")
  self.assertEqual(self.c.put(path+"/custom_motion",json={"display_enabled":True}).status_code,200)
if __name__=="__main__":unittest.main(verbosity=2)
