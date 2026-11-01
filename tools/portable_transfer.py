"""Offline Windows-to-Windows transfer. Key and archive must travel separately."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from backup_manager import Backups, MAX_TOTAL, allowed, sqlite_bytes, verify_sqlite
from mqtt_store import SecretFile
from runtime_lock import InstanceLock
from cryptography.fernet import Fernet


def decode(archive, key):
    if Path(archive).stat().st_size > MAX_TOTAL * 2:
        raise ValueError('TRANSFER_SIZE_LIMIT')
    raw = Fernet(Path(key).read_bytes().strip()).decrypt(Path(archive).read_bytes())
    if len(raw) > MAX_TOTAL:
        raise ValueError('TRANSFER_SIZE_LIMIT')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or len(names) > 65 or sum(i.file_size for i in z.infolist()) > MAX_TOTAL:
            raise ValueError('INVALID_TRANSFER')
        manifest = json.loads(z.read('manifest.json'))
        entries = manifest['files']
        if manifest['schema'] != 1 or set(names) != set(entries) | {'manifest.json'}:
            raise ValueError('INVALID_TRANSFER')
        files = {}
        for name, meta in entries.items():
            if not allowed(name) or meta['encoding'] not in ('raw', 'dpapi'):
                raise ValueError('INVALID_TRANSFER')
            data = z.read(name)
            if len(data) != meta['bytes'] or hashlib.sha256(data).hexdigest() != meta['sha256']:
                raise ValueError('INVALID_TRANSFER')
            if meta['sqlite']:
                verify_sqlite(data)
            files[name] = data
    return manifest, files


def export(root, archive, key):
    if os.name != 'nt':
        raise ValueError('WINDOWS_REQUIRED')
    root, archive, key = map(lambda p: Path(p).resolve(), (root, archive, key))
    if archive.exists() or key.exists() or archive == key:
        raise ValueError('OUTPUT_ALREADY_EXISTS')
    if archive.parent == key.parent or root in archive.parents or root in key.parents:
        raise ValueError('USE_SEPARATE_EXTERNAL_KEY_FOLDER')
    # A cleanly stopped server provides a consistent set of databases/configuration.
    with InstanceLock(root):
        files, entries, total = {}, {}, 0
        for path in Backups(root).source_files():
            if path.name == 'restore.pending.json':
                raise ValueError('RESTORE_IN_PROGRESS')
            is_db = path.suffix in ('.db', '.sqlite', '.sqlite3')
            data = sqlite_bytes(path) if is_db else path.read_bytes()
            encoding = 'dpapi' if path.suffix == '.bin' else 'raw'
            if encoding == 'dpapi':
                data = SecretFile.protect(data, True)
            total += len(data)
            if total > MAX_TOTAL:
                raise ValueError('TRANSFER_SIZE_LIMIT')
            files[path.name] = data
            entries[path.name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), sqlite=is_db, encoding=encoding)
        if not files:
            raise ValueError('NO_DATA')
        manifest = dict(schema=1, files=entries)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in files.items():
                z.writestr(name, data)
            z.writestr('manifest.json', json.dumps(manifest))
        archive.parent.mkdir(parents=True, exist_ok=True)
        key.parent.mkdir(parents=True, exist_ok=True)
        generated = Fernet.generate_key()
        with key.open('xb') as stream:
            stream.write(generated)
        with archive.open('xb') as stream:
            stream.write(Fernet(generated).encrypt(buffer.getvalue()))
        decode(archive, key)
    return len(files)


def restore(target, archive, key):
    if os.name != 'nt':
        raise ValueError('WINDOWS_REQUIRED')
    manifest, files = decode(archive, key)
    target = Path(target).resolve()
    if target.exists():
        raise ValueError('RESTORE_REQUIRES_NEW_DATA_DIRECTORY')
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.gateway-transfer-', dir=target.parent))
    try:
        for name, data in files.items():
            if manifest['files'][name]['encoding'] == 'dpapi':
                data = SecretFile.protect(data)
                if SecretFile.protect(data, True) != files[name]:
                    raise ValueError('SECRET_REWRAP_FAILED')
            (staging / name).write_bytes(data)
        # No existing data is overwritten. The server must start only after restore.
        os.rename(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return len(files)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('export', 'verify', 'restore'))
    p.add_argument('--data-dir', type=Path)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--key-file', type=Path, required=True)
    a = p.parse_args()
    try:
        if a.action == 'verify':
            count = len(decode(a.archive, a.key_file)[1])
        else:
            if a.data_dir is None:
                p.error('--data-dir required')
            count = (export if a.action == 'export' else restore)(a.data_dir, a.archive, a.key_file)
        print(f'PASS: {a.action}; {count} verified files; no secret values displayed')
        return 0
    except Exception:
        print('TRANSFER_FAILED: check paths, key, archive integrity and stopped-server requirement', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
