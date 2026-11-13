import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from workspace_views import public_radio_signal, radio_config_view, radio_metrics_view


class RadioMonitorTests(unittest.TestCase):
    def test_rssi_preserves_invalid_raw(self):
        for raw in (0, 114, 246, 254, 255):
            self.assertEqual(public_radio_signal({'rssi_raw': raw, 'rssi_dbm': -33}),
                             {'rssi_raw': raw, 'rssi_valid': False, 'rssi_dbm': None})
        self.assertEqual(public_radio_signal({'rssi_raw': 223})['rssi_dbm'], -33)
        self.assertEqual(public_radio_signal({'rssi_raw': 115})['rssi_dbm'], -141)
        self.assertEqual(public_radio_signal({'rssi_raw': 245})['rssi_dbm'], -11)
        self.assertIsNone(public_radio_signal({'rssi_dbm': -1})['rssi_dbm'])

    def test_frequency_power_advisory(self):
        config = radio_config_view({'channel': 16, 'power_dbm': 10, 'key': 'discarded'})
        self.assertEqual(config['frequency_khz'], 866125)
        self.assertEqual(config['frequency_flag'], 'OK')
        self.assertEqual(config['key'], 'not readable')
        invalid = radio_config_view({'channel': 18, 'power_dbm': 22})
        self.assertEqual(invalid['frequency_flag'], 'RED')
        self.assertEqual(invalid['power_flag'], 'RED')
        self.assertEqual(radio_config_view({'channel': 17, 'power_dbm': 13})['power_flag'], 'AMBER')

    def test_alarm_thresholds(self):
        report = {'used_us': 81, 'limit_us': 100, 'auth_failures': 3,
                  'protocol_mismatches': 1, 'poll_interval_ms': 60000}
        metrics = radio_metrics_view(report, {'valid_age_ms': 590000}, 180001)
        self.assertEqual(set(metrics['alarms']), {'NO_RECENT_VALID_RSSI', 'AUTH_FAILURES',
                        'PROTOCOL_MISMATCH', 'AIRTIME_OVER_80_PERCENT', 'STALE_RADIO_REPORT'})
        self.assertEqual(radio_metrics_view({'used_us': 80, 'limit_us': 100}, {}, 0)['alarms'], [])


    def test_retained_topic_schema_and_availability(self):
        import json
        from datetime import datetime
        from lora_retained import retained_topics, will
        profile = {'topic_prefix':'example','gateway_id':'LAB'}
        node = {'node_id':'NODE','device_role':'NODE','firmware_version':'example',
                'last_seen':'2026-11-14T00:00:00','latest_status':json.dumps({
                    'radio_signal':{'rssi_raw':223},'bench_build':True})}
        prefix = 'example/LAB/lora'
        topics = retained_topics(profile,node,datetime(2026,11,14,0,1))
        self.assertEqual(set(topics), {f'{prefix}/NODE/{kind}' for kind in
                         ('status','link','config','airtime','counters','alarms','telemetry/ina219')})
        self.assertTrue(all(payload['schema_version']==1 for payload in topics.values()))
        self.assertTrue(topics[f'{prefix}/NODE/status']['online'])
        self.assertEqual(topics[f'{prefix}/NODE/link']['rssi_dbm'],-33)
        stale = retained_topics(profile,node,datetime(2026,11,14,0,10))
        self.assertFalse(stale[f'{prefix}/NODE/status']['online'])
        self.assertIn('NODE_OFFLINE',stale[f'{prefix}/NODE/alarms']['active'])
        self.assertEqual(will(profile),(f'{prefix}/availability',
                         {'schema_version':1,'online':False,'source':'gateway'}))
