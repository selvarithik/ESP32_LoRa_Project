# Operational commands and sensor-icon colors — 29 October 2026

Implemented in the shared ESP32 source and Python Gateway. No firmware was uploaded, no production Gateway restart was performed, and no live Wi-Fi, MQTT profile, sensor setting or database record was changed. Existing unrelated working-tree changes were preserved.

## Gateway UI and sensor colors
No Gateway HTML templates, layout, CSS, navigation, Command Center design or primary 21-command dropdown were changed in this task. Existing Sensor Management icon/color controls now support the ten future-use icons with matching defaults. Explicit custom colors are retained, including when an operator changes the icon after picking a custom color. Defaults are presentation settings, not sensor calibration or driver configuration.

| Icon | Default color |
|---|---|
| fan | #0D9488 |
| flame | #DC2626 |
| cloud-rain | #0284C7 |
| magnet | #7C3AED |
| door | #B45309 |
| weight | #475569 |
| ruler | #2563EB |
| volume | #BE185D |
| compass | #4F46E5 |
| beaker | #15803D |

## Fifteen implemented actions
Twelve operational extension commands are accepted in addition to the existing 21 primary commands. The other three actions reuse existing mechanisms. Extensions are exposed through the authenticated API and device capability response, not new Gateway buttons. Physical behavior is unverified until hardware is available.

| # | Action | Implementation and limits |
|---|---|---|
| 1 | SYNC_TIME | Typed UTC bounds, authenticated Gateway, envelope match, clock-step limit and coordinator guards; no NVS write |
| 2 | MQTT_CONNECT | Existing profile only; bounded wait for actual connection and subscriptions |
| 3 | MQTT_RECONNECT | Requires IP return path; requires observed client recycle and subscription readiness; old enabled state restored on failure |
| 4 | MQTT_DISCONNECT | Requires selected/working IP return path and 10..120 s automatic restoration; actual paused-state response; wrap-safe timer |
| 5 | MQTT_TEST | Normal STATUS via existing MQTT topic; only correlated Gateway PERSISTED receipt completes test; PUBACK alone insufficient |
| 6 | RADIO_INSPECT | Existing driver's cached public readback, explicitly labelled, or bounded asynchronous read-only probe; no register-write request or RF activation |
| 7 | DISCOVER_NODES | Existing HELLO over already commissioned/enabled E220 with registration open; only recent RADIO peers count; no responding Slave fails |
| 8 | I2C_SCAN | Explicit confirmation; addresses 8..119 on the already-initialized bus; same sensor task owns all Wire access; max 32 results |
| 9 | GET_COMMAND_RESULT | Same-source volatile cache only; absent/expired result stays UNKNOWN; no invented result after reboot |
| 10 | Cancel queued command | New authenticated queued-only endpoint; reject dispatched commands, never claim physical execution cancellation |
| 11 | RESET_DIAGNOSTIC_COUNTERS | Explicit NETWORK confirmation; reset only failure/duplicate counters, preserve queues/history/settings |
| 12 | SLEEP_NOW | Volatile one-shot timer/mode; final response means PREPARING_TO_SLEEP, not proven sleep entry; drain pending work, then timer wake; saved schedule unchanged |
| 13 | CANCEL_PENDING_SLEEP | Cancel one-shot preparation while awake; cannot remotely wake a sleeping device or delete saved schedules |
| 14 | IP/MQTT transport change | Existing password-confirmed prepare/apply/probe/confirm/cancel workflow retained, including actual new-path ACK/RESPONSE proof and rollback |
| 15 | Public E220 configuration | Revisioned radio-only CONFIG_UPDATE while radio is disabled and write permission false; saves PENDING_LOCAL_COMMISSIONING, not applied/readback verified; no remote RF enablement |

## API use
Read GET /api/device-controls with an authenticated administrator session. Existing commands and command_registry remain the 21 primary commands. operational_commands and operational_registry describe extensions.
Submit an extension through the existing POST /api/v1/commands with the existing session and CSRF token:

```json
{"node_id":"ESP32-10777D842178","command_type":"MQTT_TEST","payload":{},"timeout_seconds":120}
```

This is an example only; it was not sent to the live device. State starts QUEUED. The actual target ACK confirms acceptance; a separate actual RESPONSE determines the result. No manual fake ACK/RESPONSE endpoints were added. Gateway administrator passwords never travel to ESP32.

Queued-only cancellation: POST /api/v1/devices/<identity>/commands/<command_id>/cancel-queued, authenticated and CSRF-protected. It succeeds only before dispatch, returning device_execution_cancelled=false.

Public radio updates cannot include Wi-Fi or other configuration fields. They require expected_revision. Existing lora_enabled and lora_apply_settings remain local commissioning settings and cannot be activated by these commands. Numeric channel/power validity is not regional approval.

## Runtime and recovery
A single bounded asynchronous job is owned by NetworkService. Sensor I2C probes execute in the existing sensor worker. Duplicate IDs reuse the running job or cached result. Jobs protect their cache slot, apply timeouts and return honest errors. Result sizes are bounded by existing packet limits.
MQTT connection operations wait up to 90 seconds to accommodate existing reconnect backoff. Probe/inspection waits are 15 seconds; discovery uses its requested 5..30 second window. Runtime pause restoration uses monotonic time, including millis wrap. Pending operations/restoration block conflicting configuration, restart and sleep entry. Broker and IP/MQTT switching coordinators must be quiescent.
Operational caches, one-shot sleep and runtime MQTT pause are volatile. After reboot, saved profiles and the established startup policy remain authoritative; the Gateway must report interrupted operations unknown until an actual response/status resolves them. No new credential store or claim of encrypted device storage is introduced.

## Software verification
- 177 Gateway unittest tests passed, including 7 new operational API tests and sensor-color persistence/custom override checks. All use disposable fixture databases; no physical device results inferred.
- Actual production operational runtime executed in a native C++ harness with mocked network/hardware ports: authorization, time bounds, coordinator guards, reconnect proof, receipt requirement, timeout and restore, wrap-around restore, radio/I2C errors, RF-only discovery, cached results, counter reset and sleep-request semantics.
- Native C++ command admission and exact firmware/Python accepted-command parity passed; primary 21-command UI parity retained.
- Native shared sleep drain/register encoding and actual transport transaction tests passed: stale revisions, authorization, proof, commit, cancel, timeout, reboot, corrupt/storage failures.
- ESP32 mocked UI tests passed at desktop/mobile widths for local pages, all sidebar routes, MQTT staging and access/login. No sensor readings added back to ESP32 pages.
- Gateway browser test passed on an isolated fixture: normal sign-in, all ten icon default colors, custom color preservation, wizard save, actual source mapping, charts/ranges/statistics, widget removal/re-add, desktop/mobile and both themes; no JavaScript errors.
- Both contract copies are byte-identical version 1.4.0, schema 1. All 98 settings, 15 broker fields and 11 topics remain inventoried. Six executed C++/Python canonical serialization/digest vectors passed.
- Gzip source/asset consistency passed. PlatformIO esp32dev build and preserved 4 MB huge_app partition check passed. Final measured sizes and binary hash are in the accompanying JSON.

## Test limitations and exact remaining work
No current physical ESP32, Slave, E220 RF, I2C scan, timed sleep/wake, MQTT disconnect/reconnect or live EMQX round trip was tested in this task. Connect a verified board later, back up settings before a separately authorized upload, then test the safe read/diagnostic operations first. Radio transmission still requires approved regional settings, verified antennas/supply/wiring and a working peer. E220 remote staging deliberately stops before local activation/readback, so it must not be presented as a successful radio reconfiguration.
The Gateway worker was not restarted, and firmware was not uploaded. New actions become live only after an intentional Gateway restart and later authorized firmware upload. The unchanged Gateway UI does not yet add dedicated controls for extension commands; the authenticated API is available in the updated source.

## Files changed for this action extension
Firmware: src/command/operation_rules.h, command_catalog.h, command_rules.h; src/core/operational_runtime.inc, network_service.cpp, power_manager.cpp/.h, feature_core.h; src/sensors/sensor_manager.cpp/.h; src/communication/canonical_mqtt.cpp; native operational/admission/shared-control tests.
Gateway: backend/device_control_contract.py, device_controls.py, device_api.py, command_manager.py, device_simulator.py; backend/sensor_widgets.py; dashboard/static/js/sensor-widgets.js and sensor-management.js; operational/icon/color/UI fixture tests.
Documentation: both CONFIG_CONTRACT.md copies, cross-language expected hash, this report and JSON evidence. No dependency or partition changes.

Final build: application 1,359,577 / 3,145,728 bytes (43.2%); static RAM 75,988 / 327,680 bytes (23.2%); binary 1366288 bytes. Contract SHA-256 2ab672c11966684547bda89f0b2022bb461e6e34584b0834450a625a53d9d183.
