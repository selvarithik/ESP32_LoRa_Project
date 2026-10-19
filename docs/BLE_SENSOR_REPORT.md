> Historical sensor/BLE acceptance snapshot. Later TM1637/LED work and owner-confirmed MQ135 divider/enabling are recorded in CONNECTION_INDICATORS.md and INDICATOR_PHYSICAL_EVIDENCE.json.

# BLE removal and sensor implementation / acceptance — 2026-10-19

Completed active BLE removal, DHT11/INA219/MQ135 software support, app-only COM8 deployment and real local-IP sensor ingestion. Owner confirmed Current and Power are visible and updating in Live Telemetry. This is not a claim that every historical gate or hardware acceptance item has passed.

## Scope and gates

| Gate | Actual status |
| --- | --- |
| Gate 0 | Current source/ownership inspected; byte-identical contract 1.1.0 and wire schema 1; new sensor extension documented. Old reports are historical snapshots. |
| Gate 1 | Canonical TLS MQTT, profile staging/catalog/runtime controls and device controls exist; firmware builds and real Master local-IP/sensor/ACK/RESPONSE path passes. Hosted MQTT ACL acceptance and other physical role/radio/sleep tests remain pending. |
| Gate 2 | Gateway canonical persistence/service/config controls and live sensor normalization/UI implemented; 87 selected software tests pass. MQTT permanent worker remains ACL_CONFIRMATION_REQUIRED. Private Chat is frozen and excluded. |
| Gate 3 | Unit, C++/Python parity, mocked firmware UI, real temporary Gateway UI/simulator and one physical Master local-IP sensor path pass. Radio/second-board, MQ135 electrical acceptance, reference calibration, power-loss and soak acceptance remain pending. |

## Previously pending → implementation → evidence

| Item | Implementation | Evidence / boundary |
| --- | --- | --- |
| Remove scanner feature | Dedicated worker files removed; no scanner task, Bluetooth library include, UI/commands/routes/diagnostic fields or mock interface | Both-repo BLE_SCOPE_AUDIT.json; no active/unclassified source matches; ELF has no BLEDevice/Bluedroid/GATT/scan symbols |
| Keep saved configuration during removal | Old four scanner keys ignored only on NVS load; rejected by mutations; new writes omit them | Source inspection and actual preserved identity/config/MQTT revisions after migration; interruption of migration remains untested |
| New sensor drivers | One bounded worker owns DHT, Wire on 21/22 and ADC1 GPIO34; no additional sensor dependency | Actual DHT and INA219 register measurements; MQ135 raw-only software tests, hardware disabled |
| Current/power absent | Owner confirmed R100; USB saved 100 milliohms; I=shunt_mV/R_milliohms, P=load_bus_V*I | Real current/power saved in SQLite and owner-confirmed live UI; accuracy calibration explicitly false |
| Small readings rounded away | New INA219 current/power defaults use 5 decimal places; bus/shunt use 3 | Targeted persistence/precision test and owner-confirmed UI |
| Per-sensor schema | Independent packets preserve old DHT schema and existing Message envelope; typed/ranged validators on Master and Gateway | 53 executed C++/Python sensor vectors; invalid readings add no numeric values; 3 sensor persistence/precision tests |
| Live pages | Existing refresh/reconciliation and red header retained; additive sensor-health text; generic widgets receive new parameters | Real temporary Gateway UI at 375/1440; physical database; owner confirmation |
| Capacity | GCC LTO configured at compilation, archive and post-framework linking; default.csv retained | Final build 1,228,833/1,310,720 bytes = 93.8%; RAM 60,164/327,680 = 18.4% |
| Deployment | Protected 4 MB backup, actual device/layout/app0 guard, app-only 0x10000 writes, verified flash hashes | SENSOR_PHYSICAL_EVIDENCE.json; partition table/NVS/filesystem images never flashed |
| Commands | Real local PING/GET_TELEMETRY | Both persisted QUEUED → ACK_RECEIVED → COMPLETED; physical execution response, not merely queue acceptance |

## Tests: keep categories separate

- Unit/API: 87 passed, 0 failures/errors/skips (`tests/run_software_suite.py`), excluding Private Chat/OTA/physical methods. Three targeted sensor tests reran after precision changes and passed. Test data is isolated from owner database.
- Cross-language: 6 executed canonical MQTT serializer/digest vectors; 56 network/schedule/radio model vectors; 53 sensor validation vectors. These execute real portable C++ and Python logic on Windows, not on an ESP32.
- Mocked firmware UI: local page 1280/375 and MQTT page 360/1280 passed. Deterministic gzip roundtrip/check passes. Static contract inventory covers all 89 firmware fields, canonical 15-field profile and existing 11-topic registry.
- Integrated simulator/UI: actual isolated Flask/SQLite/HTTP and simulated Master/Nodes, ACK/results, saved profiles/staging and sensor cards passed. Simulation labels retained. No simulated values entered owner database.
- Local TLS broker integration: earlier software-phase run recorded 4 passing disposable-broker tests; not rerun by this sensor-only change. Do not describe them as hosted-broker evidence. That run had teardown socket/deprecation noise.
- Hosted broker: not exercised here; permanent worker truthfully reports ACL_CONFIRMATION_REQUIRED. No TLS/authentication/PUBACK/end-to-end MQTT claim from the local-IP success.
- Physical: COM8 ESP32-D0WDQ6 rev1.0, DHT11, INA219 at 0x40, signed LAN exchange, persisted six readings and two acknowledged/completed commands passed. Owner confirmed live Current/Power. MQ135 disconnected/disabled. Reference load accuracy, second Node, E220, sleep/wake, interruption and long soak remain pending.

## Contract and setting mapping

Both CONFIG_CONTRACT.md copies remain byte-identical with SHA-256 `fb5d28feea8849f3989bb4470e09f2599d4bdd5ba3cfd41c3ee76ba73ee1f52e`. Existing MQTT field names, wire schema, separators, topic registry and digest semantics are unchanged. See the contract inventory for every device setting and ownership classification; local-only hardware fields are not falsely presented as writable Gateway equivalents.

| Field | ESP32 page | Firmware | Gateway page | Gateway server | Verification |
| --- | --- | --- | --- | --- | --- |
| profile_name | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| provider | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| host | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| port | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| mqtt_version | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| tls | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| ca_cert | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| username | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| password | same canonical name | same canonical name | same canonical name | same canonical name | Write-only; no readback, protected commissioning |
| client_id | same canonical name | same canonical name | same canonical name | same canonical name | Local identity differs intentionally; concurrent clients stay distinct |
| keepalive_s | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| timeout_s | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| qos_default | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| topic_prefix | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |
| gateway_id | same canonical name | same canonical name | same canonical name | same canonical name | Software validation/source mapping; hosted per-field mutation pending |

| New sensor setting | ESP32 page | Firmware | Gateway page | Gateway server |
| --- | --- | --- | --- | --- |
| ina219_enabled | local setting | persisted, read on start | reported per-sensor health | accepts independent INA219 samples |
| ina219_address | local setting, 64..79 | Wire 0x40 default, pins21/22 fixed | hardware-owned; no duplicate writer | no conflated Gateway setting |
| ina219_shunt_milliohms | local setting, 0 unknown | owner R100=100 saved; runtime scale | current/power plus health | typed values/units, persisted, 5-place display |
| mq135_enabled | local setting with wiring warning | false; ADC not read | NOT CONFIGURED from device | invalid packets contain no readings |
| mq135_warmup_seconds | local raw-only timer | default86400; never proves calibration | health metadata | raw counts/pin mV only |

## Preserved configuration and memory

Device ESP32-10777D842178 remains MASTER. Device configuration revision changed intentionally 3→4 when the confirmed shunt resistance was saved. MQTT firmware revision53/shared1 and active fingerprint are unchanged; Gateway revision6 and existing server client ID remain unchanged. Private deployment passwords never entered tracked code, reports or command arguments. USB commissioning did not rotate account/network/broker secrets.

Final image is 1,235,536 bytes; image headroom75,184. Application capacity1,310,720; program headroom81,887. Second OTA slot and filesystem1,441,792 bytes remain. No huge_app deployment or OTA development. Initial raw build slightly exceeded default capacity; LTO fixed this without removing features. Two incomplete LTO configurations failed before post-framework link/archive configuration was corrected; final build passed.

Actual eFuse inspection reports flash encryption=false and secure boot=false. No claim of NVS encryption. Local backup files are protected using Windows user DPAPI and ignored by Git; keep the Windows account/recovery access for recovery. Backup/recovery images contain secrets and must never be exported as ordinary files.

## BLE references and remaining actions

Remaining project references are historical audit/inventory snapshots, exclusion notices, and inert old-key migration, classified in BLE_SCOPE_AUDIT.json. They are not active configuration or features. Arduino/ESP-IDF bundled SDK still contains chip Bluetooth/HAL support; the chip capability printed by esptool is not an application BLE feature. No third-party SDK was destructively edited. Both role paths and Gateway/dashboard/manifests were searched. Chat/OTA exclusion hashes match the pre-task baseline.

MQ135: keep AO disconnected until a suitable verified divider is fitted and measured. Then use the existing local sensor setting/USB configuration to enable it and restart; follow the module's specified conditioning and calibrate independently. No concentration/safety claim is implemented.

INA219: current and power now work with the owner-confirmed shunt. Compare against a known load/reference meter before claiming accuracy, and verify actual module electrical/thermal ratings. Readings are not proof of a particular load wiring or rated power.

MQTT: verify authorized EMQX ACLs through the established process before enabling the permanent worker. E220: provide exact module/region/pins/power and validate on two physical boards. Power loss/sleep/soak: schedule deliberate hardware tests separately. No unavailable physical result was replaced with a mock success.

## Access and commands

Gateway: http://127.0.0.1:5000/ . Current DHCP ESP32 page: http://192.168.1.100/ . Conditional recovery AP: http://192.168.100.1/ . Existing account credentials are unchanged; normal login is required after Gateway process restart.

Build: `& 'C:\Users\Admin\.platformio\penv\Scripts\platformio.exe' run`

Monitor: `& 'C:\Users\Admin\.platformio\penv\Scripts\platformio.exe' device monitor --port COM8 --baud 115200`

Current verified layout app-only upload (recheck device/layout/backup before reuse):
`& 'C:\Users\Admin\.platformio\penv\Scripts\python.exe' 'C:\Users\Admin\.platformio\packages\tool-esptoolpy\esptool.py' --chip esp32 --port COM8 --baud 460800 write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB 0x10000 .pio/build/esp32dev/firmware.bin`

Firmware changes: config/default/legacy-load handling, sensor manager and telemetry validator, scanner removal in interfaces/runtime/power/status/local page, gzip assets, compiler/link configuration. Gateway changes: device telemetry validation/registration and precision, supported communications and device controls/simulator removal, additive dashboard health, sensor tests/simulator. Documentation/tests: identical contract and protocol/hardware docs, parity/UI/physical tests, audit and acceptance evidence. See Git status/diff for the complete accumulated working-tree changes; unrelated user changes were preserved and no Git reset/clean was used.
