import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from workspace_views import public_radio_signal, radio_config_view


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
