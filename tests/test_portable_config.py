import json
import tempfile
import unittest
from pathlib import Path

from gateway_fixture import server
from deployment_config import DeploymentError, load_portable


class PortableConfigTests(unittest.TestCase):
    def test_missing_file_has_setup_instructions(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(DeploymentError, 'Copy config.example.json'):
                load_portable(Path(directory) / 'config.json')

    def test_local_only_and_boolean_acl_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            path.write_text(json.dumps({'server': {'port': 5151}}), encoding='utf-8-sig')
            settings, _ = load_portable(path)
            self.assertEqual((settings['host'], settings['port']), ('127.0.0.1', 5151))
            path.write_text(json.dumps({'server': {'host': '0.0.0.0'}}))
            with self.assertRaises(DeploymentError):
                load_portable(path)
            path.write_text(json.dumps({'mqtt_acl_confirmed': 'true'}))
            with self.assertRaises(DeploymentError):
                load_portable(path)
