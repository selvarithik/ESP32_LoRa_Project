# Completion report — 28 October 2026

## Implemented and verified
1. ESP32 MQTT/TLS allocation-error recovery: the event callback captures the SDK error and requests recovery; the network task stops/destroys the old client and its TLS/outbox allocations, then recreates it with bounded 1–60 second backoff and internal-memory guards. No reboot, TLS bypass, profile switch or NVS write is used. Unconfirmed outbox bytes released are reported separately; application-level retry/persistence logic remains authoritative. USB mqtt_reconnect is identity-confirmed and runtime-only.
2. Gateway BIND_FAILED: its saved listener address 192.168.1.104 was no longer assigned. The Gateway-only bind address was changed to the current Wi-Fi adapter 192.168.1.103, port 5001. No ESP32 Wi-Fi setting was changed. Live listener state LISTENING, last_error=null, and unauthenticated challenge HTTP401 were verified. Startup now distinguishes ADDRESS_NOT_ASSIGNED from PORT_IN_USE/BIND_REJECTED in diagnostics. Physical local-IP device exchanges were not enabled/tested because this acceptance run is EMQX-only.
3. Non-secret remote configuration: CONFIG_UPDATE accepts role, master_id, wifi_ssid, local_ip_enabled and routing_policy with expected_revision. Existing IP controls remain. Python/C++ admission parity passed. Connectivity values are saved for an explicit restart; saved is not reported as live applied. Role-specific firmware rejects a role that conflicts with its image (MATCHING_ROLE_FIRMWARE_REQUIRED). No connectivity-changing command was sent to the live Master. Wi-Fi/broker passwords, tokens and mesh keys remain local-provisioning only.
4. MQTT observations: a bounded 200-entry feed records validated/persisted canonical traffic from the existing permanent worker. It returns headers and allowlisted summaries, never arbitrary raw payloads. A live filter and canonical config PROBE queueing are implemented. UI showed real telemetry/status/command_ack messages and no console errors. PROBE returned QUEUED / NOT_YET_ACKNOWLEDGED; this is not claimed as confirmed delivery. No second worker or general wildcard subscription was added.
5. MQ135 offline calibration tool: tools/mq135_calibration.py computes Rs/R0 only from supplied measured RL, divider gain, supply, reference concentration and gas-specific curve. Arithmetic and invalid-input tests pass. It writes no device settings.

## Physical acceptance
- Master ESP32-10777D842178 on COM8; EMQX only, mandatory certificate/hostname verification, MQTT3.1.1/QoS1.
- Application-only upload verified by flash hash. Protected NVS/partition/OTA bytes matched before/after; DPAPI backup round-trip verified. No flash layout change.
- Linked flash: 1,303,417 / 1,310,720 bytes (99.4%). RAM: 75,276 / 327,680 (23.0%). Firmware image: 1,310,128 bytes; 592 bytes remain in application slot. Default partition, second OTA slot and filesystem preserved.
- Three runtime client-recreation cycles recovered VERIFIED TLS and READY subscriptions without reboot; profile fingerprint/revision unchanged. Unit test covers allocation error -0x7F00, non-allocation failures, retry bounds, memory gating and timer wrap. Actual low-memory failure was not forcibly injected into the live board; multi-hour stability is still pending.
- Actual Dashboard PING CMD-81CBE4B68627: ACK ACCEPTED at 19:10:17.040392 IST; RESPONSE COMPLETED at 19:10:17.241246 with ok=true and the test echo. The database and browser response were both checked.
- 144 fresh MQTT sensor values had arrived from 19:10:17 to 19:13:18 at the recorded acceptance checkpoint. Dashboard showed fresh temperature/humidity, INA219 and raw MQ135. MQ135 still correctly reports warming-up/raw-only as applicable.
- Full Gateway Python suite: 160 tests passed. Existing Windows temporary SQLite cleanup warning remains after unittest OK; not represented as clean teardown. New completion tests cover remote validation/revision and secret rejection, feed bounds, auth/CSRF, bind diagnostics and calibration arithmetic.
- Native C++ command rules/registry parity, MQTT command gate, allocation recovery, persistence routing and cache-release checks passed. Generated gzip assets match source. Contract copies remain identical: SHA256 4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde.

## Preservation
Gateway complete MQTT document and protected .bin files match the captured SHA256 fingerprints. Master MQTT revision, shared/secret revisions and active fingerprint remain unchanged across runtime recovery. No Wi-Fi or sensor mutation was sent. Only the Gateway listener bind setting changed, as requested. No Slave upload, RF transmission, BLE, Chat or OTA development was performed in this work.

## Exact limits
- Permanent recovery logic is implemented; a multi-hour soak and a naturally recurring allocation failure still require observation. Three successful reconnects are not proof that all future memory pressure is eliminated.
- Real MQ135 gas-concentration calibration cannot be completed from an invented reference. Measured load resistance and a known reference for a selected gas are required; raw readings stay unchanged.
- Unrestricted arbitrary MQTT publish/subscribe remains excluded by the canonical-topic/security contract and currently verified ACL scope. The implemented feed and PROBE are real, but are not advertised as an unrestricted MQTT Explorer. Use Command Center for validated commands.
- Remote role switches need a compatible image; the explicit Master image will not silently become a Slave. Wi-Fi credential replacement requires USB commissioning. New non-secret connectivity mutations were tested in software, not applied to the live device.
- Existing Slave damage/LoRa physical verification and regional RF approval remain outside this Master-only test.

## GitHub
Source and regression tests are prepared for both existing repositories. Runtime databases, credentials, protected backups, raw telemetry reports and screenshots are excluded from the code commits. Git push results are recorded separately after the push completes.
