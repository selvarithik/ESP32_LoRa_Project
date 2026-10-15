"""Regression tests use a disposable SQLite database and firmware directory."""
import io
import unittest
from datetime import datetime, timedelta
from gateway_fixture import seed, server


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = seed()

    def get(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, (path, response.get_data(as_text=True)))
        result = response.json
        response.close()
        return result

    def post(self, path, payload, code=200):
        response = self.client.post(path, json=payload)
        self.assertEqual(response.status_code, code, (path, response.json))
        return response.json

    def test_pages_and_assets(self):
        for path in ['/', '/nodes', '/sensors', '/command-center', '/communication', '/firmware', '/logs', '/system-overview', '/system', '/chat', '/static/css/dashboard.css', '/static/js/dashboard.js', '/static/vendor/socket.io.min.js', '/static/img/logo-icon.svg']:
            with self.subTest(path=path):
                self.get(path)

    def test_api_reads(self):
        for path in ['/api/status', '/api/nodes', '/api/logs', '/api/live/snapshot', '/api/parameters/defaults', '/api/commands', '/api/commands/node/TEST_001', '/api/chat/users', '/api/chat/conversations?user_id=GATEWAY', '/api/firmware/releases', '/api/firmware/devices', '/api/firmware/jobs', '/api/firmware/config']:
            with self.subTest(path=path):
                self.get(path)
        for suffix in ['status', 'mesh', 'statistics', 'settings', 'master', 'gateway', 'queue/incoming', 'queue/outgoing']:
            self.get('/api/communication/' + suffix)
        for suffix in ['', '/config', '/parameters', '/parameters/latest', '/parameters/statistics', '/parameters/temperature/statistics', '/parameters/temperature/graph', '/telemetry/temperature', '/telemetry/compare?parameters=temperature,humidity']:
            self.get('/api/nodes/TEST_001' + suffix)

    def test_configuration_roundtrip(self):
        path = '/api/nodes/TEST_001/config'
        self.assertEqual(self.get(path)['config']['watchdog']['timeout_s'], 60)
        response = self.client.put(path, json={'config': {'watchdog': {'timeout_s': 125}, 'extension': {'keep': 1}}})
        self.assertEqual(response.status_code, 200, response.json)
        config = self.get(path)['config']
        self.assertEqual(config['watchdog']['timeout_s'], 125)
        self.assertTrue(config['time']['sync_enabled'])
        self.assertEqual(config['extension']['keep'], 1)
        self.assertEqual(self.client.put(path, json={'config': {'watchdog': {'timeout_s': -1}}}).status_code, 400)
        self.post(path + '/reset', {})
        self.assertEqual(self.get(path)['config']['watchdog']['timeout_s'], 60)
        self.assertEqual(self.client.get('/api/nodes/missing/config').status_code, 404)

    def test_http_and_socket_telemetry(self):
        socket = server.socketio.test_client(server.app)
        now = datetime.now().isoformat()
        self.post('/api/telemetry', {'node_id': 'TEST_001', 'timestamp': now, 'parameters': {'temperature': 32.5}})
        events = socket.get_received()
        event = next(item for item in events if item['name'] == 'telemetry_update')['args'][0]
        self.assertEqual(event['parameters'][0]['value'], 32.5)
        self.assertIn('alarm_status', event['parameters'][0])
        socket.emit('telemetry', {'node_id': 'TEST_002', 'sensor': {'temperature': 29.1, 'humidity': 51}, 'battery': {'percent': 80}, 'lora': {'rssi': -80, 'snr': 9}})
        names = [event['name'] for event in socket.get_received()]
        self.assertIn('node_update', names)
        self.assertIn('telemetry_update', names)
        socket.disconnect()

    def test_out_of_order_telemetry(self):
        now = datetime.now()
        self.post('/api/telemetry', {'node_id': 'TEST_003', 'timestamp': now.isoformat(), 'parameters': {'temperature': 40}})
        self.post('/api/telemetry', {'node_id': 'TEST_003', 'timestamp': (now - timedelta(minutes=2)).isoformat(), 'parameters': {'temperature': 10}})
        params = self.get('/api/nodes/TEST_003/parameters/latest')['parameters']
        self.assertEqual(next(p['value'] for p in params if p['parameter_id'] == 'temperature'), 40)

    def test_invalid_telemetry(self):
        for data in [[], {'node_id': 'TEST_001', 'parameters': []}, {'node_id': 'TEST_001', 'timestamp': 'bad', 'parameters': {}}]:
            with self.subTest(data=data):
                self.post('/api/telemetry', data, 400)

    def test_command_types_and_lifecycle(self):
        socket = server.socketio.test_client(server.app)
        for kind in ['STATUS', 'PING', 'WIFI_SCAN', 'WIFI_CONNECT', 'RESTART', 'GET_CONFIG', 'SET_INTERVAL', 'CUSTOM']:
            cmd = self.post('/api/commands', {'node_id': 'TEST_001', 'command_type': kind, 'payload': {'message': 'test', 'ssid': 'test', 'password': 'test', 'interval_ms': 2000}}, 201)['command']
            cid = cmd['command_id']
            self.post(f'/api/commands/{cid}/cancel', {'reason': 'test'})
            self.get(f'/api/commands/{cid}/events')
        cmd = self.post('/api/commands', {'node_id': 'TEST_001', 'command_type': 'PING', 'payload': {'message': 'echo'}}, 201)['command']
        cid = cmd['command_id']
        self.post(f'/api/commands/{cid}/state', {'state': 'SENT'})
        self.post(f'/api/commands/{cid}/ack', {'node_id': 'TEST_001', 'status': 'OK'})
        self.post(f'/api/commands/{cid}/execute', {'node_id': 'TEST_001'})
        self.post(f'/api/commands/{cid}/response', {'node_id': 'TEST_001', 'status': 'SUCCESS', 'data': {'echo': 'test'}})
        self.assertEqual(self.get(f'/api/commands/{cid}')['command']['state'], 'COMPLETED')
        self.assertIn('command_update', [event['name'] for event in socket.get_received()])
        socket.disconnect()

    def test_command_timeout_retry(self):
        cmd = self.post('/api/commands', {'node_id': 'TEST_001', 'command_type': 'STATUS'}, 201)['command']
        cid = cmd['command_id']
        self.post(f'/api/commands/{cid}/timeout', {'reason': 'test timeout'})
        self.assertEqual(self.get(f'/api/commands/{cid}')['command']['state'], 'TIMEOUT')
        self.post(f'/api/commands/{cid}/retry', {})

    def test_chat_roundtrip(self):
        response = self.post('/api/chat/messages', {'sender_id': 'GATEWAY', 'recipient_id': 'TEST_001', 'content': 'sample <safe> message'})
        messages = self.get('/api/chat/messages?user_id=GATEWAY&with_user_id=TEST_001')['messages']
        self.assertTrue(messages)
        mid = messages[-1]['message_id']
        self.get('/api/chat/messages/' + mid)
        self.post('/api/chat/messages/' + mid + '/delivered', {})
        self.post('/api/chat/messages/' + mid + '/seen', {'receiver_id': 'TEST_001'})

    def test_mesh_settings(self):
        for node in ['TEST_001', 'TEST_002']:
            self.post('/api/communication/mesh/nodes', {'node_id': node, 'role': 'NODE'})
        self.post('/api/communication/mesh/link', {'node_id': 'TEST_001', 'neighbor_id': 'TEST_002', 'rssi': -80, 'snr': 9, 'success_rate': 99})
        self.get('/api/communication/mesh/TEST_001/neighbors')
        settings = self.get('/api/communication/settings')
        response = self.client.put('/api/communication/settings', json=settings.get('settings', settings))
        self.assertEqual(response.status_code, 200, response.json)

    def test_logs_filter(self):
        server.create_log('warning', 'TEST', 'sample filter marker')
        logs = self.get('/api/logs?severity=warning&search=sample%20filter%20marker')['logs']
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['severity'], 'warning')

    def test_firmware_invalid_upload(self):
        response = self.client.post('/api/firmware/releases', data={'firmware': (io.BytesIO(b'bad'), 'bad.txt'), 'version': '2.0.0', 'build': '1', 'hardware_family': 'ESP32', 'hardware_model': 'ESP32-S3', 'hardware_revision': 'A'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json['success'])

    def test_firmware_release_and_interrupted_job(self):
        response = self.client.post('/api/firmware/releases', data={
            'firmware': (io.BytesIO(bytes([0xE9]) + bytes(1023)), 'sample.bin'),
            'version': '2.0.0', 'build': '1', 'hardware_family': 'ESP32',
            'hardware_model': 'ESP32-S3', 'hardware_revision': 'A',
        })
        self.assertEqual(response.status_code, 201, response.json)
        release = response.json['release']
        rid = release['release_id']
        for state in ['TESTING', 'APPROVED', 'ACTIVE']:
            self.post(f'/api/firmware/releases/{rid}/status', {'status': state})
        self.get(f'/api/firmware/releases/{rid}')
        download = self.client.get(f'/api/firmware/download/{rid}')
        self.assertEqual(download.status_code, 200)
        self.assertEqual(len(download.data), 1024)
        download.close()
        self.post('/api/firmware/check', {
            'node_id': 'OTA_TEST', 'hardware_family': 'ESP32', 'hardware_model': 'ESP32-S3',
            'hardware_revision': 'A', 'firmware_version': '1.0.0', 'build': 0,
            'bootloader_version': '1.0.0', 'security_version': 0, 'channel': 'stable',
        })
        job = self.post('/api/firmware/update', {'node_id': 'OTA_TEST', 'release_id': rid}, 201)['job']
        jid = job['job_id']
        self.post(f'/api/firmware/jobs/{jid}/state', {'state': 'DOWNLOADING', 'progress': 30})
        self.post(f'/api/firmware/jobs/{jid}/state', {'state': 'FAILED', 'error': 'Simulated interrupted link'})
        self.assertEqual(self.get(f'/api/firmware/jobs/{jid}')['job']['state'], 'FAILED')

    def test_node_and_parameter_crud(self):
        self.post('/api/nodes', {'node_id': 'CRUD', 'name': 'Sample', 'communication_type': 'LoRa'})
        self.post('/api/nodes/CRUD/parameters', {'parameter_id': 'x', 'parameter_name': 'Sample', 'parameter_type': 'TEST', 'data_type': 'FLOAT'})
        self.assertEqual(self.client.put('/api/nodes/CRUD/parameters/x', json={'parameter_name': 'Updated'}).status_code, 200)
        self.post('/api/nodes/CRUD/parameters/x/enable', {'enabled': False})
        self.assertEqual(self.client.delete('/api/nodes/CRUD/parameters/x').status_code, 200)
        self.post('/api/nodes/CRUD/enable', {'enabled': False})
        self.assertEqual(self.client.delete('/api/nodes/CRUD').status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
