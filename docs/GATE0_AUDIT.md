# Gate 0 source audit — 2026-10-17

## Actual repositories and initial state
Firmware: D:/esp32 selva/ESP32_LoRa_ESP32_Firmware. Not a Git repository; no branch/commit claim.
Gateway: D:/esp32 selva/ESP32_LoRa_Project, main tracking origin/main. Pre-existing modified files:
backend/account_settings.py, backend/node_manager.py, backend/server.py,
dashboard/static/js/firmware.js, tests/gateway_fixture.py, tests/test_accounts.py,
tests/test_gateway.py. Existing untracked Part 1 integration files and prior draft
CONFIG_CONTRACT.md were present. They were not reset, committed or pushed.
No AGENTS.md was found under D:/esp32 selva during this audit.

## Files inspected and architecture
Firmware: platformio.ini; config_schema.h/default_config.h/config_fields.h;
core/config_manager.cpp, network_service.cpp, main.cpp; communication/transport_manager.cpp,
wifi_manager.cpp, lora_transport.cpp; protocol/protocol.h and protocol.cpp;
web/local_web_server.h/.cpp; sensors/sensor_manager.cpp; docs/PART1_AUDIT.md,
PART1_REPORT.md; test/local_page.cjs. Existing private credential include was not dumped.

PlatformIO espressif32 7.0.1, esp32dev / ESP32-WROOM-32, Arduino 2.0.17 package
3.20017.241212, ArduinoJson7.4.3, PubSubClient2.8, DHT1.4.6/Unified Sensor1.1.15.
FreeRTOS network task handles HTTP/MQTT; main loop owns dispatch and WebServer.
DHT task is separate; sensor disabled by default. No Modbus/RS485 firmware integration found.
Wi-Fi AP+STA, DHCP/static IPv4, AP returns on disconnect and stops after stable STA.
Preferences device namespace config_v1 is the persisted JSON snapshot plus old per-key migration.
Existing local login is HTTP Basic; mutation header X-Config-Request:1. No HTTPS local server.
There is no pre-existing multi-page wizard, /mqtt, config import/export, BOOT-button reset,
last-known-good boot counter or firmware OTA handler. Existing typed reset/restart routes work.

Standard 4MB partition: NVS 0x5000, app0/app1 each 0x140000, spiffs0x160000,
coredump0x10000. No filesystem web asset mount was found; current pages are PROGMEM.
SDK config enables MQTT3.1.1 and SSL; bundled esp-mqtt headers exist, but switching from
PubSubClient requires a separate built/tested adapter. Current PubSubClient publish is QoS0.
The inspected SDK config does not enable NVS/flash encryption/secure boot. Actual chip
security eFuse state was not read. No encryption or hardware protection claim.

Gateway: backend/server.py; database.py, device_api.py, mqtt_adapter.py,
account_settings.py, auth_manager.py, config_manager.py, node_manager.py,
command_manager.py, chat_manager.py, communication_manager.py, packet_manager.py,
mesh_manager.py, routing_manager.py; requirements-part1.txt/requirements-mqtt.txt;
tests/gateway_fixture.py; docs/PART1_INTEGRATION.md and COMMAND_CHAT_IMPLEMENTATION.md.
Flask3.1.3/SocketIO5.6.1/Werkzeug3.1.8; optional Paho2.1.0.
SQLite data/gateway.db; accounts data/accounts.sqlite3; legacy auth.json and session.key.
Server import initializes/migrates tables; audit therefore used AST/text inspection,
not an import against live storage. Tests explicitly redirect DBs to disposable fixtures.
Account sessions use password hashes and session revision; administrator/creator plus
CSRF for mutating Gateway APIs. Device bridge uses enrolled Master bearer token hashes.
Legacy auth_manager has obsolete bootstrap behavior; current login uses account_settings.
Do not accidentally wire the legacy default-password helper back into authentication.
MQTT worker starts from environment in normal main path; callback currently performs DB
work. Planned service must move ingestion to a bounded worker and add shutdown ownership.

## Confirmed flow
NODE -> authenticated LAN HTTP -> MASTER -> HTTP device exchange / optional legacy MQTT
-> device_api -> existing SQLite telemetry/commands -> Socket.IO dashboard.
MASTER polls HTTP commands every2s, independent of optional MQTT data publishing.
E220 compile guard disabled; sendLoRa returns false. No hardware routing claim.
Gateway's legacy packet_manager uses numeric type IDs, maximum180 bytes, TTL<=10;
firmware/Part1 bridge uses string types, maximum4096 bytes, TTL<=15. Do not merge codecs.
Private Chat is database-only: its DELIVERED state means Gateway storage, not device receipt.

## Routes, settings and integration points
See GATE0_SETTINGS_INVENTORY.md: every one of77 DeviceConfig members is inventoried
(or mapped through seven legacy MQTT aliases), plus canonical profile settings, legacy
Gateway-only settings, sensor definitions and runtime metadata. The route appendix lists
114 static Gateway route decorators without starting the application.
Firmware existing routes: /, /api/status, /api/config GET/POST, /api/network/scan,
/api/commands, /api/diagnostics, /api/mesh, /api/system/restart,
/api/system/factory-reset, /api/v1/packets. New MQTT routes are documented in phase report.
Existing Gateway templates/static assets remain unchanged. Supplied logos found:
dashboard/static/img/logo-lockup.svg, logo-mark.svg, logo-icon.svg. No logo recreated.

## Resolutions and limitations
- Canonical 15-field broker profile; preserve old keys only at a migration boundary.
- Local client IDs/credentials/provider labels differ legitimately; exclude from shared digest.
- Role/device name/id map at device_api boundary, without renaming legacy DB columns.
- Firmware link timeout_ms and Gateway command timeout_seconds are different semantics;
  keep scoped separately. Legacy mesh settings are not applied radio configuration.
- No radio packet-size register semantics or exact module confirmed: reserve null/NONE,
  leave driver and packet formats untouched. Do not invent RF settings.
- New shared contract defines config topic bidirectionally for secret-free receipts/probes.
- Credentials cannot be distributed safely by existing local HTTP or ordinary MQTT config.
  Full provisioning and coordinated switch stop at this security boundary (prompt12.3).
- Existing login plaintext in firmware and bench overrides require a secure commissioning
  migration. No claim that the whole firmware meets the new security contract.
- Broker host is an operator-provided hint, not evidence of current active profile.
  No MQTT credentials, CA chain, second broker or ACL evidence has been supplied.

## Commands
Firmware: C:/Users/Admin/.platformio/penv/Scripts/pio.exe run.
Firmware static contract: same Python directory python.exe test/check_contract.py.
Web compression: python.exe test/build_web_assets.py; then --check.
UI: node test/local_page.cjs; node test/mqtt_page.cjs (Edge, mocked APIs).
Gateway baseline: .venv/Scripts/python.exe -m unittest discover -s tests -p test_*.py.
Do not flash until outstanding deployment/security decisions are understood.
