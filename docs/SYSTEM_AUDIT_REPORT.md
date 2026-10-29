# Local system audit — 2026-10-25

## A. Inspection and scope

The existing Command Center is the command/response implementation. The path is
authenticated and CSRF-protected Gateway API, durable command queue, signed local
IP exchange, Master command handler, and separate ACK and execution RESPONSE.
An ACCEPTED ACK is not execution success. The physical Slave/LoRa path is not
verified by the local-IP or simulator results below.

The initial findings are in SYSTEM_AUDIT_FINDINGS.md. Gateway
AUDIT_CONTROL_INVENTORY.json inventories 194 template controls with script/API
candidates; these are static inspection results, not 194 successful live tests.
Existing user changes were retained. MQTT connection tests/configuration changes,
Private Chat, OTA development, account resets and destructive flash operations
were excluded.

## B. Changes

* Restored the local device listener on the laptop's current Wi-Fi address
  192.168.1.105:5001, replacing the stale .108 address. Updated only the Master's
  local server address to match. Dashboard access remains 127.0.0.1:5000.
* Added an explicit, default-disabled loopback test-session path using an existing
  eligible administrator account without changing its password/database. It
  requires a local Host/Origin, POST JSON and a custom header. Bootstrap expires
  after one hour; ordinary revocable session and idle expiry still apply.
  tools/run_local_audit.py starts the existing local services without starting
  MQTT. Omit --local-test-session to disable the temporary login helper.
* Corrected Command Center outcome labels, source/target metadata, timeout bounds,
  configured-heartbeat online detection, misleading static radio wording, and
  five controls whose values were ignored. Added scoped responsive response-card
  styling, retaining the existing header/navigation and shared Chat stylesheet.
* Added a bounded HTTP response-body reader. The pinned Arduino HTTPClient body
  loop can remain connected with no bytes available and no body deadline. All
  three production response-body reads now have absolute deadlines and size
  bounds; malformed/truncated responses fail rather than masquerading as success.
* Added an in-flight delivery gate and coalescing of unsent local Master sensor
  telemetry by sensor ID. Relayed messages and in-flight identities are preserved.
  Idle status polling yields to pending delivery work. This addresses observed
  pending-queue pressure; final physical verification is still required.
* Added identity-confirmed physical USB apply_build_role commissioning for explicit
  Master/Slave builds. It changes only the role and an invalid self-parent
  assignment. It does not change accounts, Wi-Fi, MQTT or sensor settings.

## C. Evidence categories

| Category | Result | Limits |
|---|---|---|
| Gateway selected unit/API suite | 79 passed, 0 failures/errors/skips | Excludes MQTT/cloud, Chat and OTA |
| Local disposable TCP/HTTP integration | 4 passed | Includes authentication, malformed/segmented input, deduplication and persistence; not RF |
| Command Center fixture UI | Passed | Software Master/Slave simulation, separate ACK/RESPONSE |
| Node-state UI | Passed in light/dark at desktop/mobile widths | Mocked snapshots, offline/recovery and reduced motion |
| Firmware static contract | Passed | Both contract copies identical; 92 settings, 15 profile fields, 11 topics |
| Portable production firmware logic | Passed | E220 framing/settings/reassembly, commands, sessions, feature rules, role confirmation, bounded body reads and delivery gate |
| Embedded assets | Passed | Existing generation/decompression checks |
| Real Master local-IP commands | PING, GET_TELEMETRY, GET_ROUTE_INFO, GET_SENSOR_STATUS returned ACK and RESPONSE | See MASTER_LOCAL_COMMAND_EVIDENCE.json in Gateway docs; no LoRa claim |
| Real Master sensors | INA219 and MQ135 values reached Gateway persistence/dashboard | MQ135 raw and uncalibrated; DHT11 READ_ERROR, old readings remain stale |
| Corrected Slave upload | Not performed | COM8 no serial data with no-reset; normal reset reports wrong boot mode 0x17 |
| Physical LoRa/mesh | Pending | No RF packets or register writes performed |
| MQTT/TLS/broker | Not tested in this audit | Existing settings preserved |

Canonical contract remains version 1.2.0 / wire schema 1, SHA-256
`4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde`.
Build sizes and exact unchanged partition offsets are recorded separately in
esp32_master_BUILD_EVIDENCE.json and esp32_slave_BUILD_EVIDENCE.json. No partition
change, huge_app selection, filesystem write, flash erase or NVS reset was made.

The Master previously received the bounded-body fix as an application-only write
at 0x10000 with successful esptool hash verification. The subsequent delivery-gate
change must not be described as physically tested merely because its build passes.

## D. Radio and unresolved hardware

Read-only probes of both E220-900T22D modules found address 0, UART 9600, channel
18 (868.125 MHz), air code 2, 22 dBm, 200-byte subpacket, transparent mode,
RSSI/LBT disabled. Firmware LoRa remains disabled. The current diagnostic reports
PROBE_COMPLETE_NO_RF through its error field even after a successful register
inspection; this is not an RF test.

India's published short-range-device rules describe the 865–868 MHz band with
power/bandwidth/duty conditions. The observed 868.125 MHz default needs an
appropriate verified regional configuration before transmission. Antenna type
alone does not establish compliant settings. Sources: [DoT rules](https://www.dot.gov.in/static/uploads/2025/07/84f33f09e137fa81930f44bcd5f2d238.pdf),
[PIB announcement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1797179&lang=2&reg=48),
[EBYTE manual](https://www.ebyte.com/Uploadfiles/Files/2021-7-6/202176188184448.pdf).

COM8 was identified as ESP32-CC9B23E2DEC4, 4 MB, running a Master profile.
Owner-confirmed BOOT/reset attempts did not reliably enter download mode. No
Slave backup or flash write succeeded. A successful build cannot correct the
physical board until upload and identity-confirmed role commissioning succeed.
Master is ESP32-10777D842178 on COM12, 4 MB. Its protected settings snapshot was
verified before its earlier application write.

## E. Remaining actions

1. Establish reliable COM8 download mode, verify its MAC/flash identity, save a
   protected NVS/partition snapshot, then write only the explicit Slave application.
   Preserve settings and apply the compiled NODE role using the exact device ID.
2. Deploy and observe the final delivery-gate build before claiming the brief
   telemetry interruption/queue issue is resolved. Perform a longer reconnect soak.
3. Resolve DHT11 READ_ERROR electrically; do not show historical values as live.
4. Verify regional radio settings, power supply and fitted antennas before enabling
   LoRa; then test discovery, ACK, RESPONSE and real Slave sensor forwarding.
5. Account/password, restart, sleep, radio/network mutation and other disruptive
   controls were not all exercised physically. The static control inventory and
   simulator coverage must not be reported as a full live-button acceptance pass.

This audit does not establish production readiness or complete physical-system
acceptance. No MQTT, radio, Slave upload or long-soak result is inferred from mocks.

Final artifact inspection: Master program 1,289,245 bytes, image 1,295,952 bytes
(14,768 bytes image headroom); Slave program 1,284,849 bytes, image 1,291,552 bytes
(19,168 bytes image headroom). Each application partition is 1,310,720 bytes.
Static RAM is 74,588 / 74,540 bytes respectively. Both artifacts pass bounds and
partition-overlap checks for 4 MB flash. Capacity is tight but fits; the second
application slot and 1,441,792-byte filesystem remain unchanged. These final
artifacts have not been uploaded or physically verified.
