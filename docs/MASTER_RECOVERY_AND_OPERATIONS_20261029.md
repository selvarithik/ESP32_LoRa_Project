# Master COM8 recovery and operational acceptance — 29 October 2026

Final firmware **1.1.1-recovery** uploaded and verified on ESP32-10777D842178, COM8. EMQX only. Gateway remains running. This is bounded acceptance evidence, not production readiness or a long soak certification.

## Changes and recovery evidence

- MQTT network worker now recycles a stale client after Wi-Fi return or bounded connection stall, with existing memory guards/backoff and mandatory verified TLS. Valid profile selection remains independent of a temporary SDK-client restart; no unintended HTTP fallback.
- WIFI_RECONNECT waits for Gateway persistence of its acceptance ACK, reconnects using existing saved settings, then requires MQTT subscription readiness before reporting completion.
- Restart result persistence survives reboot and stops repeated replay after Gateway receipt. Recovery command defaults are 120 seconds; expiry and response deadlines are classified separately. Routine own-device telemetry may be discarded during power drain; critical responses and forwarded messages are retained.
- Real WIFI_RECONNECT completed in **37.85 s**; following PING completed. Real RESTART completed in **59.82 s**, including post-boot execution response; following PING completed. Restart can still wait for pending critical work, so it is not an instant reboot.
- Initial iteration exposed a BUSY response when the next operation was immediate; final acceptance uses 1.5-second pacing and retains the initial evidence separately.

Commands were submitted through the owner's local validated Gateway command queue. Actual ACKs and execution responses came through the permanent EMQX worker and were persisted in SQLite. No synthetic ACKs, additional MQTT client, forged browser session or authentication bypass was used. Dashboard clicks and browser authentication were not reverified in this acceptance run.

## Twelve operational commands

| Command | ACK | Execution response | Detail |
|---|---|---|---|
| SYNC_TIME | ACCEPTED | COMPLETED | Completed through real worker. |
| MQTT_CONNECT | ACCEPTED | COMPLETED | Completed through real worker. |
| MQTT_RECONNECT | ACCEPTED | FAILED | VERIFIED_IP_RETURN_PATH_REQUIRED |
| MQTT_DISCONNECT | ACCEPTED | FAILED | VERIFIED_IP_RETURN_PATH_REQUIRED |
| MQTT_TEST | ACCEPTED | COMPLETED | Actual Gateway persistence receipt received. |
| RADIO_INSPECT | ACCEPTED | FAILED | MODE_RESTORE_TIMEOUT |
| DISCOVER_NODES | ACCEPTED | FAILED | REGISTRATION_CLOSED |
| I2C_SCAN | ACCEPTED | COMPLETED | Found 0x40 on SDA21/SCL22. |
| GET_COMMAND_RESULT | ACCEPTED | COMPLETED | Completed through real worker. |
| RESET_DIAGNOSTIC_COUNTERS | ACCEPTED | COMPLETED | NETWORK counters reset as requested; queue/history retained. |
| SLEEP_NOW | ACCEPTED | COMPLETED | Preparation accepted; cancelled before entry. Actual sleep/wake not tested. |
| CANCEL_PENDING_SLEEP | ACCEPTED | COMPLETED | Cancellation confirmed; saved schedule unchanged. |

**8 completed, 4 returned explicit failures.** MQTT_RECONNECT and MQTT_DISCONNECT require a verified alternate IP return path; it was not enabled because this run is EMQX only. RADIO_INSPECT returned MODE_RESTORE_TIMEOUT/AUX not ready without register writes or RF transmission. DISCOVER_NODES returned REGISTRATION_CLOSED; registration and radio settings were preserved. These are truthful guarded/failure results, not successful positive-path verification.

## Continuous telemetry

The final **180.1-second** observation received **108 MQTT sensor values**, 18 each for INA219 bus voltage, shunt voltage, current and power, plus MQ-135 raw ADC and pin mV. Maximum receive gap was **11.18 seconds**, consistent with the saved 10-second telemetry interval plus transport jitter. Every sampled MQTT state was connected, certificate verification VERIFIED (zero verification flags), authentication ACCEPTED and subscription READY. No observed disconnect, reboot, USB error or increase in drop counter occurred during this window. This short run does not prove indefinite stability.

DHT11 still reports NO_RESPONSE/READ_ERROR: **zero new temperature or humidity values**. Old readings must remain stale. Physical sensor/wiring replacement isolation remains required. MQ-135 is raw, uncalibrated and reports warm-up status; no gas concentration or calibration was fabricated. INA219 current/power use the configured shunt, not a new reference calibration.

## Preservation and deployment

A full 4 MB flash backup was encrypted locally with Windows DPAPI and verified before upload. Only the application at 0x10000 was written. Readback confirmed the exact image and all flash bytes outside its sector-aligned application region unchanged before reboot. NVS, partition table, bootloader and filesystem were preserved. Runtime journals legitimately update NVS after boot.

Existing huge_app layout retained: application capacity 3,145,728 bytes, no second OTA slot. No partition/filesystem deployment or erase-all was performed. Program size **1,361,121 bytes (43.3%)**, static RAM **76,004 bytes (23.2%)**; image file **1,367,824 bytes**. Upload hash and encrypted backup verification are in MASTER_RECOVERY_UPLOAD_20261029.json in the firmware docs.

MQTT revisions remain 77/shared 2/secret 7, active fingerprint and client ID preserved. Public config revision remains 11; recovery/operational GET_CONFIG values match. Gateway broker document, protected secrets, local-IP token and account store match the pre-deployment baseline. Wi-Fi, MQTT profile and sensor settings were not edited. Saved sleep schedule was not changed. SYNC_TIME changes the runtime clock, RESET_DIAGNOSTIC_COUNTERS resets requested counters, and restart/reconnect affect runtime state intentionally.

## Software verification

- Gateway full suite: **189 passed**. Additional final targeted operational suite: **8 passed** (includes the new power-status receipt regression); a combined 190-test full run was not claimed.
- Native firmware recovery, delivery, operations, shared controls, MQTT command gate and persistence receipt checks passed.
- Cross-language parity: **6 native C++/Python vectors passed**. Contract copies byte-identical; SHA-256 listed in accompanying JSON. Firmware contract checks, gzip asset check and local/MQTT page mock checks passed.
- PlatformIO esp32dev final build passed. Updated frozen Gateway executable passed isolated login/CSRF, Socket.IO polling, backup, single-instance and shutdown smoke checks, then was deployed with the old bundle retained.
- Git diff whitespace checks passed for both repositories (line-ending warnings only).

## Remaining actions

1. DHT11: repair/replace or isolate the powered sensor on GPIO4, then verify fresh temperature/humidity end to end.
2. Positive MQTT disconnect/reconnect command tests need an independently verified IP return path; do not disable the safety guard.
3. Actual sleep/wake is pending; this run verified preparation and cancellation only.
4. E220 UART/AUX fault, approved radio configuration, registration, RF and physical Slave forwarding remain unverified. No RF test was performed.
5. Gateway saved LAN listener still reports BIND_FAILED; no network setting was changed in this request. EMQX command/telemetry testing was independent of that listener.
6. Longer outage/soak and browser live-display checks remain separate acceptance work. Current evidence proves Gateway ingestion/database persistence, not a new dashboard visual test.

Detailed sanitized command IDs, timestamps, upload evidence and telemetry metrics are in the accompanying JSON. Private raw evidence and encrypted backup remain in local ignored data folders; no credentials are included in this report.
