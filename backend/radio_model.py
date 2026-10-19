"""Explicitly simulated addressed radio, matching the portable binary framing core.
Not an E220 hardware implementation and not enabled by firmware radio settings.
"""
import json,math,struct,zlib
import device_api
HEADER=struct.Struct('<BBBBIBBH')
TYPES={name:i+1 for i,name in enumerate(('HELLO','HEARTBEAT','TELEMETRY','COMMAND','ACK','RESPONSE','STATUS','EVENT','ALARM','DIAGNOSTIC'))}
def encode(source,destination,kind,ttl,sequence,payload):
 device_api.safe_id(source);device_api.safe_id(destination)
 if not 1<=kind<=10 or not 1<=ttl<=15 or len(payload)>128:raise ValueError('INVALID_RADIO_FRAME')
 a=source.encode();b=destination.encode();raw=HEADER.pack(0xe2,1,kind,ttl,sequence,len(a),len(b),len(payload))+a+b+payload
 return raw+struct.pack('<I',zlib.crc32(raw))
def decode(raw):
 if not 18<=len(raw)<=240:raise ValueError('INVALID_RADIO_LENGTH')
 magic,version,kind,ttl,sequence,a,b,n=HEADER.unpack(raw[:12])
 if magic!=0xe2 or version!=1 or not 1<=kind<=10 or not 1<=ttl<=15 or n>128 or len(raw)!=16+a+b+n or zlib.crc32(raw[:-4])!=struct.unpack('<I',raw[-4:])[0]:raise ValueError('INVALID_RADIO_FRAME')
 source=raw[12:12+a].decode('ascii');destination=raw[12+a:12+a+b].decode('ascii');device_api.safe_id(source);device_api.safe_id(destination)
 return source,destination,kind,ttl,sequence,raw[12+a+b:-4]
class SimulatedRadio:
 def __init__(self):self.drop_next=0;self.corrupt_next=False;self.transmitted=0;self.received=0;self.rejected=0;self.sequence=0
 def transfer(self,packet,source,destination):
  device_api.validate_packet(packet);raw=json.dumps(packet,separators=(',',':')).encode()
  if len(raw)>4096:raise ValueError('RADIO_MESSAGE_TOO_LARGE')
  chunks=[raw[i:i+124] for i in range(0,len(raw),124)];self.sequence=(self.sequence+1)&0xffffffff;received={}
  for i,chunk in enumerate(chunks):
   data=encode(source,destination,TYPES[packet['type']],packet['ttl'],self.sequence,struct.pack('<BBH',i,len(chunks),len(raw))+chunk);self.transmitted+=1
   if self.drop_next:self.drop_next-=1;continue
   if self.corrupt_next:data=data[:-1]+bytes([data[-1]^1]);self.corrupt_next=False
   try:
    sender,target,kind,ttl,sequence,payload=decode(data)
    index,count,total=struct.unpack('<BBH',payload[:4])
    if kind!=TYPES[packet['type']] or sender!=source or target!=destination or sequence!=self.sequence or count!=len(chunks) or total!=len(raw) or index>=count:raise ValueError('MISADDRESSED_FRAGMENT')
    received[index]=payload[4:];self.received+=1
   except (ValueError,UnicodeError,struct.error):self.rejected+=1
  if len(received)!=len(chunks):return None
  result=json.loads(b''.join(received[i] for i in range(len(chunks))));device_api.validate_packet(result);return result
 def status(self):return dict(simulated=True,state='SIMULATED_RADIO',transmitted=self.transmitted,received=self.received,rejected=self.rejected,rssi=None,snr=None)
