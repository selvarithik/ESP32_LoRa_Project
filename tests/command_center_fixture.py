"""Disposable Gateway and software-only Master/Slave, loopback port 5084."""
import tempfile,threading,time
from pathlib import Path
from gateway_fixture import seed,server
import device_api as api
from device_simulator import SimulatedNode,SimulatedMaster
if __name__=='__main__':
 seed();folder=tempfile.TemporaryDirectory();master_id='SIM-COMMAND-MASTER';node_id='SIM-COMMAND-SLAVE'
 api.enroll(master_id,'Simulated Master','MASTER');api.enroll(node_id,'Simulated Slave','NODE',master_id,'4')
 nodes=[SimulatedNode(i,master_id,Path(folder.name)/(i+'.json')) for i in (master_id,node_id)]
 def exchange(frame):
  result=api.ingest(master_id,frame,transport='SIMULATED_ONLY');result['commands']=api.pending_commands(master_id);return result
 master=SimulatedMaster(master_id,nodes,exchange);master.announce()
 def worker():
  while True:
   api.ingest(master_id,api.packet('STATUS',node_id,'GATEWAY',nodes[1].status()),transport='SIMULATED_ONLY');master.tick();time.sleep(.25)
 threading.Thread(target=worker,daemon=True).start()
 server.socketio.run(server.app,host='127.0.0.1',port=5084,debug=False,allow_unsafe_werkzeug=True)
