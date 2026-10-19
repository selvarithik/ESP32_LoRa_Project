"""Disposable dashboard + actual local HTTP listener for browser refresh regression."""
import hashlib
from gateway_fixture import seed,server
import database,device_api,local_ip
seed()
device_api.enroll('REFRESH-MASTER','Refresh Master','MASTER')
local_ip.save_credential('REFRESH-MASTER','fixture-refresh-token-only-not-deployment')
local_ip.service.start(dict(bind_address='127.0.0.1',port=5063))
server.socketio.run(server.app,host='127.0.0.1',port=5062,debug=False,allow_unsafe_werkzeug=True)
