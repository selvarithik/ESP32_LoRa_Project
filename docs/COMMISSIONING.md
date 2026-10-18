# Current commissioning guide — 2026-10-19

See [FINAL_ACCESS_REPORT.md](FINAL_ACCESS_REPORT.md) for full evidence and limitations. These instructions replace the older Basic-authentication workflow.

## Current state
- Gateway login: http://127.0.0.1:5000/login . Existing Gateway accounts are preserved and separate from ESP32/MQTT credentials.
- New ESP32 browser-session firmware is built, **not uploaded**. Existing device credentials/configuration were not rotated. Last verified DHCP address: 192.168.1.105; it may change.
- COM8 is listed, but the final open returned Windows error 31. Reconnect/check USB and close monitors before any owner-run upload.
- Existing secure-store MQTT authentication is currently rejected: Bad user name or password. TLS verification passes. This requires authorized broker/credential reconciliation; initial commissioning must not overwrite active profiles.
- Permanent worker remains ACL_CONFIRMATION_REQUIRED. A diagnostic client is not the permanent worker.

## Gateway recovery, only if needed
From the Gateway project, preview the selected existing-account operation:
```powershell
.venv\Scripts\python.exe backend/recover_account.py --user admin
```
The separate `--apply` flag deliberately writes a verified-backed-up credential reset for that one account and forces browser password replacement. It preserves other accounts, device enrollment, Gateway data and MQTT stores. It was not run against live accounts. `--bootstrap --apply` is only for an actually empty account store; no normal boot restores default credentials.

## Owner-run firmware deployment
```powershell
Set-Location 'D:\esp32 selva\ESP32_LoRa_ESP32_Firmware'
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' device list
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' run
# The next command writes firmware; run it yourself only when ready:
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' run --target upload --upload-port COM8
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' device monitor --port COM8 --baud 115200
```
Default partitions still fit. No Huge App, flash erase, filesystem format or NVS reset is needed. Upload normally writes bootloader/table/OTA metadata/application regions with the same offsets. OTA development is deferred; both existing slots are retained.

After uploading, use the actual DHCP address, `/login`, and `/account`. Existing NVS credential records remain valid. First-use/recovery credentials force browser password replacement. Password visibility controls avoid hidden terminal entry. HTTP does not encrypt credentials/cookies: keep access on a trusted LAN, without public tunnels.

If the local password is forgotten, this **owner-run credential-writing recovery** is available only in the new firmware:
```powershell
& 'C:\Users\Admin\.platformio\penv\Scripts\python.exe' tools/commission.py --port COM8 --operation recover-account --confirm-device-id ESP32-10777D842178
```
It replaces only the local owner credential/name, invalidates browser sessions, and requires password replacement through the browser. It was not executed here. It does not change Wi-Fi, broker, device identity or other NVS settings.

For acceptance using an existing clipboard password without changing it:
```powershell
& 'C:\Users\Admin\.platformio\penv\Scripts\python.exe' tools/device_acceptance.py --check-only
```
The helper distinguishes legacy Basic from new cookie/CSRF authentication. Without `--check-only`, the helper writes a generated replacement password; do not use that mode merely to inspect status. No credentials are printed or stored in reports.

## Broker provisioning and security
Use the existing staged-candidate workflow. Do not rerun initial MQTT commissioning over either active profile. Inspect current revisions/pending states; stage public settings on both MQTT pages and provision any pending password through the existing local console/USB helpers. Use exact matching non-secret profile files and the actual pending revision. Gateway helper supports `--pending-password`; firmware `tools/commission.py --operation mqtt` provisions only a matching pending profile when an active profile already exists.

Current authentication must be reconciled with authorized EMQX management before assuming the old control path or a coordinated switch works. Do not force revisions, bypass TLS validation or overwrite the active profile to obtain a green status.

An authorized operator must verify anonymous denial, per-client/principal topic directions and unauthorized-topic denial. Only after that and usable broker authentication, stop the existing Gateway console process and deliberately enable the normal worker:
```powershell
Set-Location 'D:\esp32 selva\ESP32_LoRa_Project'
$env:GATEWAY_MQTT_TRUST_ACL='1'
.venv\Scripts\python.exe backend/server.py
```
The flag alone does not verify ACLs or fix a rejected password. No hosted ACL, broker password or stored active credential was changed here.

MQTT credentials remain write-only, absent from tracked examples. Gateway secrets use the existing current-user DPAPI file; do not export it. ESP32 NVS is not encrypted at rest according to prior read-only security inspection. Do not dump NVS/flash, password verifiers or private backups into logs/reports.

Physical NVS password persistence/reboot, browser handlers, memory/network soak, permanent-worker telemetry-to-dashboard and E220 module/readback/RF acceptance remain pending as specified in the final report. E220 is still unavailable in normal firmware; native UART doubles do not prove radio delivery.
