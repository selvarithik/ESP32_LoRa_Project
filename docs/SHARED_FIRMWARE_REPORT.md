# Shared Master/Slave firmware — Stage A, 2026-10-23

Stage A software implementation and builds are complete. Physical radio operation
and broker integration are NOT_TESTED. No upload, erase, serial session, board NVS
change, live MQTT connection, ACL change, new Gateway server or worker was performed.
Existing dirty changes from the Command Center/login task were preserved.

## Inspection and implementation

Inspected both existing repositories: PlatformIO/default partitions, main/identity,
configuration schema/defaults/persistence, commissioning, sensors, indicators,
protocol validators, transport/MQTT, NetworkService, commands/roles/mesh/diagnostics,
Gateway device API/control/command manager, MQTT contract/store/service, dashboard
Command Center, existing tests, contract and prior audit/reports. Reused Arduino,
ArduinoJson, existing FreeRTOS workers and shared Gateway handlers; no new dependency.

| Requirement | Implementation | Evidence / status |
| --- | --- | --- |
| One shared source | Explicit DEVICE_ROLE_MASTER / DEVICE_ROLE_SLAVE; legacy esp32dev retained | Both actual builds pass: BUILD_VERIFIED |
| Unique identity | Existing eFuse-derived ID retained; explicit foreign ID/role mismatch inhibits joining without rewriting NVS | Native role tests/builds; actual Slave MAC NOT_TESTED |
| Sensors | Shared DHT/MQ defaults; Master INA enabled initially with saved shunt; Slave INA always inhibited | 53 C++/Python validation vectors; new-image physical reads NOT_TESTED |
| Absent TM1637 | DisplayPresent=false inhibits construction/pin writes in both roles | Executed native profile assertions; physical pins NOT_TESTED |
| E220 UART | UART2 state machine, AUX/mode handling, public read-only settings probe, no register writes | Both compiled; settings parser native-tested; IMPLEMENTED_BUT_NOT_HARDWARE_VERIFIED |
| Radio framing | RV1 MessagePack/HMAC/COBS, bounded fragments/two assemblies/expiry | Native production framing/reassembly tests; on-device HMAC/UART/RF NOT_TESTED |
| Discovery/routes | Authenticated HELLO, admission/assignment, bounded12 routes, age/hop budget/loop and duplicate forwarding controls | Production core tests; physical direct/multi-hop NOT_TESTED |
| Reliability | Existing bounded command cache/retries, separate ACK/actual RESPONSE; radio UART submission not success | Command admission/parity and Gateway unit/API tests; lost RF ACK/reboot NOT_TESTED |
| Gateway compatibility | Existing15-field Message/approved topics unchanged; radio metadata stays inside adapter | Six canonical digest +56 network/schedule +53 sensor parity vectors; physical bridge NOT_TESTED |
| Cloud preparation | Four public EMQX/HiveMQ participant profiles, blank secrets, candidate CA metadata | Five new offline unit cases in108-test suite; not activated |
| Security/preservation | TLS unchanged; explicit cloud paused, Slave client inhibited, active document/protected stores unchanged | Release fingerprint/assertion checks; device flash encryption NOT_TESTED |

Protocol: CONFIG_CONTRACT.md1.2.0, wire schema1. Version change documents the new
radio adapter, effective role masks and paused startup without renaming fields or
changing the Gateway JSON schema. Both contract copies are byte-identical, SHA256:
`4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde`.
COMMAND_PROTOCOL.md specifies RV1 fields, sizes, byte order, authentication, retry
limits and the Gateway -> Master -> Slave -> actual response return flow.
MQTT_TOPIC_CONTRACT.md lists every approved topic's actual publisher/subscriber,
including preserved legacy subscriptions and unfinished reserved handlers.

## Actual build results

Command in firmware repository:

```powershell
& 'C:\Users\Admin\.platformio\penv\Scripts\platformio.exe' run -e esp32_master -e esp32_slave
```

| Artifact | Application program / capacity | Static RAM / capacity | Binary bytes | Binary headroom |
| --- | --- | --- | --- | --- |
| .pio/build/esp32_master/firmware.bin |1,288,621 /1,310,720 (98.31%)|74,548 /327,680 (22.75%)|1,295,328|15,392|
| .pio/build/esp32_slave/firmware.bin |1,284,665 /1,310,720 (98.01%)|74,492 /327,680 (22.73%)|1,291,376|19,344|

Both SUCCESS. Size evidence is from actual ELF sections and binary files, not a
plain text+data sum. Heap/stack use under real radio/login concurrency is unverified.
Headroom is small; future additions must be rebuilt/measured. No asset rewrite or
partition change was needed. Existing gzip generation/decompression check passes.

The generated tables are byte-identical (SHA256
148b959cbff1c38aa8e1d5c0ba9d612c54997b945e56a63f41223eef650653a1), preserve NVS,
filesystem and both0x140000 slots, and do not overlap or exceed4MB. huge_app was not
selected. Actual Slave flash capacity remains to be physically verified. Image
hashes and complete partition offsets are in SHARED_FIRMWARE_EVIDENCE.json.

## Tests actually run

| Category | Command / coverage | Result |
| --- | --- | --- |
| Gateway software unit/API | .venv/Scripts/python.exe tests/run_software_suite.py |108 run,0 failures,0 errors,0 skipped; excludes Chat/OTA/hardware |
| Production native radio core | python test/check_e220.py | Both compile roles pass;500 COBS lengths each,64/128/200 fragmentation up to3072 bytes, reorder/duplicates/bounds/expiry/settings/routes/role masks |
| Contract static inventory | python test/check_contract.py |92 settings,15 profile fields,11 topics pass |
| Cross-language digests | Gateway tests/contract_parity.py |6 executed C++/Python canonical bytes/SHA vectors pass |
| Cross-language runtime/sensors | Gateway tests/runtime_parity.py; tests/sensor_parity.py |56 network/schedule +53 sensor vectors pass; hardware mocks labelled |
| Native command/session/features | check_command_rules.py, check_sessions.py, check_features.py | Pass; registry equality, admission, session lifecycle, schedules and old simulated boundaries |
| Generated assets | python test/build_web_assets.py --check | All source pages equal decompressed generated gzip |
| Mocked firmware UI | node test/local_page.cjs; mqtt_page.cjs; access_page.cjs; access_timeout.cjs | Desktop/mobile pass; pending login expires and releases button |
| Release preservation | Gateway venv Python test/check_shared_release.py | Contract, artifacts, partitions, excluded files, active MQTT document/stores and stored-secret scan pass |
| Local broker integration | Not run in this stage | NOT_TESTED; no broker connection evidence claimed |
| EMQX/HiveMQ live | Explicitly deferred | NOT_APPROVED_NOT_RUN |
| Physical hardware | Explicitly deferred | NOT_TESTED; no fresh board/serial evidence |

Git diff --check passes in both repositories (generated header has Git newline
normalization notice only). No new Gateway runtime/database schema changes were
needed for this radio adapter. Unit tests use fixtures; owner data was not migrated.
No browser dashboard claim is inferred from mocked firmware pages.

## Files changed for this shared-firmware stage

Firmware additions: src/config/hardware_profile.h,
src/communication/e220_core.h, test/e220_core_host.cpp, test/check_e220.py,
test/check_shared_release.py, tools/radio_inspect.py.

Firmware edits: platformio.ini; src/config/default_config.h, config_schema.h;
src/communication/lora_transport.h/.cpp, transport_manager.cpp, canonical_mqtt.cpp;
src/main.cpp; src/core/network_service.cpp,
config_manager.cpp, commissioning.cpp, connection_indicators.cpp;
src/identity/device_identity.cpp; src/diagnostics/diagnostics_manager.cpp;
src/protocol/protocol.h; src/sensors/sensor_manager.cpp;
src/web/web_assets_gzip.h regenerated from existing pages.

Gateway additions: backend/cloud_profile_preparation.py,
tools/prepare_cloud_profiles.py, tests/test_cloud_preparation.py.
Gateway edits: tests/contract_parity.py expected version hash;
docs/SOFTWARE_TEST_RESULTS.json refreshed. Existing command/login/dashboard changes
listed in git status predate this stage and were retained, not replaced.

Both repositories: CONFIG_CONTRACT.md, COMMAND_PROTOCOL.md, HARDWARE_REQUIREMENTS.md,
MQTT_TOPIC_CONTRACT.md, TELEMETRY_SCHEMA.md; deployment/prepared/emqx-master.json,
emqx-gateway.json, hivemq-master.json, hivemq-gateway.json, preparation.json;
docs/CLOUD_PREPARATION.md, SHARED_FIRMWARE_REPORT.md, SHARED_FIRMWARE_EVIDENCE.json;
historical-status notices in docs/CONNECTION_INDICATORS.md and SOFTWARE_BASELINE.md.
Firmware README adds build/readiness links.

No Private Chat/OTA implementation or tests were changed; exclusion baseline hashes
match. BLE source/dashboard/manifests were searched: no active application feature
or dependency found. Remaining mentions are historical inventories, removal reports,
exclusion notices and inert legacy-key migration. Arduino bundles chip BT HAL code;
ELF contains zero-length NimBLE linker boundary anchors, not an active stack. SDK
files were not deleted. Historical SOFTWARE_BASELINE claims are superseded.

## Remaining work and next safe test

1. User authorizes Master-only upload, then verify actual COM8 identity, board/flash,
   wiring, supply, antenna and regional settings. Preserve data and deployed layout;
   no erase/NVS reset. Confirm boot, saved role/identity and sensor/INA calibration.
2. With RF disabled, approved read-only inspection can use tools/radio_inspect.py
   --port COM8 --read-only. It temporarily changes mode pins and restores levels;
   no settings are written. Reconcile observed public settings with saved configuration
   securely. Mesh credential and explicit RF enable are still required. No probe ran.
3. Before Slave upload, request explicit press-and-hold BOOT confirmation; verify
   COM10 chip/flash/divider first. Never batch-upload both targets. Check INA/display
   inhibition and distinct physical MAC after boot.
4. Verify direct discovery, heartbeat/offline, real sensor packets, addressed PING,
   correlated ACK and actual RESPONSE, loss/duplicate/expiry, UART busy, RSSI framing,
   reboot/power interruption, Wi-Fi outage, concurrent sensor/command load and soak.
   The whole UART/HMAC driver is only compile-verified; native tests cover its portable
   core, not radio timing or RF behavior. Radio reinitialization after a fault requires
   explicit inspection/re-enable rather than endless automatic register cycling.
5. Extra relay hardware must prove multi-hop; two boards cannot establish it. Shared
   mesh-key membership is not per-device key identity. Ordinary duplicate caches are
   volatile across reboot; exactly-once physical side effects are not guaranteed.
6. The existing legacy radio_frame/Python simulator is a different old software model,
   not a full RV1 simulator. Native RV1 tests and compiled driver evidence are separate.
7. Broker console access/ACL ordering and actual CA chain remain unverified. Follow
   CLOUD_PREPARATION.md only after separate approval; provision secrets locally, stage,
   test and confirm through the existing transaction. Never replace active settings
   just to test. No claim of end-to-end cloud telemetry or production readiness.
