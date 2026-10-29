# Continuous EMQX Master telemetry — 26 October 2026

## Result
Physical Master ESP32-10777D842178 (COM8) now sends continuous MQTT sensor packets through the existing EMQX deployment into the normal running Gateway server.py worker, SQLite and authenticated Dashboard. The normal worker remains running in TELEMETRY_ONLY mode. No HiveMQ connection or Slave operation was performed.

The normal-worker observation lasted 170.65 seconds and persisted 102 fresh parameter values in 34 receive batches. The largest inter-batch receive gap was 10.470054 seconds. All six INA219/MQ135 parameters had 17 samples during the window. This is a short live acceptance run, not a multi-hour outage/soak qualification. EMQX_CONTINUOUS_STREAM_EVIDENCE.json records the exact counts and receive timestamps.

Before enabling the normal worker, the bounded real-broker check received 11 telemetry and 6 status packets, with zero handler errors, verified TLS, QoS 1 SUBACKs and 17 Gateway broker acknowledgements. The scoped config replies and actual database ingestion passed. This authorizes only telemetry/status/config, not a general wildcard ACL or command/chat operation. The permanent worker was enabled only after this scoped verification.

The normal authenticated Chrome Dashboard was inspected: Master ONLINE; MQTT connected / SCOPED_TELEMETRY_VERIFIED; bus voltage, shunt voltage, current, power, MQ135 ADC and MQ135 pin mV marked Live, with advancing receive timestamps and graphs. See EMQX_LIVE_DASHBOARD_EVIDENCE.json and EMQX_LIVE_SENSOR_VALUES.png. No login bypass or account reset was used.

## Changes and defects fixed
- Added physical USB mqtt_prepare bootstrap carrying the existing canonical SWITCH_PREPARE message, with revision/MASTER/account checks. Existing digest, deadline, peer proof, durable commit and rollback checks remain authoritative.
- Activated the real profiles through the existing staged/tested/coordinated commit flow. Both sides reached READY_TO_CONFIRM with real TLS/CONNACK/SUBACK/PUBACK/peer-probe/peer-ready evidence before COMMIT. Initial USB interruptions were rolled back, not marked successful. Final Gateway revision 20/shared revision 2 is committed.
- Fixed explicit-role Master startup leaving MQTT paused despite MQTT transport selection.
- Fixed retries changing envelope timestamps for the same packet ID, which caused DUPLICATE_CONFLICT. The original packet timestamp and expiration are now stable. The final bounded stream had zero such errors.
- Fixed queued MQTT sends being treated as HTTP failures. The internal accepted/pending result releases the bounded retry gate; only the application PERSISTED response completes ownership. No queued publish or PUBACK is labelled physical/application delivery.
- Added Gateway TELEMETRY_ONLY worker mode: only telemetry/status/config subscriptions and config replies, with pending command delivery and excluded Chat queues inactive.
- Added a non-secret local authorization proof bound to the exact active profile and protected credential reference. Normal server.py startup can reconnect this verified telemetry scope. A different profile/reference fails closed and requires new proof. No broker ACL or cloud account permissions were changed.

## Active deployment and preservation
EMQX host n1161c10.ala.eu-central-1.emqxsl.com, verified TLS port 8883, canonical prefix selvarithik/gateway, gateway GW001, QoS 1. Master client CL_ID_ESP32_MASTER_01 and Gateway client CL_ID_ESP32GATEWAY are distinct. The supplied working account/credential was provisioned locally at runtime; no password was added to source, examples, command arguments or this report. Gateway secrets remain in the existing Windows DPAPI store. ESP32 NVS encryption is not configured/verified; no encryption-at-rest claim is made for the device.

Only the transport selection local_ip_enabled changed to false, plus its configuration_revision metadata. Protected NVS comparisons show Wi-Fi fields unchanged: True; sensor/display/interval fields unchanged: True. See firmware docs/EMQX_WIFI_SENSOR_PRESERVATION.json. No SSID, Wi-Fi password, sensor enablement, pins, calibration or intervals were changed. Device identity, user accounts, old database data and application routes were preserved. MQTT profile changes were necessary and explicitly requested by the continuous MQTT task.

Contract copies remain byte-identical, version 1.2.0/wire 1, SHA-256 4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde. No packet format/topic/schema version change was made.

Application-only upload at 0x10000 passed flash hash verification. Final image 1305680 bytes, SHA-256 5840cfffeac2049c1a3419a9f35eb25b727a3adad57062533615c4144a659d6e; capacity 1,310,720 bytes, image headroom 5040 bytes. RAM 74,732/327,680 (22.8%). Existing partition table, NVS and OTA metadata read back unchanged during upload. Existing second application slot/filesystem retained; no huge_app, partition flash or full flash erase.

## Software checks
Master PlatformIO build passed. Native MQTT retry timestamp and delivery/retry/ACK gate tests passed. Contract and generated gzip checks passed. Gateway diagnostics tests: 7 passed. Telemetry isolation and proof-binding tests: 4 passed. Five selected existing worker persistence/auth/queue/shutdown/coordination tests passed, excluding Chat. Python compilation and git diff --check passed. No claim that the complete unrelated suite or Slave build/hardware was retested in this phase.

## Files
Firmware: src/core/commissioning.cpp; src/communication/transport_manager.cpp; src/communication/canonical_mqtt.cpp; new src/config/mqtt_retry_stamp.h; test/mqtt_retry_host.cpp and test/check_mqtt_retry.py.
Gateway: backend/mqtt_api.py; backend/mqtt_service.py; new backend/mqtt_runtime_policy.py; tests/test_mqtt_telemetry_mode.py. Evidence/report files are under docs. Local protected backups, commissioning runners and mqtt-telemetry-authorization.json remain under ignored data paths. No commit/push was requested or performed.

## Current limitations
DHT11 reports READ ERROR; temperature/humidity are old stored values marked Stale. No fresh DHT readings were counted or fabricated. Check its physical 3.3 V/GND/DATA-to-GPIO4 connection and module condition before a separate sensor test. Its saved settings were preserved.

MQ135 remains raw/uncalibrated and WARMING_UP_RAW_ONLY; no ppm, calibrated gas concentration or safety classification is claimed.

The saved local-IP listener address is no longer assigned to this laptop and the Dashboard shows its separate bind warning. MQTT telemetry does not use that listener; it was left unchanged. Ethernet, damaged Slave, LoRa/RF/mesh, command delivery over the new worker, Chat and OTA are outside this test.

USB was intermittent and temporarily disappeared; the owner reconnected COM8. Successful final MQTT observation is independent of USB monitoring. The clock was bootstrapped locally for verified TLS; autonomous cold-boot NTP recovery without USB and a long Wi-Fi/broker outage soak remain unverified. No production-readiness/all-gates-passed claim is made.

## Running
Open http://127.0.0.1:5000 and sign in normally; Dashboard filter is left on the tested Master. The normal server worker is left running. On later ordinary server.py startup, the local profile-bound telemetry authorization is rechecked; broad GATEWAY_MQTT_TRUST_ACL is not required. Stop the server before removing the local authorization file if this telemetry scope should be disabled. New MQTT profiles or credential references require their own verified scope.
