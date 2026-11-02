"""Isolated manual illustrations. Never starts a broker or reads production data."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from gateway_fixture import seed,server
import device_api as api
client=seed()
master='DEMO-MASTER'
api.enroll(master,'Demonstration Master','MASTER')
for field,value in [('temperature',26.4),('humidity',62.0)]:
 client.post('/api/nodes/'+master+'/parameters',json={'parameter_id':field,'parameter_name':field.title(),'parameter_type':field.upper(),'data_type':'FLOAT','unit':'C' if field=='temperature' else '%RH','enabled':True,'graph_enabled':True,'sensor_id':master+'-DHT11-'+field})
client.post('/api/telemetry',json={'node_id':master,'parameters':{'temperature':26.4,'humidity':62.0}})
for kind,payload in [('PING',{'message':'Manual demonstration only'}),('GET_STATUS',{})]:
 response=client.post('/api/v1/commands',json={'node_id':master,'command_type':kind,'payload':payload})
 assert response.status_code==201,response.status_code
 cid=response.json['command']['command_id']
 api.pending_commands(master)
 for category,status,data in [('ACK','ACCEPTED',{}),('RESPONSE','SUCCESS',{'ok':True,'demonstration':True})]:
  api.ingest(master,api.packet(category,master,'GATEWAY',{'command_id':cid,'status':status,'data':data},correlation_id=cid))
server.socketio.run(server.app,host='127.0.0.1',port=5063,debug=False,allow_unsafe_werkzeug=True)
