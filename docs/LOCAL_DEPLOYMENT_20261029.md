# Windows local deployment — 2026-10-29

The Gateway now uses Waitress, a single instance lock and the existing permanent MQTT worker. Dashboard styling, Wi-Fi, MQTT profiles and sensor settings are preserved. No ESP32 upload was performed.

## Start and stop

PowerShell:

```powershell
cd "D:\esp32 selva\ESP32_LoRa_Project"
.\deployment\Start-Gateway.ps1
```

Open http://127.0.0.1:5000 and use your existing Gateway account.

```powershell
.\deployment\Stop-Gateway.ps1
.\dist\Gateway\Gateway.exe status --data-dir .\data
```

The previous `.\.venv\Scripts\python.exe backend\server.py` command also starts the production launcher. Do not start both. Duplicate instances are rejected. The PowerShell supervisor retries crashes three times; a clean stop does not restart.

Current-user startup is installed and runs after Windows sign-in under the same Windows identity. Remove it using `deployment/Remove-Startup.ps1`. This is not a system service and does not run before sign-in. Reboot/sign-in operation remains untested.

## Windows executable

`dist/Gateway/Gateway.exe` is built and tested. Keep `_internal` beside it. The bundle is approximately 38.8 MiB and contains no user databases or credentials. The Start script uses the existing project data directory. Direct EXE launch without `--data-dir` uses `%LOCALAPPDATA%/SelvarithikGateway/data`, requiring an existing commissioned account and configuration; no default password is created.

Dependencies are in `requirements-deployment.txt` and `requirements-build.txt`. Stop the Gateway before rebuilding with the project virtual environment: `python -m PyInstaller --noconfirm deployment/Gateway.spec`. Build and dist are generated, ignored directories.

## Encrypted backups

A verified encrypted backup was created before deployment. Automatic backups run every 24 hours and retain seven verified archives. Each SQLite database is backed up consistently; separate databases are not one atomic transaction. The archive is encrypted with Windows DPAPI and requires the original Windows user/computer context. It is not a portable machine-loss backup. The in-memory archive limit is 256 MiB.

```powershell
.\dist\Gateway\Gateway.exe backup --data-dir .\data
.\dist\Gateway\Gateway.exe verify-backup --data-dir .\data --archive "FULL_ARCHIVE_PATH"
.\dist\Gateway\Gateway.exe restore --data-dir .\data --archive "FULL_ARCHIVE_PATH"
```

Restore previews by default. Stop the Gateway and verify the selected archive before intentionally adding `--apply`. Apply creates a pre-restore backup and an interrupted-restore recovery marker. No live database restore was performed.

Telemetry retention is optional and disabled. `maintenance --data-dir .\data --retention-days 90` previews eligible rows. Applying requires the Gateway stopped and creates a backup first. No actual telemetry history was deleted.

## Security and live updates

Deployment disables local test access, validates allowed hosts, protects cookies and adds security headers. Existing account authentication, login rate limits, command authorization and history remain in use. Windows Waitress uses Socket.IO HTTP polling; WebSocket upgrades are disabled in this mode. Real HTTP login and polling events were tested.

No internet endpoint was created. `deployment/proxy.example.json` prepares HTTPS reverse-proxy configuration with explicit allowed hosts and trusted proxy ranges. DNS, HTTPS and public deployment still need separate verification. Do not expose port 5000 directly.

## Verification

- Full Gateway unittest discovery: **187 passed**.
- Deployment regression suite rerun: **10 passed**.
- Source and frozen EXE smoke tests passed normal login, actual Socket.IO polling/events, encrypted backup verification, duplicate-instance rejection and clean stop using isolated fixture data.
- Actual local health: HTTP 200. Protected deployment status: HTTP 401 without login.
- Permanent MQTT worker: connected, alive, no queued messages at observation. This does not establish fresh physical sensor or PING delivery.
- Account database and credential files preserved byte-for-byte. MQTT configuration/revision preserved. Existing candidate remains PENDING.
- Separate saved LAN listener remains **FAILED / BIND_FAILED**. Dashboard works. Select a currently assigned laptop LAN address in Local IP settings when device LAN access is needed; the saved address was not silently changed.
- ESP32 hardware tests, new physical command round trips, Windows sign-in startup and multi-day stability remain pending.

Sanitized evidence: `LOCAL_DEPLOYMENT_20261029.json`. Rotating deployment log: `data/logs/gateway.log`.

## Recoverable cleanup

Removed 43 unreferenced generated documentation images (3,493,971 bytes) and 94 generated Python bytecode files across both repositories. Current approved previews, referenced assets, source code, databases, credentials and hardware backups were preserved. Bytecode may regenerate normally.

Images were encrypted and verified before removal. Recovery archive: `data/cleanup/generated-images-20261029T112327Z-4fc2a549.cleanup`. Exact manifest: `data/cleanup/latest.json`.

Preview recovery:

```powershell
.\.venv\Scripts\python.exe tools\cleanup_generated.py --root "D:\esp32 selva\ESP32_LoRa_Project" --root "D:\esp32 selva\ESP32_LoRa_ESP32_Firmware" --restore "data\cleanup\generated-images-20261029T112327Z-4fc2a549.cleanup"
```

Add `--apply` to restore archived images. Differing existing files are preserved. Recovery requires the same Windows DPAPI identity.
