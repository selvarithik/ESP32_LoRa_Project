# Master COM8 — 30-minute EMQX stability test, 28 October 2026

Started: 2026-10-28T19:29:19.889861 IST. Finished: 2026-10-28T19:59:24.196153 IST. Observation duration: 1804.3 seconds.

**Result: COMPLETED_WITH_NETWORK_FINDINGS.** This is a physical test through the permanent EMQX worker, not a simulator. No firmware upload, forced reconnect, reboot, Wi-Fi change, MQTT-profile change or sensor-setting change was performed during this test.

## Outcome summary

- 30 minutes 4 seconds observed, 19:29–19:59 IST.
- 5/6 PINGs received both ACCEPTED ACK and successful execution RESPONSE; one timed out.
- 1 automatic MQTT reconnect, 0 additional client-recreation operations and 0 observed reboots. Final Master state: connected, VERIFIED TLS, READY subscriptions.
- 1,096 new MQTT sensor values persisted. INA219 and raw MQ135 resumed after a maximum 98.839-second inter-reading gap and were fresh at finish.
- DHT11 stopped producing new values after approximately 5 minutes 50 seconds; the final device health reports READ_ERROR / NO_RESPONSE with zero captured pulses and DATA idle-low. The cause was not established or corrected during this observation-only test.
- Gateway MQTT/protected files and the rechecked Master MQTT/sensor settings were unchanged. No configuration mutations were sent.
- Eight initial persistent serial-observer timeouts are recorded separately; the final short USB status recheck succeeded. These limitations were not hidden or counted as successful TLS samples.

## PING acknowledgement and execution

| Command ID | Queued at elapsed seconds | State | Device ACK | Device execution success |
| --- | ---: | --- | --- | --- |
| CMD-1ABAA44BF373 | 0.5 | COMPLETED | ACCEPTED | True |
| CMD-C1D89F432769 | 350.9 | TIMEOUT | Not received | False |
| CMD-FC54C43C5C6C | 601.5 | COMPLETED | ACCEPTED | True |
| CMD-28376D7CF588 | 902.1 | COMPLETED | ACCEPTED | True |
| CMD-D8C069D5EF65 | 1202.7 | COMPLETED | ACCEPTED | True |
| CMD-DB81D0D917F2 | 1503.5 | COMPLETED | ACCEPTED | True |

## MQTT sensor persistence

Fresh database values during window: 1096. Source filter: mqtt, selected Master only.

| Parameter | Fresh values | Largest inter-reading gap (s) | Age at finish (s) |
| --- | ---: | ---: | ---: |
| temperature | 35 | 12.855 | 1454.3 |
| humidity | 35 | 12.855 | 1454.3 |
| bus_voltage | 171 | 98.83 | 5.091 |
| shunt_voltage | 171 | 98.83 | 5.091 |
| current | 171 | 98.83 | 5.091 |
| power | 171 | 98.83 | 5.091 |
| mq135_adc_raw | 171 | 98.839 | 4.798 |
| mq135_pin_mv | 171 | 98.839 | 4.798 |

A largest inter-reading gap does not capture a signal that stopped altogether: the age-at-finish column identifies stale temperature/humidity. MQ135 remains raw/uncalibrated.

## Runtime and preservation

MQTT heartbeat reboots observed: 0. Device-reported heap range: 69868–75808 bytes. First/last five-sample heap medians: 73428/73008 bytes. Total free heap alone cannot rule out fragmentation.

Gateway MQTT document and protected-file fingerprints unchanged: True. Master saved settings recheck: True. The only commands sent were six PINGs. No setting mutations were sent.

## Instrumentation limitation

The initial persistent serial status observer produced 8 timeouts. Its driver was replaced while preserving the original start/deadline and existing PING IDs. Monitoring continued using read-only MQTT heartbeats and persisted MQTT telemetry. The second PING was queued after that instrumentation handover; actual elapsed timestamps above are authoritative.

Final serial recheck: Available. Final direct Master runtime: {'tls_state': 'VERIFIED', 'state': 'connected', 'subscription_state': 'READY', 'reconnect_count': 4, 'tls_client_recycles': 3, 'outbox_bytes': 2330, 'dropped': 0}. Do not infer exact TLS reconnect/recovery counters if the final serial recheck was unavailable.

No production-readiness or permanent-reliability claim follows from this bounded test. The observed outages, missing ACKs and DHT11 read errors require follow-up diagnosis.
