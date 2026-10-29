# Permanent EMQX Master command acceptance - 2026-10-27

Physical test: 2026-10-27T21:36:15.192906 to 2026-10-27T21:38:33.412315 (local time). Master COM8 / ESP32-10777D842178. Normal permanent Gateway worker; no separate broker test client. Browser control failed to initialize, so authenticated Dashboard click/display acceptance remains pending.

## Changes and evidence

The permanent worker supports the verified telemetry/command scope, bounded dispatch, correlated ACK and execution RESPONSE ingestion, durable command history, and stable retry envelopes. Private Chat remains excluded. The Master persistence adapter sets the required next-hop field. Command caches expire beyond the existing message-age window, refuse new work under low memory, and release full reply bodies only after the Gateway confirms durable persistence. Command identities remain cached for deduplication. Earlier failed sweep evidence is retained separately.

Latest upload: application only at 0x10000; flash hash verified; protected NVS/partition/OTA bytes unchanged. Image 1,307,856 bytes. Linked program 1,301,149 / 1,310,720 bytes (99.3%); RAM 75,244 / 327,680 bytes (23.0%). Original partition table retained.

Gateway active MQTT state unchanged: True. No Wi-Fi, broker-profile or sensor settings mutations sent. TLS verified before: VERIFIED; after: VERIFIED. Master reconnect counter before/after: 0 / 0. Final runtime free internal 8-bit heap: 44440; largest block: 18420.

## Command results

| Command | ACK | Gateway result | Execution response |
|---|---|---|---|
| PING | ACCEPTED | COMPLETED | received |
| GET_STATUS | ACCEPTED | COMPLETED | received |
| STATUS | ACCEPTED | COMPLETED | received |
| DIAGNOSTICS | ACCEPTED | COMPLETED | received |
| GET_CAPABILITIES | ACCEPTED | COMPLETED | received |
| GET_SENSOR_STATUS | ACCEPTED | COMPLETED | received |
| GET_MESH_STATUS | ACCEPTED | COMPLETED | received |
| GET_NODE_STATUS | ACCEPTED | COMPLETED | received |
| GET_ROUTE_INFO | ACCEPTED | COMPLETED | received |
| GET_TELEMETRY | ACCEPTED | COMPLETED | received |
| GET_CONFIG | ACCEPTED | COMPLETED | received |
| GET_CONFIGURATION | ACCEPTED | COMPLETED | received |
| GET_NETWORK | ACCEPTED | COMPLETED | received |
| GET_RADIO_STATUS | ACCEPTED | COMPLETED | received |
| GET_POWER_STATUS | ACCEPTED | COMPLETED | received |
| WIFI_SCAN | ACCEPTED | FAILED | received |
| RADIO_TEST | ACCEPTED | FAILED | received |
| SET_CONFIGURATION | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| CONFIG_UPDATE | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| SET_DEVICE_NAME | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| SET_SLEEP_SCHEDULE | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| SET_TELEMETRY_INTERVAL | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| SET_HEARTBEAT_INTERVAL | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| RESTART | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| REBOOT | pending | not run: preserves settings/connection or avoids restart | not tested physically |
| WIFI_RECONNECT | pending | not run: preserves settings/connection or avoids restart | not tested physically |

Post-sweep PING: COMPLETED / ACCEPTED; execution response at 2026-10-27T21:38:32.364982.

WIFI_SCAN is expected to return FAILED / WIFI_SCAN_BUSY_MQTT_ACTIVE without starting a disruptive all-channel scan. RADIO_TEST is expected to return FAILED / USE_ADDRESSED_PING_DURING_APPROVED_HARDWARE_TEST. This is an honest rejection, not an RF communication pass. No Slave/RF test was performed.

## Telemetry continuity

| Parameter | New records | Source | Largest observed gap (s) | Last sample |
|---|---:|---|---:|---|
| bus_voltage | 13 | mqtt | 11.254 | 2026-10-27T21:38:25.100891 |
| current | 13 | mqtt | 11.254 | 2026-10-27T21:38:25.100891 |
| mq135_adc_raw | 13 | mqtt | 12.032 | 2026-10-27T21:38:27.821413 |
| mq135_pin_mv | 13 | mqtt | 12.032 | 2026-10-27T21:38:27.821413 |
| power | 13 | mqtt | 11.254 | 2026-10-27T21:38:25.100891 |
| shunt_voltage | 13 | mqtt | 11.254 | 2026-10-27T21:38:25.100891 |

DHT11 remains a physical READ_ERROR; stale temperature/humidity are not counted as live. MQ135 values remain raw and uncalibrated. This bounded observation is not a long-duration reliability qualification.

## Software checks

38 selected Gateway tests passed: command scope (5), telemetry isolation (4), saved profiles (6), MQTT diagnostics/authentication (7), Command Center (16). Production C++ command-gate, persistence-receipt parser, cache-release and scan-stream guard regressions passed. These software tests are distinct from the real hardware results above. Firmware build and git diff --check passed.

Contract files are byte-identical; SHA-256: 4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde

Dashboard next action: sign in normally, open Command Center, select the Master, send PING and inspect ACK/response history. No login bypass was used.
