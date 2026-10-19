"""Typed sensor payload validation; no gas concentration inference."""
import math
SPECS={
 'DHT11':{'temperature':(0,50,'C'),'humidity':(0,100,'%RH')},
 'INA219':{'bus_voltage':(0,26,'V'),'shunt_voltage':(-320,320,'mV'),'current':(-320,320,'A'),'power':(-8320,8320,'W')},
 'MQ135':{'mq135_adc_raw':(0,4095,'count'),'mq135_pin_mv':(0,3300,'mV')}}
PRECISION={'bus_voltage':3,'shunt_voltage':3,'current':5,'power':5,'mq135_adc_raw':0,'mq135_pin_mv':0}
def validate(body):
 kind=body.get('sensor_type','DHT11');values=body.get('parameters')
 if not isinstance(kind,str) or kind not in SPECS or type(body.get('valid')) is not bool or not isinstance(values,dict):raise ValueError('INVALID_SENSOR_SCHEMA')
 if not body['valid']:
  if values:raise ValueError('INVALID_SAMPLE_HAS_READINGS')
  return kind,values
 expected=set(SPECS[kind]);keys=set(values)
 if kind=='INA219':
  if keys not in ({'bus_voltage','shunt_voltage'},expected):raise ValueError('INVALID_SENSOR_FIELDS')
 elif keys!=expected:raise ValueError('INVALID_SENSOR_FIELDS')
 for key,value in values.items():
  lo,hi,_=SPECS[kind][key]
  if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi or (kind=='MQ135' and type(value) is not int) or (kind=='INA219' and key=='shunt_voltage' and abs(value)>=320):raise ValueError('INVALID_SENSOR_MEASUREMENT')
 return kind,values
