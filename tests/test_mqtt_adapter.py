"""The insecure legacy adapter must fail closed after migration."""
import unittest
from gateway_fixture import seed
import mqtt_adapter
class LegacyMqttTests(unittest.TestCase):
    def test_migration_required(self):
        with self.assertRaisesRegex(ValueError,'MIGRATION_REQUIRED'):
            mqtt_adapter.build_client('broker',1883,'fixture','fixture',None,True)
