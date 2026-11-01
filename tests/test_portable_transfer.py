import importlib.util
from contextlib import closing
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile
from cryptography.fernet import Fernet

spec = importlib.util.spec_from_file_location('portable_transfer', Path(__file__).resolve().parents[1] / 'tools/portable_transfer.py')
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI required')
class PortableTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        db = sqlite3.connect(self.source / 'gateway.db')
        db.execute('CREATE TABLE readings (value INTEGER)')
        db.execute('INSERT INTO readings VALUES (42)')
        db.commit()
        db.close()
        (self.source / 'mqtt-secrets.bin').write_bytes(transfer.SecretFile.protect(b'{"test":"fixture-only"}'))
        (self.source / 'session.key').write_bytes(b'fixture-session-key')
        self.archive = self.base / 'package/data.sgwportable'
        self.key = self.base / 'keys/transfer.key'

    def test_round_trip_and_no_overwrite(self):
        self.assertEqual(transfer.export(self.source, self.archive, self.key), 3)
        self.assertNotIn(b'fixture-only', self.archive.read_bytes())
        target = self.base / 'restored'
        transfer.restore(target, self.archive, self.key)
        self.assertEqual(transfer.SecretFile.protect((target / 'mqtt-secrets.bin').read_bytes(), True), b'{"test":"fixture-only"}')
        with closing(sqlite3.connect(target / 'gateway.db')) as db:
            self.assertEqual(db.execute('SELECT value FROM readings').fetchone()[0], 42)
        with self.assertRaises(ValueError):
            transfer.restore(target, self.archive, self.key)

    def test_wrong_key_and_tamper_fail_closed(self):
        transfer.export(self.source, self.archive, self.key)
        original = self.key.read_bytes()
        self.key.write_bytes(Fernet.generate_key())
        with self.assertRaises(Exception):
            transfer.decode(self.archive, self.key)
        self.key.write_bytes(original)
        raw = bytearray(self.archive.read_bytes())
        raw[len(raw) // 2] ^= 1
        self.archive.write_bytes(raw)
        with self.assertRaises(Exception):
            transfer.restore(self.base / 'bad', self.archive, self.key)
        self.assertFalse((self.base / 'bad').exists())

    def test_running_server_and_unsafe_name_rejected(self):
        with transfer.InstanceLock(self.source):
            with self.assertRaises(Exception):
                transfer.export(self.source, self.archive, self.key)
        self.key.parent.mkdir()
        key = Fernet.generate_key()
        self.key.write_bytes(key)
        self.archive.parent.mkdir()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            z.writestr('../escape.bin', b'bad')
            z.writestr('manifest.json', json.dumps({'schema': 1, 'files': {'../escape.bin': {'encoding': 'raw'}}}))
        self.archive.write_bytes(Fernet(key).encrypt(buffer.getvalue()))
        with self.assertRaises(ValueError):
            transfer.decode(self.archive, self.key)


if __name__ == '__main__':
    unittest.main()
