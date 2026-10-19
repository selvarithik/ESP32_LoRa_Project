"""Headless Part 1 contract tests: disposable databases, no serial hardware/broker."""
import copy
import json
import unittest
from datetime import datetime, timedelta
from gateway_fixture import seed, server
import command_manager
import database
import device_api as api

class DeviceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = seed()
        cls.token = api.enroll('ESP32-MASTER', 'Bench master', 'MASTER')
        api.enroll('ESP32-NODE', 'Bench node', 'NODE', 'ESP32-MASTER', '1')
        cls.device = server.app.test_client()
        cls.headers = {'X-Device-ID': 'ESP32-MASTER', 'Authorization': 'Bearer ' + cls.token}

    def uplink(self, kind, body, source='ESP32-NODE', frame=None, code=200):
        f = frame or api.packet(kind, source, 'GATEWAY', body)
        r = self.device.post('/api/v1/device/exchange', json=f, headers=self.headers)
        self.assertEqual(r.status_code, code, r.json)
        return r.json

    def test_registration_and_real_readings(self):
        self.uplink('HELLO', {'device_id':'ESP32-NODE','role':'NODE','master_id':'ESP32-MASTER','heartbeat_seconds':15,'configuration_revision':2,'firmware_version':'1.0.0-part1'})
        frame = api.packet('TELEMETRY','ESP32-NODE','GATEWAY',{'valid':True,'parameters':{'temperature':27.5,'humidity':55}})
        self.uplink('TELEMETRY',{},frame=frame)
        self.assertTrue(self.uplink('TELEMETRY',{},frame=frame)['duplicate'])
        db = database.get_connection()
        try:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM telemetry_values WHERE node_id='ESP32-NODE' AND parameter_id='temperature' AND value=27.5").fetchone()[0],1)
        finally: db.close()
        latest = self.admin.get('/api/nodes/ESP32-NODE/parameters/latest').json['parameters']
        self.assertEqual(next(p for p in latest if p['parameter_id']=='temperature')['value'],27.5)

    def test_absent_sensor_has_no_values(self):
        db=database.get_connection()
        try: before=db.execute("SELECT COUNT(*) FROM telemetry_values WHERE node_id='ESP32-NODE'").fetchone()[0]
        finally: db.close()
        self.uplink('TELEMETRY',{'valid':False,'status':'NOT_CONFIGURED','parameters':{}})
        self.uplink('TELEMETRY',{'valid':False,'parameters':{'temperature':0}},code=400)
        db=database.get_connection()
        try: self.assertEqual(before,db.execute("SELECT COUNT(*) FROM telemetry_values WHERE node_id='ESP32-NODE'").fetchone()[0])
        finally: db.close()

    def test_end_to_end_command_ack_response(self):
        r=self.admin.post('/api/v1/commands',json={'node_id':'ESP32-NODE','command_type':'PING','command_id':'CMD-PART1-TEST'})
        self.assertEqual(r.status_code,201,r.json)
        poll=self.uplink('STATUS',{'device_id':'ESP32-MASTER','role':'MASTER','master_id':'ESP32-MASTER'},source='ESP32-MASTER')
        command=next(c for c in poll['commands'] if c['message_id']=='CMD-PART1-TEST')
        self.assertEqual(api.validate_packet(command)['command'],'PING')
        self.assertEqual(command_manager.get_command('CMD-PART1-TEST')['state'],'SENT')
        for kind,body in [('ACK',{'command_id':'CMD-PART1-TEST','status':'RECEIVED'}),('RESPONSE',{'command_id':'CMD-PART1-TEST','status':'SUCCESS','data':{'ok':True}})]:
            f=api.packet(kind,'ESP32-NODE','GATEWAY',body,correlation_id='CMD-PART1-TEST')
            self.uplink(kind,body,frame=f)
            self.assertTrue(self.uplink(kind,body,frame=f)['duplicate'])
        self.assertEqual(command_manager.get_command('CMD-PART1-TEST')['state'],'COMPLETED')
        duplicate=self.admin.post('/api/v1/commands',json={'node_id':'ESP32-NODE','command_type':'PING','command_id':'CMD-PART1-TEST'})
        self.assertEqual(duplicate.status_code,200,duplicate.json)
        self.assertTrue(duplicate.json['duplicate'])
        conflict=self.admin.post('/api/v1/commands',json={'node_id':'ESP32-NODE','command_type':'GET_STATUS','command_id':'CMD-PART1-TEST'})
        self.assertEqual(conflict.status_code,409)

    def test_packet_validation(self):
        valid=api.packet('TELEMETRY','ESP32-NODE','GATEWAY',{'valid':True,'parameters':{'temperature':25,'humidity':50}})
        for key,value in [('protocol_version',2),('ttl',0),('type','OTA_REQUEST'),('source','bad/id'),('payload_crc32',1),('payload_length',0),('sequence_number',True),('final_destination_id','WRONG')]:
            f=copy.deepcopy(valid);f[key]=value
            self.uplink('TELEMETRY',{},frame=f,code=400)
        f=copy.deepcopy(valid);f['payload']=json.loads(f['payload'])
        self.uplink('TELEMETRY',{},frame=f,code=400)
        self.uplink('TELEMETRY',{'valid':True,'parameters':{'temperature':'25','humidity':50}},code=400)

    def test_source_assignment_and_identity(self):
        self.uplink('STATUS',{'device_id':'someone-else','role':'NODE','master_id':'ESP32-MASTER'},code=400)
        self.uplink('TELEMETRY',{'valid':False,'parameters':{}},source='UNENROLLED',code=403)
        other=api.enroll('ESP32-OTHER','Other master','MASTER')
        f=api.packet('TELEMETRY','ESP32-NODE','GATEWAY',{'valid':False,'parameters':{}})
        r=self.device.post('/api/v1/device/exchange',json=f,headers={'X-Device-ID':'ESP32-OTHER','Authorization':'Bearer '+other})
        self.assertEqual(r.status_code,403)
        with self.assertRaises(ValueError): api.enroll('DUP-NODE','Duplicate logical ID','NODE','ESP32-MASTER','1')

    def test_authentication_and_no_secret_exposure(self):
        f=api.packet('STATUS','ESP32-MASTER','GATEWAY',{'device_id':'ESP32-MASTER','role':'MASTER','master_id':'ESP32-MASTER'})
        self.assertEqual(self.device.post('/api/v1/device/exchange',json=f).status_code,401)
        self.assertEqual(self.device.post('/api/commands',json={'node_id':'ESP32-NODE','command_type':'PING'}).status_code,401)
        self.assertEqual(self.device.get('/api/nodes').status_code,401)
        self.assertEqual(self.device.get('/api/auth/status').json['authenticated'],False)
        self.assertNotIn('device_token_hash',self.admin.get('/api/nodes').get_data(as_text=True))
        self.assertNotIn('device_token_hash',self.admin.get('/api/nodes/ESP32-MASTER').get_data(as_text=True))
        self.assertNotIn(self.token,self.admin.get('/api/v1/devices').get_data(as_text=True))
        socket=server.socketio.test_client(server.app)
        self.assertFalse(socket.is_connected())

    def test_conflicting_duplicate_and_receipt_persistence(self):
        f=api.packet('TELEMETRY','ESP32-NODE','GATEWAY',{'valid':False,'parameters':{}})
        self.uplink('TELEMETRY',{},frame=f)
        api.migrate()
        self.assertTrue(self.uplink('TELEMETRY',{},frame=f)['duplicate'])
        changed=api.packet('TELEMETRY','ESP32-NODE','GATEWAY',{'valid':False,'status':'different','parameters':{}},message_id=f['message_id'])
        self.uplink('TELEMETRY',{},frame=changed,code=400)

    def test_content_type_size_and_disabled_device(self):
        self.assertEqual(self.device.post('/api/v1/device/exchange',data='{}',headers=self.headers).status_code,415)
        self.assertEqual(self.device.post('/api/v1/device/exchange',data='x'*4097,content_type='application/json',headers=self.headers).status_code,413)
        api.enroll('DISABLED','Disabled','NODE','ESP32-MASTER','9')
        db=database.get_connection()
        try:
            db.execute("UPDATE nodes SET enabled=0 WHERE node_id='DISABLED'");db.commit()
        finally: db.close()
        self.uplink('TELEMETRY',{'valid':False,'parameters':{}},source='DISABLED',code=403)

    def test_command_timeout_and_safe_subset(self):
        cmd=command_manager.create_command('ESP32-NODE','PING',command_id='CMD-EXPIRED')
        db=database.get_connection()
        try:
            db.execute('UPDATE commands SET timeout_at=? WHERE command_id=?',((datetime.now()-timedelta(seconds=1)).isoformat(),cmd['command_id']));db.commit()
        finally: db.close()
        api.pending_commands('ESP32-MASTER')
        self.assertEqual(command_manager.get_command(cmd['command_id'])['state'],'TIMEOUT')
        self.assertEqual(self.admin.post('/api/v1/commands',json={'node_id':'ESP32-NODE','command_type':'FACTORY_RESET'}).status_code,400)

    def test_crc_golden_vector(self):
        import zlib
        self.assertEqual(zlib.crc32(b'123456789'),0xcbf43926)
        frame=api.packet('EVENT','ESP32-NODE','GATEWAY',{'message':'sensor disconnected'})
        self.assertEqual(api.validate_packet(frame),{'message':'sensor disconnected'})

    def test_status_health_and_remote_config(self):
        self.uplink('HEARTBEAT',{'device_id':'ESP32-NODE','role':'NODE','master_id':'ESP32-MASTER','heartbeat_seconds':10})
        self.assertEqual(self.admin.get('/api/v1/devices/ESP32-NODE/status').json['device']['health'],'ONLINE')
        db=database.get_connection()
        try:
            db.execute('UPDATE nodes SET last_seen=? WHERE node_id=?',((datetime.now()-timedelta(seconds=25)).isoformat(),'ESP32-NODE'));db.commit()
        finally:db.close()
        self.assertEqual(self.admin.get('/api/v1/devices/ESP32-NODE/status').json['device']['health'],'STALE')
        self.assertEqual(self.admin.post('/api/v1/devices/ESP32-NODE/config',json={'telemetry_seconds':1}).status_code,400)
        self.assertEqual(self.admin.post('/api/v1/devices/ESP32-NODE/config',json={'wifi_password':'rejected'}).status_code,400)
        response=self.admin.post('/api/v1/devices/ESP32-NODE/config',json={'telemetry_seconds':15})
        self.assertEqual(response.status_code,202,response.json)
        self.assertEqual(response.json['command']['state'],'QUEUED')
        self.assertEqual(self.admin.get('/api/v1/devices/ESP32-NODE/config').json['source'],'LAST_RECEIVED_STATUS')

    def test_cross_device_feedback_and_redaction(self):
        command_manager.create_command('TEST_001','PING',command_id='CMD-OTHER-DEVICE')
        f=api.packet('ACK','ESP32-NODE','GATEWAY',{'command_id':'CMD-OTHER-DEVICE','status':'RECEIVED'},correlation_id='CMD-OTHER-DEVICE')
        self.uplink('ACK',{},frame=f,code=403)
        self.uplink('DIAGNOSTIC',{'message':'sensor offline','wifi_password':'must-not-persist','nested':{'mesh_key':'secret'}})
        text=self.admin.get('/api/v1/devices/ESP32-NODE/diagnostics').get_data(as_text=True)
        self.assertIn('sensor offline',text)
        self.assertNotIn('must-not-persist',text)
        self.assertNotIn('mesh_key',text)

if __name__=='__main__': unittest.main()
