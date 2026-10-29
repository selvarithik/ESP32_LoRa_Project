# Sensor latency and radio checks — 25 October 2026

Status: software changes built and uploaded; physical Slave DHT11 and RF acceptance remain pending. This is not an all-gates or production-readiness claim.

## Changes in this task

Firmware: `src/sensors/dht_provider.h`, new `dht_pulse_core.h`, and sensor_manager.cpp use hardware RMT pulse capture with bounded waits and truthful capture diagnostics. Sensor GPIO4, enabled flags and sampling settings are preserved. Added portable decoder tests. Master physical readings are valid with 84 captured pulses; Slave reports NO_RESPONSE, zero pulses and DATA idle high. This narrows the next check to the physical sensor/DATA path but does not prove exactly which component failed. Owner cannot swap the modules now. Next physical action: power off, test a known-good module and DATA lead on Slave GPIO4; verify 3.3 V/common ground and module pull-up. No fabricated or old measurement is substituted.

Firmware: network_service.cpp and delivery_core.h coalesce own unsent telemetry and release non-command work after authenticated HTTP transport acceptance. QUEUED means peer ownership, not end-to-end persistence. Command ACK/RESPONSE and radio receipts remain separate. New delivery assertions cover these distinctions.

Gateway: telemetry_manager.py derives a freshness grace from enrolled-device telemetry cadence without writing saved settings. sensor-widgets.js and dashboard.js share this grace; index.html/sensors.html cache versions updated. For a reported 10-second interval and saved 10-second timeout, effective display timeout is 25 seconds. Offline, invalid and missing measurements remain distinct; no value is manufactured. Four API/persistence regression cases and production-JS freshness checks added.

## Verification categories

- Gateway unit/API regression: 85 run, 85 passed, zero errors/failures/skips. Scope excludes MQTT/cloud, Chat, OTA and physical runners; this is not a full unrelated-feature acceptance claim.
- Firmware native logic: DHT pulse decoder, delivery receipt policy, E220 framing/settings and existing local-link checks passed. Native tests are not physical RF evidence.
- JavaScript: freshness state checks and syntax checks passed. Browser runtime inspected actual Dashboard; both nodes ONLINE, Master physical DHT/INA219/MQ135 readings and Slave MQ135 readings Live. Slave DHT11 truthfully READ ERROR / N/A. Screenshot: SENSOR_LATENCY_DASHBOARD.png in Gateway docs.
- Both PlatformIO Master/Slave builds passed. Embedded web asset generator check and existing page checks passed earlier in this task; no page-source changes after uploads.
- Real local-IP command: CMD-DE4C10CB2B70 completed with ACCEPTED ACK and execution RESPONSE; about 4.02 seconds from creation to response. This proves the IP path, not LoRa or MQTT.
- Real two-minute read-only Gateway observation: each monitored series had 12 readings. Median gaps approximately 10 seconds; maximum Master temperature 10.345 s, current 10.317 s, Master MQ135 12.893 s, Slave MQ135 15.567 s. No uptime decrease in the captured observation. A Slave POWERON restart occurred outside that window; cause unconfirmed. Intermittent HTTP 400/401/408/timeouts and other transport errors remain in diagnostics, including after restart. Long soak and complete reconnect root-cause resolution are pending; no guaranteed latency claim.
- MQTT/live cloud tests: not run or reconfigured. No broker worker started by the local audit wrapper.

## Upload and preservation

Master COM8: ESP32-10777D842178. Slave COM11: ESP32-CC9B23E2DEC4. Both application-only uploads at 0x10000 were readback/hash verified. Partition/NVS/OTA bytes at 0x8000..0x10000 identical before/after upload; protected backups roundtrip verified. No erase, partition-table deployment or filesystem upload.

| Build | Program bytes | Image bytes | Static RAM bytes | Image headroom |
|---|---:|---:|---:|---:|
| Master | 1,296,953 | 1,303,664 | 74,700 | 7,056 |
| Slave | 1,292,065 | 1,298,768 | 74,652 | 11,952 |

Application capacity remains 1,310,720 bytes; verified 4 MB board/layout. Master program usage 98.95%, RAM 22.80%; Slave program usage 98.58%, RAM 22.78%. Images fit but headroom is small. Existing default layout, second app slot and filesystem remain unchanged. No OTA development added.

Gateway sensor_parameters table hash and MQTT configuration document hash match their pre-display-change baseline. Protected accounts/secret-store/session-key files and excluded Chat/OTA source/artifact baseline also match. Saved device MQTT/Wi-Fi/sensor settings were preserved by upload readback. Contract copies are byte-identical, current version 1.2.0 / wire schema 1, SHA-256 `4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde`. No contract changes in this task.

## Radio result and remaining actions

Both E220 modules answered read-only UART settings inspection: channel18 / 868.125 MHz, transparent mode, 22 dBm, address0, baud9600, air rate2.4 kbps. No radio registers changed and no RF packets transmitted. Current center frequency lies above the 865–868 MHz tables examined for India. Merely changing channel/power does not verify the applicable channel-access/duty/APC and equipment-approval requirements. A supported approved operating profile must be established before enabling automatic radio traffic; no LoRa ACK or delivery result is claimed.

Official reference: [DoT SRD compendium, PDF pages137–139](https://www.dot.gov.in/static/uploads/2025/07/84f33f09e137fa81930f44bcd5f2d238.pdf). Module reference: [EBYTE E220 manual](https://www.ebyte.com/Uploadfiles/Files/2021-7-6/202176188184448.pdf).

MQ135 remains raw, warming up and uncalibrated; it is not a gas-concentration or safety measurement. Slave INA219 remains inhibited by its existing profile; no sensor setting changed.

Gateway remains running at http://127.0.0.1:5000 with device listener 192.168.1.104:5001. Current device station addresses observed: Master 192.168.1.106, Slave 192.168.1.105; DHCP addresses may change.

Evidence: SENSOR_LATENCY_EVIDENCE.json, SENSOR_LATENCY_SOAK.json, SENSOR_LATENCY_PRESERVATION.json, role-specific SENSOR_LATENCY_UPLOAD.json and BUILD_EVIDENCE.json. Existing dirty work was preserved; no Git commit/push/reset performed.
