# Shared firmware, commands, sleep and transport switching

Date: 2026-10-28. Status: software implemented and built; physical acceptance pending.

No board upload, flash operation, serial provisioning, live command, Wi-Fi change,
active MQTT-profile change or sensor-setting change was performed. The permanent
Gateway process was not restarted. Previous physical TLS/DHT11 stability findings
are not declared fixed by this feature work.

## Implementation

- One shared `esp32dev` image uses the persisted MASTER/NODE role. Old master/slave
  PlatformIO target names are compatibility aliases with identical build flags.
  Saved role, identity and settings are retained. Use the new shared artifact,
  not old cached per-role binaries.
- Exactly 21 advertised commands match across C++, Python, the ESP32 form and
  Gateway Command Center. Legacy aliases remain accepted for compatibility;
  RADIO_TEST remains an unadvertised rejection boundary.
- SET_SLEEP_SCHEDULE accepts sleep_mode DEEP/LIGHT and lora_sleep_mode KEEP/DEEP.
  Existing enable/start/duration/days/UTC-offset settings are retained. Timer wake
  only. LIGHT suspends the network worker and Wi-Fi, retains RAM and uses bounded
  one-second timer chunks. DEEP restarts on wake. Pending work and either active
  configuration transaction prevent sleep/restart.
- E220 M1/M0 follows manual page 11: NORMAL=00, WOR_TX=01, WOR_RX=10,
  DEEP/configuration=11. The conflicting page-12 WOR_TX line is not followed.
- E220 public-register encoding, explicit local write permission, C0 response and
  C1 readback are implemented. UART/channel/power/air-rate/packet/WOR-cycle bounds
  are checked. Keys and authenticated radio packet formats stay unchanged.
  Without write permission, NORMAL mode adopts observed legacy packet/WOR values
  without rewriting them. Other existing configured radio fields must match.
- AUX is readiness, not recipient delivery. RSSI is reported only after an actual
  RSSI byte; SNR stays unavailable. WOR receivers temporarily enter normal mode
  to send replies and then restore WOR receive. Physical timing remains untested.
- Gateway administrator password confirms each transport action over HTTPS or
  loopback only. Existing account verifier, administrator session, CSRF, request
  bounds, revision and target checks apply. Password is removed before command
  creation and never forwarded over MQTT. Reauthentication is rate limited.
- CONFIG_UPDATE carries prepare/apply/confirm/cancel transport actions. Prepare
  preserves the active connection and does not start the trial deadline. Apply
  persists its journal before changing runtime selection, with a three-second
  response grace period. The old stored selection remains until commit.
- Confirm requires a transaction-correlated PING, ACCEPTED ACK and completed
  response over the selected actual ingress. The Gateway replaces claimed
  transport evidence with observed ingress. Old-path/forged/missing proof fails.
  Trial timeout or reboot restores the old selection. Lost outcomes stay unknown
  until a device response/status reconciles them; queuing is never commitment.
- ESP32 offline white sidebar, compact cards and grouped Network/Device/Radio/
  Nodes/System forms use the supplied HTML as visual guidance. MQTT keeps existing
  canonical staging. Foreign routes, credentials and RS485/SD features were not
  imported. The Gateway branding/header layout was not redesigned.
- Physical USB set_role requires an explicit role and exact device-ID confirmation.
  Network provisioning supports the shared image. These handlers were compiled,
  not invoked on a physical device.

## Test evidence

| Category | Result |
| --- | --- |
| Gateway unit/API/database/simulated integration | 169 tests passed; clean process exit |
| Final Command Center regression | 16 tests passed |
| Every primary command | All 21 passed through real Gateway API/database with simulated target ACK/RESPONSE; not physical evidence |
| Actual firmware transaction code on host | Passed with mock NVS/network: revision, authority, staging, proof, commit, cancel, timeout, reboot, corrupt/storage failure |
| Native E220/framing/routes | Passed settings, 500 COBS vectors, subpacket sizes, reassembly, duplicates, bounds, expiry and routes |
| Power/network/command checks | Passed admission, sleep-drain policy, scan guard, USB allowlist, TLS recovery policy and bounded HTTP reader |
| Cross-language digest | Six C++/Python canonical-byte and SHA-256 vectors passed |
| Contract | Byte-identical version 1.3.0; wire schema 1; 98 settings, 15 profile fields, 11 approved topic types |
| ESP32 mocked browser tests | Local page 1280/375 px; MQTT page 1280/360 px; validation, secrets, staging, offline assets and overflow checks passed |
| Assets/build | Gzip source/decompression check, pio run -e esp32dev and partition inspection passed |
| Physical board, live broker, RF and sleep current | Not run in this software-only phase |

Contract SHA-256:
6f463f36075885baca81aa1e7cefa44d23d0d11817d860c6e4a6324a59f51248

The Gateway MQTT document and protected-store fingerprints match the existing
preservation baseline. Physical Wi-Fi/sensor NVS was not accessed or written.

## Build and partition implications

The retained default-layout attempt failed: 1,318,669 program bytes exceeded the
1,310,720-byte slot. Existing LTO optimization was retained and features were not
removed. Source now selects installed huge_app.csv for the known 4 MB ESP32 target.

- Final linked program: 1,320,905 / 3,145,728 bytes, 42.0%.
- Binary: 1,327,616 bytes; 1,818,112 bytes of image headroom.
- Static RAM: 75,556 / 327,680 bytes, 23.1%.
- Partition artifact check: no overlap, 4 MB image header, final end 0x400000.
- Shared application artifact: .pio/build/esp32dev/firmware.bin.

| Partition | Previous | Source-selected |
| --- | --- | --- |
| NVS | offset 0x9000, size 0x5000 | unchanged |
| OTA metadata | offset 0xE000, size 0x2000 | unchanged |
| app0 | offset 0x10000, size 0x140000 | offset 0x10000, size 0x300000 |
| app1 | offset 0x150000, size 0x140000 | removed |
| SPIFFS | offset 0x290000, size 0x160000 | offset 0x310000, size 0xE0000 |
| Core dump | offset 0x3F0000, size 0x10000 | unchanged |

The changed layout was NOT deployed. Do not upload this application alone against
the old table: it exceeds the old slot and can overlap the old app1 region.

Before separately approved physical migration, verify board identity, flash size
and boot selection; make private verified full-flash, NVS and filesystem backups;
keep them out of Git. Extract needed filesystem files and verify that they fit
the smaller filesystem before repacking. A previous 0x160000 filesystem image
cannot be copied raw into the new 0xE0000 region. Preserve account/profile/device
NVS, inspect OTA metadata if it selects app1, and retain the original complete
image for recovery. Physical deployment remains with the owner. Future OTA needs
a new partition strategy; no OTA functionality was developed.

## Remaining hardware acceptance

1. Actual light/deep timer wake, Wi-Fi recovery, indicators and watchdog behavior;
   measure current before claiming power savings.
2. E220 public-register readback, AUX timing, WOR reply turnaround and matching
   peers with approved regional parameters, antennas and stable supply. Module
   capability does not establish regional RF approval.
3. Real Master/Slave discovery, routing, retries, duplicates and sensor delivery.
   The damaged/unavailable Slave prevents a current pair test.
4. After planned partition migration, physical IP/MQTT switching, new-path proof,
   timeout, power interruption and rollback. Mock NVS does not prove physical
   power-loss behavior. Local-IP credentials must already be provisioned.
5. Repeat EMQX stability and diagnose existing DHT11 no-response and telemetry gaps.
6. Restart the Gateway deliberately when ready to activate this backend. No GitHub
   push or permanent-worker restart was performed in this task.

Sleep reference: https://docs.espressif.com/projects/esp-idf/en/v4.4.2/esp32/api-reference/system/sleep_modes.html
Radio reference: supplied E220-900T22D manual, pages 11-16.

## Main files changed

Firmware: platformio.ini; config/schema/field/role headers; command catalog and
admission; transport_trial core/runtime; transport, MQTT, Wi-Fi and E220 drivers;
PowerManager, NetworkService, commissioning, diagnostics and main; ESP32 web pages
and generated gzip assets. Native admission, E220, sleep/transaction, parity and
responsive-page tests were added or updated.

Gateway: backend/transport_switch.py, command_manager.py, device_api.py,
device_control_contract.py, device_controls.py and device_simulator.py;
device_controls.html, command_center.html and device-controls.js; isolated fixture
cleanup and command/transport/contract regression tests. Contract and report copies
are maintained in both repositories.
