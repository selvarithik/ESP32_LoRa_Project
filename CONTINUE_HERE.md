# Continue on the Coimbatore Windows laptop

Prepared 1 November 2026. This is a development handoff, not a claim that all hardware tests passed.

## Take these files
- ESP32_LoRa_ESP32_Firmware-source.zip and ESP32_LoRa_Project-source.zip: complete committed source, tests, dependencies and documentation. Git clones are equivalent.
- Page-Sources.zip: all ESP32 pages and Gateway templates, shared CSS/JS/fonts/logos, plus separated inline CSS/JS reference blocks. These reference exports do not replace production sources.
- Gateway-Windows.zip: the currently running Windows executable and its supporting _internal folder. Optional; source development still requires Python.
- Gateway-private.sgwportable: encrypted Gateway databases, account hashes, configuration, protected MQTT credentials and local-link token, captured with the Gateway stopped. Contains private data. Never put it on GitHub.
- SEPARATELY: gateway-transfer.key from the private key folder identified in the delivery note. Possession of both key and archive permits decryption. Do not send either through chat or commit them.
- Both ESP32 boards with their saved NVS settings, sensors, E220 modules/antennas, data USB cables and spare jumper wires. Firmware/NVS stays on the boards without this laptop.

Do not copy .venv, .pio or build caches. Windows account-bound .sgwb backups and original DPAPI .bin files alone are not portable. Historical firmware flash backups also remain bound to this Windows account; do not rely on them as portable recovery copies. No new flash backup or upload was performed for this handoff.

## Set up development
Keep both repositories beside one another, for example C:\IoT\ESP32_LoRa_Project and C:\IoT\ESP32_LoRa_ESP32_Firmware. The exact drive does not matter. Install Git, Python (this laptop uses 3.14.3), Node.js, and PlatformIO using their official installers/documentation. Use the versions pinned by the repositories; do not upgrade dependencies while diagnosing a hardware problem. Install the USB-to-serial driver appropriate to each actual board.

PowerShell, inside ESP32_LoRa_Project:
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-deployment.txt
```
If that Python version is unavailable, validate dependency compatibility and all tests with the chosen version before using the production database.

## Restore private Gateway data BEFORE first server start
Copy the encrypted archive and separate key to private locations on the new laptop. The target data directory MUST NOT exist; the tool refuses to overwrite any directory. If the app has already created data, stop it and choose a new data-directory name instead of deleting existing data.

```powershell
.\.venv\Scripts\python.exe tools\portable_transfer.py verify --archive C:\Transfer\Gateway-private.sgwportable --key-file C:\Private\gateway-transfer.key
.\.venv\Scripts\python.exe tools\portable_transfer.py restore --data-dir .\data --archive C:\Transfer\Gateway-private.sgwportable --key-file C:\Private\gateway-transfer.key
.\.venv\Scripts\python.exe tools\gateway.py serve --data-dir .\data --config deployment\local.example.json --no-browser
```
Open http://127.0.0.1:5000 and sign in with the EXISTING Gateway account. No passwords are reset. Stop from another PowerShell window with:
```powershell
.\.venv\Scripts\python.exe tools\gateway.py stop --data-dir .\data
```
The transfer rewraps .bin secrets under the new Windows account using DPAPI; the archive is encrypted with a separate random Fernet key. Keep the encrypted archive/key backed up separately. Another Windows-machine restore is still pending until performed there.

Optional executable: extract Gateway-Windows.zip beside backend/dashboard/deployment (the archive includes dist/Gateway-command-ui-20261101 and launcher files). Start/stop with deployment/Start-Gateway.ps1 and deployment/Stop-Gateway.ps1 after restoring data. Do not run source and EXE servers simultaneously. Source-only archives safely fall back to the source launcher if no EXE exists.

## Network changes at the new location
COM numbers, laptop LAN IP and ESP32 DHCP addresses may change. Discover them; never assume COM8/COM11 or previous IPs are still correct. The saved router network may be unavailable in Coimbatore. Use existing physical USB commissioning to provision a new network only when explicitly requested. Do not edit MQTT credentials merely because the local network changes.
The current saved Gateway local-IP listener has BIND_FAILED: it refers to an old laptop address. Use Local IP Communication to explicitly select the new laptop's actual LAN address and an available port, then update the device's Gateway endpoint through the authorized flow if local IP is required. Keep dashboard binding on loopback unless LAN access is intentionally configured. Windows firewall permissions may be needed for the separate LAN listener. EMQX-only operation does not require public web hosting.
Do not run the old and new Gateway workers concurrently with the same client ID. Shut down this laptop's Gateway before starting the replacement. Keep the canonical contract, verified TLS and approved topic ACLs unchanged.

## Hardware identity and current state
| Board | Device ID | Last port | Role | E220 UART | Flash layout |
|---|---|---|---|---|---|
| Master | ESP32-10777D842178 | COM8 | MASTER | RX32 / TX33 | 4 MB huge_app, app at 0x10000, 3 MB; no second OTA slot |
| Slave | ESP32-842F2AE81F84 | COM11 | NODE | RX16 / TX17 | Legacy app at 0x100000, 1.5 MB, second slot retained |

One shared firmware codebase; persisted role selects behavior. E220 TXD connects to ESP32 RX, and E220 RXD to ESP32 TX. Both use M0=25, M1=26, AUX=27 and common ground. E220 supply from board 5 V; antenna fitted before any transmission. Do not run a normal PlatformIO full upload on the Slave: its preserved legacy partition offsets differ from the current huge_app build table. Use identity-confirmed application-only backup/upload tooling and inspect the actual layout first. Never erase NVS or flash a new partition table simply to fix a connection.
Sensors: DHT11 DATA4/3.3 V; INA219 SDA21/SCL22/3.3 V, current calibration only for a verified shunt; MQ135 supply5 V, AO through a verified 10k/10k divider into GPIO34. MQ135 data is raw, not calibrated ppm/AQI. Do not enable or recalibrate a saved sensor automatically. Master display CLK18/DIO19, onboard LED typicallyGPIO2.

## Evidence and pending work
- Physical Master EMQX telemetry and separate command ACK/execution responses were observed. PING, GET_NETWORK and GET_STATUS completed in the prior real tests; see Gateway docs/NETWORK_AND_COMMAND_UI_20261101.md and private acceptance results on the original laptop.
- Command Center readable cards, typed command-dependent forms, sleep timing, expand view and Logs navigation have software tests. Simulated browser tests are not physical Slave verification.
- Master E220 settings read still fails (no valid response on GPIO32/33); Slave read worked. LoRa RF delivery/mesh is NOT verified. Check wiring, module voltage/logic waveforms and region-approved configuration before RF transmission. Current recorded channel18=868.125 MHz must not be assumed lawful for India.
- Slave Wi-Fi/local-link commissioning remains unavailable; current saved settings intentionally preserved. A paired physical Slave test is pending.
- DHT11/INA219 read errors require physical diagnosis. Do not display fabricated sensor values. MQ135 calibration needs a known reference/RL/baseline; internet reference numbers cannot calibrate this unit.
- A prior temporary IP-backup observation saw a PANIC/reset and an intermittent receipt validation error; long stability/root-cause verification remains pending.
- No Ethernet hardware is connected. No BLE, Private Chat or OTA development is requested.
- Contract copies are version1.4.1, wire1, SHA-256 cdd19216fb270c93b3347aa894f0c90d7a40a1040d73da5c4d23da403a6aada5.

## Verify before continuing
Firmware: python test/check_contract.py; python test/build_web_assets.py --check; node test/local_page.cjs; node test/mqtt_page.cjs; node test/access_page.cjs; pio run. Build only; no automatic upload.
Gateway: .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py". For browser tests, run npm install --ignore-scripts and npx playwright install chromium in each repository first. Playwright is a development-only dependency; existing Windows UI tests use Microsoft Edge where specified. Historical preview/manual scripts may still contain old machine paths; they are not application startup requirements.
Start with this file, CONFIG_CONTRACT.md in both repositories, docs/GATE0_SETTINGS_INVENTORY.md, docs/GATE0_AUDIT.md, the latest dated implementation reports, platformio.ini, and the actual Git status. Inspect current source before editing. Never send secrets/screenshots of passwords to the next assistant.

## Handoff verification (1 November 2026)
Gateway unittest discovery: 195 passed, including 3 portable-transfer tests. Real encrypted archive: 10 files verified through isolated restore on this Windows account; different-machine restore pending. ESP32 contract/gzip/page checks, config-storage host checks and 8 flash-layout tests passed. Firmware build after gzip regeneration: 1,374,557 / 3,145,728 bytes (43.7%); RAM 76,140 / 327,680 bytes (23.2%). No firmware upload or saved device-setting change was performed for this transfer.

## Gateway design update, 2 November 2026
The approved updated red/black design is now implemented on the Gateway only. See docs/RED_GATEWAY_DESIGN_20261102.md. The active Windows release is dist/Gateway-red-ui-20261102. All navigation routes and live-data handlers are retained. ESP32 source and saved Wi-Fi/MQTT/sensor settings were not changed. The original encrypted private transfer archive remains a snapshot from 1 November; the newer UI is in source and the refreshed Windows bundle.
