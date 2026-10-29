# Master COM8 EMQX acceptance test

29 October 2026. Real Master ESP32-10777D842178, IP 192.168.1.105, reported firmware 1.1.0-software. Commands were sent through the normally authenticated Chrome Command Center and the existing permanent EMQX worker. No second broker client, firmware upload, Wi-Fi credential/profile edit, MQTT profile edit or sensor-setting change was performed.

## Result

All 21 advertised primary commands were exercised once. Eighteen completed with ACCEPTED ACK and execution RESPONSE. WIFI_SCAN returned the expected protective error; WIFI_RECONNECT timed out; RESTART physically executed but its successful response arrived late. Follow-up PING, GET_POWER_STATUS and GET_CONFIG were additional recovery/readback checks, not repeated attempts to hide the failures.

The running device does not advertise the 12 newest operational extension commands. Those remain pending a separately reviewed firmware update. Exact flash-image identity was not read because no bootloader/reset probe or flash read was required for this runtime test.

## Command results

| Command | First command ID | ACK | Gateway result | Detail |
|---|---|---|---|---|
| PING | CMD-437E87838923 | ACCEPTED | COMPLETED |  |
| GET_CAPABILITIES | CMD-711BE6D95911 | ACCEPTED | COMPLETED |  |
| GET_STATUS | CMD-72E8C4A3F98B | ACCEPTED | COMPLETED |  |
| GET_CONFIG | CMD-BFF49DB045B4 | ACCEPTED | COMPLETED |  |
| GET_NETWORK | CMD-3AFB95B7C2E0 | ACCEPTED | COMPLETED |  |
| GET_TELEMETRY | CMD-8FCF8324A3CE | ACCEPTED | COMPLETED |  |
| GET_SENSOR_STATUS | CMD-D9E3C2A88856 | ACCEPTED | COMPLETED |  |
| GET_POWER_STATUS | CMD-C9C80A8A6F07 | ACCEPTED | COMPLETED |  |
| GET_RADIO_STATUS | CMD-55864D79AF7A | ACCEPTED | COMPLETED |  |
| GET_MESH_STATUS | CMD-52DA556B3DF3 | ACCEPTED | COMPLETED |  |
| GET_NODE_STATUS | CMD-A91729DBDF01 | ACCEPTED | COMPLETED |  |
| GET_ROUTE_INFO | CMD-B885C86B3FE2 | ACCEPTED | COMPLETED |  |
| DIAGNOSTICS | CMD-ECFFA3570AE2 | ACCEPTED | COMPLETED |  |
| WIFI_SCAN | CMD-A439C87B6DAE | ACCEPTED | FAILED | WIFI_SCAN_BUSY_MQTT_ACTIVE; no disruptive scan |
| SET_DEVICE_NAME | CMD-BAEF54E3EBC7 | ACCEPTED | COMPLETED | Exact saved values; no-op; revision remained 11 |
| SET_TELEMETRY_INTERVAL | CMD-BDEC28528F0E | ACCEPTED | COMPLETED | Exact saved values; no-op; revision remained 11 |
| SET_HEARTBEAT_INTERVAL | CMD-D4E15945EDCB | ACCEPTED | COMPLETED | Exact saved values; no-op; revision remained 11 |
| SET_SLEEP_SCHEDULE | CMD-449399AB1F7D | ACCEPTED | COMPLETED | Exact saved values; no-op; revision remained 11 |
| CONFIG_UPDATE | CMD-601AD2E5F73D | ACCEPTED | COMPLETED | Exact saved values; no-op; revision remained 11 |
| WIFI_RECONNECT | CMD-8531097BD166 | Not received | TIMEOUT | Wi-Fi returned but MQTT remained CONNECTING; runtime USB recovery required |
| RESTART | CMD-A17DFFE68FF4 | ACCEPTED | TIMEOUT | Actual software reboot; successful LATE_RESPONSE; TIMEOUT retained |

## TLS and telemetry

Before testing, Master TLS was VERIFIED, authentication ACCEPTED, subscriptions READY, certificate verify flags 0, reconnect count 0 and dropped count 0. The permanent Gateway worker was connected.

The steady observation lasted 300.3 seconds and persisted 180 new MQTT values: 30 each for INA219 bus/shunt voltage/current/power and MQ135 raw ADC/pin millivolts. Maximum observed gaps were 11.533 seconds for INA219 and 11.527 seconds for MQ135. The configured telemetry interval remained 10 seconds. No reboot or TLS loss was observed during that steady window. This five-minute window is not a long stability qualification.

No fresh DHT11 temperature or humidity arrived. The real target reports READ_ERROR, NO_RESPONSE and zero response pulses. Dashboard correctly shows those readings stale. MQ135 remains raw, warming up and uncalibrated. INA219 has a configured 100 milliohm shunt; no new accuracy calibration was performed.

After recovery and restart, Master returned to VERIFIED TLS, READY subscriptions and fresh six-field sensor delivery. Post-restart PING CMD-27EE540C3167 completed with ACCEPTED ACK and MQTT-verified response. Dashboard was inspected at approximately 20:43 IST and showed fresh values for all six fields; DHT11 remained stale.

## Recovery findings

WIFI_RECONNECT CMD-8531097BD166 lost its ACK/result path and timed out. Wi-Fi rejoined, but MQTT remained CONNECTING without a reported certificate error. One existing identity-confirmed physical USB mqtt_reconnect operation recycled the runtime client and restored verified TLS/subscriptions within about eight seconds. It did not change NVS profile credentials or configuration. This manual runtime recovery is not a permanent automatic-reconnect fix.

RESTART CMD-A17DFFE68FF4 was sent at 20:39:58, acknowledged at 20:40:00, timed out at 20:40:30, then produced a successful LATE_RESPONSE at 20:41:04. Device uptime reset and GET_POWER_STATUS reported SOFTWARE reset, ACTIVE and restart_pending=false. The Gateway correctly retained TIMEOUT rather than retroactively converting it to timely success. Pending-work drain/response deadlines need follow-up.

## Preservation

Public GET_CONFIG before/after restart matches, including configuration revision 11. Master MQTT active fingerprint/client ID/revision 77/shared revision 2/secret revision 7 match the initial snapshot. Sensor enable/GPIO snapshot matches. Gateway MQTT document and protected credential files match the earlier deployment baseline. No secrets are included in this report.

The no-op device-name command used the already saved name ESP32 LoRa Device. Gateway display metadata now reflects that name instead of its prior ID label. The board name itself was unchanged.

## Remaining work

- Diagnose DHT11 physical no-response; do not fabricate temperature/humidity.
- Fix and regression-test automatic MQTT recovery after WIFI_RECONNECT.
- Reconcile restart drain timing with final-response/expiry semantics.
- Install and test the 12 operational extensions only under separate firmware deployment approval.
- Resolve the separately saved Local IP listener BIND_FAILED; it was not modified during this EMQX-only test.
- Correct the top-level OFFLINE badge while fallback HTTP polling is successfully updating.
- LoRa remains disabled; no RF, Slave, mesh, sleep-entry or radio-register-write test occurred.

Evidence: MASTER_COM8_EMQX_ACCEPTANCE_20261029.json. Raw private checkpoints are under data/live-master-20261029. Manual writing remains paused.
