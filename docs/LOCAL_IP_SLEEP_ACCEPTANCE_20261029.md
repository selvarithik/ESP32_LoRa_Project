# Local IP repair and timed deep sleep — 29 October 2026

## Gateway listener fixed

The saved listener used 192.168.1.103, which was no longer assigned to this computer. Using the existing revision-checked configuration handler, changed only Gateway listener bind_address to current Wi-Fi address **192.168.1.102**, retaining port **5001** and enabled state; revision 5 -> 6. The running Gateway executable now listens there. Unauthenticated challenge returned 401, enrolled Master challenge returned 200 and its HMAC signature verified against the protected existing credential. Dashboard remains on http://127.0.0.1:5000.

No wildcard bind, authentication bypass, device IP transport enablement, Wi-Fi change, MQTT profile change or sensor setting change was performed. This verifies the real listener and signed challenge; it is not a Master IP telemetry exchange test. If DHCP changes this laptop address again, update Local IP settings or arrange an address reservation on the router. No router setting was changed automatically.

## Real Master deep sleep and wake passed

Master COM8 / ESP32-10777D842178 received SLEEP_NOW through the permanent EMQX worker, returned ACCEPTED ACK and separate PREPARING_TO_SLEEP response. One-time mode DEEP, requested duration 90 seconds; no saved sleep schedule update. The board stayed active while draining pending work, then stopped responding to USB status, woke without a manual reset and reported reset_reason **DEEPSLEEP** via GET_POWER_STATUS. It reconnected with verified TLS and completed a fresh PING ACK and execution response.

Observed timing: USB status still available around 56 seconds after the preparation response; unavailable in samples around 65–92 seconds; boot visible around 99 seconds; verified reconnection followed. The manual request window includes drain time and grace; this was not 90 full seconds of physical sleep. No power-consumption measurement was taken, so low-current performance is not claimed. Light-sleep mode and E220 sleep remain separate tests.

Saved sleep_enabled remains false; original persistent schedule unchanged. MQTT revision, fingerprint, client ID and sensor enable/pin values match pre-test snapshot. Wi-Fi station IP remains 192.168.1.105. After wake INA219 reads OK and MQ135 reports WARMING_UP_RAW_ONLY; DHT11 remains READ_ERROR. No false temperature/humidity was generated.

## MQ-135 remains uncalibrated

Manufacturer guidance was reviewed; see MQ135_CALIBRATION_ASSESSMENT_20261029.md. Internet standard concentrations cannot replace a known local calibration atmosphere, measured circuit/load values and verified initial preheating. No invented ppm, AQI or safe-air judgement was added.

The matching JSON records actual command IDs, ACK/response timestamps, wake reset reason, final PING result and sanitized preservation checks. Raw local snapshots remain excluded from Git.

Final Gateway regression run: 190 tests passed in 121.1 seconds. Post-wake INA219 and MQ135 MQTT values were fresh (approximately four seconds old); DHT11 values remained stale and were not treated as live.
