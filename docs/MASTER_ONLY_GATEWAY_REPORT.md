# Master-only implementation and test report — 25 October 2026

## Outcome and scope
The remaining connected Master COM8 (ESP32-10777D842178) was tested. The owner reports the Slave damaged; no further COM11 operations were performed in this phase. Shared firmware compilation does not establish Slave hardware, mesh or RF operation. No production-readiness claim is made.

## Implemented Gateway changes
- Replaced the login visuals with the requested offline red/white aerospace layout, existing SR logo and local font assets. Normal authentication, CSRF and session handling remain enabled. Remember me remembers only the username. Recovery explains the existing authorized recovery workflow; it does not reset an account.
- Added shared grouped navigation for Communication, Command Center, Diagnostics, System and Settings. Existing routes remain; Network and Diagnostics reuse existing facilities. Page titles identify the actual page. Branding is Selvarithik A&D without apostrophe S.
- Added a read-only operations overview with real device freshness, known network information and completed radio/mesh command observations. Stored offline observations are labelled historical. Configured parent relationships are not presented as verified RF links; unavailable RF loss/RSSI/SNR stay unknown.
- Removed only the Dashboard Recent Logs component. Log persistence and Diagnostics remain.
- Added bounded authenticated/admin/CSRF-protected active-profile MQTT diagnostics, with revision checks, unique temporary client IDs, verified TLS and canonical QoS 1 config PROBE. Results separately expose TLS, CONNACK, SUBACK, PUBACK and self-loopback. This never activates/stages a profile, confirms the full ACL or claims physical Master delivery.
- Improved Command Center short-viewport layout and response readability without modifying excluded shared Private Chat code. Added actual hardware MAC display and centralized duplicate-MAC enrollment checks, including legacy aliases and a SQLite immediate transaction.

## Files changed in this phase
Gateway backend: server.py integration; new workspace_views.py and mqtt_diagnostics.py; device_identity.py, device_api.py and node_manager.py identity/enrollment guards.
Frontend: login.html/login.js; base.html and navigation-links partial; index.html, nodes.html, sensors.html, logs.html, communication.html, mqtt.html, network.html and operations-overview partial; login-aerospace.css, workspace-organization.css, command-responses.css; operations-overview.js, mqtt-diagnostics.js and command_center.js.
Tests: test_workspace_views.py and test_mqtt_diagnostics.py. Documentation/evidence: MASTER_ONLY_* files and LOGIN_AEROSPACE_* screenshots.
No new firmware source edits or flash operations were required in this final Gateway/Master-only phase. Earlier firmware/link changes and builds are separately documented in HTTP_MESH and upload evidence. All pre-existing dirty user work is retained; no commit or push was performed.

## Evidence by category
| Category | Result | Evidence / limits |
|---|---|---|
| Local unit/API regression | 94 passed, zero failures/errors/skips | LOCAL_AUDIT_TEST_RESULTS.json; excludes cloud, Private Chat, OTA and physical tests |
| Workspace API/identity tests | 9 passed | Included in local suite; repeated after final source/newline correction |
| MQTT diagnostics unit/API tests | 7 passed | Mocked sockets/broker; authentication, role/CSRF/revision/input guards and safe failure states; not a real broker pass |
| JavaScript/static checks | Passed | Command Center state predicate, syntax checks, Python compilation and git diff --check |
| Contract/assets static checks | Passed | Firmware check_contract.py and build_web_assets.py --check; exact gzip-source match |
| Cross-project contract | Identical | Version 1.2.0/wire 1; SHA-256 below. Static declarations: 92 firmware settings, 15 profile fields, 11 topic entries; not new live cross-language serialization coverage |
| Real authenticated browser | Passed inspected flows | Normal Edge sign-in, live Dashboard readings, responsive login desktop/tablet/mobile and physical PING via Send; final source-only guard/metadata changes checked by API tests |
| Final browser reinspection | Unavailable | Browser extension returned Debugger unattached during final rebind. Existing inspected screenshots and real UI PING retained; no claim of a new post-restart visual pass |
| Physical Master commands over local IP | 9/9 completed, ACK ACCEPTED, no retries | MASTER_ONLY_COMMAND_EVIDENCE.json: PING, GET_STATUS, GET_NETWORK, GET_RADIO_STATUS, GET_MESH_STATUS, GET_ROUTE_INFO, GET_SENSOR_STATUS, GET_CAPABILITIES, GET_TELEMETRY |
| Additional physical browser PING | Completed, ACK ACCEPTED, no retries | MASTER_ONLY_UI_PING.json, CMD-104EF939796D; Gateway creation-to-response 1.288 s, reported execution duration 0.626 s. These are different timings |
| Real hosted TLS | Passed | TLS 1.3 chain and hostname verification, MASTER_ONLY_MQTT_PROBE.json; broker leaf expires February 26, 2027. This differs from CA expiry and does not invalidate the CA |
| Real MQTT authentication | Failed honestly | Active profile plus two prepared identities with existing stored credential refused authentication. Unique diagnostic client IDs may be subject to Client-ID authentication policy. Do not infer definitely wrong password |
| QoS 1 subscription/publication and ACL | Pending | No successful CONNACK, therefore no SUBACK/PUBACK/loopback; permanent worker remains ACL_CONFIRMATION_REQUIRED |
| Physical ESP32 cloud MQTT | Pending | Master remains in existing local-IP mode. No network/profile settings changed merely to test cloud |
| Slave, RF and physical mesh | Pending | Slave damaged; no current two-device evidence or RF transmission. Existing E220 radio configuration/profile remains unresolved |
| Long HTTP soak | Pending | Final short observation is recorded separately; historical failures are retained, not cleared |

## Physical telemetry and network
The Master remains MASTER on DHCP 192.168.1.108. Gateway dashboard is http://127.0.0.1:5000, device listener 192.168.1.104:5001. A final normal server.py restart loaded the completed changes without enabling a login bypass; existing sessions may need normal sign-in again.

Master DHT11 and INA219 report OK/valid. MQ135 reports WARMING_UP_RAW_ONLY/valid; values remain raw and uncalibrated, not gas concentration. The browser displayed actual live readings and SQLite contains fresh telemetry. MASTER_ONLY_FINAL_OBSERVATION.json records the exact short post-restart sample count, maximum observed timestamp gap and success/error/queue deltas. This short sample does not prove long-term elimination of intermittent HTTP errors or guarantee a fixed sampling interval.

## Preservation and firmware resources
MASTER_ONLY_PRESERVATION.json verifies accounts.sqlite3, mqtt-secrets.bin and session.key unchanged, both contract copies identical, and all baseline excluded Chat/OTA source/artifact files unchanged. The active MQTT document remains byte-identical at revision 6; no candidate was staged. Wi-Fi or sensor setting mutations were not issued.

Contract SHA-256: 4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde.

Earlier final Master build (not rebuilt or reflashed in this UI phase): program 1,298,249 bytes; image 1,304,960 bytes in 1,310,720-byte application partition (5,760 image bytes spare); reported RAM 74,732 bytes. Existing 4 MB layout, second OTA slot, filesystem and NVS retained. No huge_app selection, partition flash or erase. This narrow headroom is documented for future feature work, not hidden by changing partitions. OTA development is excluded.

Source rollback snapshot: ignored data/system-audit/pre-ui-reorganization-20261025.zip. It preserves the prior dirty source without copying secret stores/databases. Restore only selected reviewed source files if needed; do not reset user data or credentials.

## Remaining actions
1. Authorized EMQX administrator must verify account enablement, the protected stored credential and whether Client-ID-bound authentication permits diagnostic suffixes. Do not rotate credentials merely as a test. Prepared identities are separate from the unchanged active legacy profile.
2. Verify the exact canonical per-participant topic ACL matrix before enabling the permanent worker. The bounded diagnostic is not an ACL audit. No broker administrative permissions or rules were changed.
3. If a profile/secret change is authorized, use existing candidate staging and protected local provisioning; never put secrets in source, command arguments or screenshots. Existing Gateway helper: .venv\Scripts\python.exe backend\commission_mqtt.py --profile deployment\prepared\emqx-gateway.json --revision <actual-pending-revision> --pending-password. Enter the secret locally. This command was not run and no pending revision was invented.
4. After broker authentication/ACL approval, separately verify QoS 1 acknowledgements, physical Master MQTT, Gateway reception/database/dashboard and failure/recovery. Existing local-IP operation must not be silently disabled.
5. Replace/recover the damaged Slave before two-board sensor, link LED, mesh/LoRa delivery and RF ACK/response testing. Validate an applicable approved radio profile and hardware before transmission. No RF success is claimed from UART/software checks.
6. Run a longer Master HTTP reconnect/soak with error-stage capture. The historical failure counter remains visible even when the short final sample has zero new failures.

## Gate status
Gate 0: shared contract/static inventory preserved and passing. Gate 1: previous shared firmware build and current Master local-IP/sensor/command tests pass; cloud MQTT/Slave/RF hardware acceptance remains pending. Gate 2: this phase's Gateway UI/diagnostics/identity work implemented and automated checks pass; hosted authentication and permanent service ACL acceptance remain blocked. Gate 3: software and Master local-IP evidence recorded; all-gates-passed status is not justified.


## Subsequent EMQX-only screenshot-profile test
The owner supplied the actual MQTT Explorer setup after the initial report. EMQX_SCREENSHOT_EXACT_PROBE.json supersedes the prior authentication result for that exact tested profile: username ESP32_MASTER_01, Client ID CL_ID_ESP32GATEWAY, supplied CA file. TLS 1.3 chain/hostname verification, accepted CONNACK, canonical config-topic QoS 1 SUBACK, PUBACK and own PROBE loopback all passed. The existing matching MQTT Explorer credential was read in memory only; no credential was copied to project stores. Active profile/revision 6 and protected secret store remain unchanged. The test is a PC broker path, not physical ESP32 cloud MQTT or complete ACL acceptance. No HiveMQ contact was made. The active project credential matches the successful test credential: False. Therefore this result does not mean the unchanged active project profile is ready to connect. Use approved staged activation and secure local provisioning for an authorized deployment change.
