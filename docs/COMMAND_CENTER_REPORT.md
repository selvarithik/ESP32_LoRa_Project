# Command Center and ESP32 login implementation report - 2026-10-23

Software is implemented in the existing two repositories and compiled for Master and
Slave. Hardware testing is deferred by the owner. Physical LoRa remains blocked by
unverified E220 hardware; this report does not claim the full physical mesh is complete.
No firmware upload, NVS reset, credential reset, factory reset or live broker probe occurred.

## Phase 1: firmware
- Reused NetworkService and the existing packet codec, transport queues, role handling,
  sensors, configuration manager and restart journal. Removed unused placeholder success
  responses from CommandExecutor; execution remains exclusively in NetworkService.
- Added production command catalog/admission core with native C++ tests and Gateway parity.
  Added capability/sensor/mesh/node/route reads, name update and documented aliases.
- Validate command shape, types, bounds and argument allowlist before acceptance. Admission
  ACK statuses ACCEPTED/REJECTED/BUSY/DUPLICATE are distinct from execution RESPONSE.
- Reserve result capacity before execution; queue overflow does not execute silently.
  Retried IDs reuse the bounded result cache. Execution response records elapsed time.
- Master stops retransmitting after application acceptance and waits for bounded expiry.
  Forwarding consumes TTL; stale/missing route, hop limit and queue failures are Master
  events, never fabricated Slave ACKs. Child nodes cannot administer their Master.
- Preserved enrolled legacy IDs and exposed actual hardware_mac. Python aliases normalize
  uppercase colon-separated station/base MAC to existing routing records without migration
  of credentials, historical rows or keys. Simulator IDs remain explicitly simulated.
- Separate esp32_master and esp32_slave builds select initial role; existing saved role wins.

## ESP32 login defect
The old browser request had no deadline and the initial session fetch could race submission.
The 100000-round PBKDF2 check also ran in the web/main task. The new browser disables submit
until CSRF/session readiness, uses bounded requests and polls a single session-bound worker.
Hash verification now runs outside the network loop. The main task owns session rotation;
credential-generation changes invalidate pending checks. An abandoned completed job is
reclaimed after 60 seconds. Password-hash strength and legacy login endpoint are preserved.
Wrong credentials report the saved-password requirement, rather than remaining Verifying.
admin/admin is only for the initial account. Existing saved password is not changed or
bypassed. Physical confirmation of latency, watchdog, heap and successful real login is pending.
The currently flashed device still uses its previous firmware until a later approved upload.

## Phase 2: Gateway
- Extended the existing command manager and SQLite history with durable command_delivery
  scheduling, not a second execution manager. Configurable ACK timeout, response timeout,
  expiry, bounded attempts and capacity are shared in the contract. State updates compare
  prior state and in-process mutations are serialized. Schedules survive process reload.
- Negative/busy ACKs fail honestly. Execution RESPONSE can complete without manufacturing
  an ACK. Missing execution response times out as unknown; late results are audited without
  turning TIMEOUT/CANCELLED into success. Unknown status values are rejected for active work.
- Both command submission routes use canonical validation for enrolled devices. Browser
  endpoints cannot forge enrolled device ACK/RESPONSE/state. Assigned authenticated device
  ingress remains required. Secret settings are disallowed as command arguments.
- Command Center preserves the existing header/navigation and layout. Corrected PING,
  interval, config, restart and scan payloads. Added documented read/action selections,
  argument JSON and separate ACK/expiry settings. Removed Wi-Fi credential inputs.
  History retains actual ACK, result, errors, timestamps and audit events. Stop dispatch
  is explicitly not remote cancellation. Registry metadata is at existing /api/device-controls.
- Existing canonical MQTT topics and TLS/ACL gate are unchanged. command carries commands;
  command_ack carries distinct ACK and RESPONSE packets. ACL_CONFIRMATION_REQUIRED stays.
- Simulator captures commands returned on all exchanges, including ACK/response exchanges,
  so concurrent commands are not discarded. It uses disposable databases and labeled peers.

## Verification categories
| Category | Result | What it proves |
|---|---|---|
| Gateway unit/API software suite | 103 passed, 0 failures/errors | Production validation, persistence, correlation, failure paths and simulator integration; excludes Chat/OTA/physical runners |
| New Command Center regressions | 16 tests included in total | Master-local and Slave PING, reads/writes, expiry, queue pressure, rejection, lost ACK/response, duplicate execution, concurrent targets, late response, route errors, aliases and persistence |
| Production C++ admission/registry | Passed | Executes actual admission core and exact Python/C++ name parity |
| Cross-language canonical digest | 6 vectors passed | Executed C++/Python canonical bytes and SHA256 |
| Network/schedule/radio core parity | 56 vectors passed | Production portable software core; no physical radio |
| Sensor validation parity | 53 vectors passed | Validation only, no generated physical readings |
| Real loopback TCP/local-IP | 4 passed | Actual framing/HMAC listener, fragmentation, rejection, timeout and restart; software peers |
| ESP32 browser mocks | Passed at mobile/desktop widths plus timeout case | Login states, first-use change, timeout recovery, local settings and MQTT page behavior; not real device authentication |
| Command Center browser | Passed | Real isolated Flask/SQLite -> simulated Slave -> ACK/RESPONSE -> database -> UI; invalid interval rejected |
| Master and Slave compilation | Both passed | Actual Xtensa/Arduino/PlatformIO build; not execution on boards |
| Physical ESP32, E220, sensors | Not run | Deferred by owner |
| Live MQTT broker | Not run | No external success claimed |
| Secret and exclusion checks | Passed | No tested local secret values in nonignored source/docs; protected Chat/OTA baseline byte-identical |

## Resources and partition layout
Board: esp32dev, ESP32-D0WDQ6 previously verified, 4 MB configured flash. Pinned
espressif32 7.0.1 / Arduino framework 3.20017.241212+sha.dcc1105b. No new dependencies.
Both targets: program 1,243,685 / 1,310,720 bytes (94.9%), static RAM 60,316 / 327,680
bytes (18.4%). Binary image 1,250,384 bytes; image headroom 60,336 bytes. These figures
use PlatformIO section accounting; runtime worker heap/stack must be checked physically.
Default partition layout preserved: NVS 0x9000/0x5000, otadata 0xe000/0x2000,
app0 0x10000/0x140000, app1 0x150000/0x140000, SPIFFS 0x290000/0x160000,
coredump 0x3f0000/0x10000. No overlaps; final boundary 4 MB. huge_app was unnecessary.
No partition table was flashed. No OTA functionality was developed.

## Remaining limitations and exact next actions
1. Physical E220 driver/mesh is unavailable: obtain exact SKU/frequency, pins/UART,
   supply, antenna and regional settings; then implement/verify physical framing,
   authenticated routing, fragmentation and ACK/RESPONSE. No multi-hop hardware claim.
2. Hardware login is pending: later upload the intended role image, use the saved password,
   test initial admin/admin only on an uncommissioned account. Recover forgotten credentials
   through the existing local USB helper, without factory-resetting settings.
3. Ordinary duplicate cache is volatile (32); only restart has a durable device marker.
   Power-loss exactly-once is not promised. Test NVS failure/power interruption physically.
4. MQTT command transport still needs approved EMQX ACL verification and bounded real
   broker/device acceptance tests. No ACL changes or credential rotation were attempted.
5. LoRa compact framing/fragment tests are simulated only. No physical RSSI/SNR invented.
6. Verify Wi-Fi reconnect/soak, simultaneous login+telemetry, result delivery after restart,
   queue saturation and response loss on actual Master/Slave boards when connected.
7. Production Gateway was not restarted as part of this software-only acceptance. Restart
   it when beginning hardware tests to load the updated backend and database migration.
8. Manual cancel stops dispatch; already accepted operations can still execute. Response
   after cancellation is audited; remote device cancellation is not implemented.

## Exact commands run
Firmware directory:
```powershell
& 'C:\Users\Admin\.platformio\penv\Scripts\platformio.exe' run -e esp32_master -e esp32_slave
python test/check_contract.py
python test/build_web_assets.py
python test/build_web_assets.py --check
python test/check_features.py
python test/check_sessions.py
python test/check_command_rules.py
node test/access_page.cjs
node test/access_timeout.cjs
node test/local_page.cjs
node test/mqtt_page.cjs
```
Python commands used the installed PlatformIO Python, except command rule parity used
the Gateway virtual environment (imports its validation module). Gateway directory:
```powershell
.\.venv\Scripts\python.exe -W ignore::ResourceWarning tests/run_software_suite.py
.\.venv\Scripts\python.exe -W ignore::ResourceWarning tests/local_ip_tcp.py
.\.venv\Scripts\python.exe tests/contract_parity.py
.\.venv\Scripts\python.exe tests/runtime_parity.py
.\.venv\Scripts\python.exe tests/sensor_parity.py
.\.venv\Scripts\python.exe tests/command_center_fixture.py
node tests/command_center_ui.cjs
```
The disposable browser fixture used 127.0.0.1:5084 and was stopped after testing.
No OTA, BLE or Private Chat functionality was implemented, extended or refactored.

Contract SHA256: `70f187bdfdbf97812f609fa71cebc0c03238232b5b1cdf7fb2551b0b4c2a6a45`. Both copies byte-identical, version 1.1.1, wire schema 1.

## Changed files

ESP32_LoRa_ESP32_Firmware:

- `COMMAND_PROTOCOL.md`
- `CONFIG_CONTRACT.md`
- `HARDWARE_REQUIREMENTS.md`
- `MQTT_TOPIC_CONTRACT.md`
- `TELEMETRY_SCHEMA.md`
- `platformio.ini`
- `src/command/command_executor.cpp`
- `src/config/default_config.h`
- `src/core/commissioning.cpp`
- `src/core/commissioning.h`
- `src/core/config_manager.cpp`
- `src/core/network_service.cpp`
- `src/web/access_page.h`
- `src/web/browser_auth.cpp`
- `src/web/local_web_server.cpp`
- `src/web/local_web_server.h`
- `src/web/web_assets_gzip.h`
- `test/access_page.cjs`
- `src/command/command_catalog.h`
- `src/command/command_rules.h`
- `test/access_timeout.cjs`
- `test/check_command_rules.py`
- `test/command_rules_host.cpp`

ESP32_LoRa_Project:

- `COMMAND_PROTOCOL.md`
- `CONFIG_CONTRACT.md`
- `HARDWARE_REQUIREMENTS.md`
- `MQTT_TOPIC_CONTRACT.md`
- `TELEMETRY_SCHEMA.md`
- `backend/command_manager.py`
- `backend/device_api.py`
- `backend/device_control_contract.py`
- `backend/device_controls.py`
- `backend/device_simulator.py`
- `backend/server.py`
- `dashboard/static/js/command_center.js`
- `dashboard/templates/command_center.html`
- `docs/SOFTWARE_TEST_RESULTS.json`
- `tests/contract_parity.py`
- `tests/test_device_controls.py`
- `backend/device_identity.py`
- `tests/command_center_fixture.py`
- `tests/command_center_ui.cjs`
- `tests/test_command_center.py`
