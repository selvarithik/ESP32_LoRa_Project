# System audit findings before edits — 2026-10-25

The existing Commands/Command Center is the requested comments/responses path.
No separate Comments API exists in the inspected templates. Private Chat remains
excluded. UI -> authenticated/CSRF command API -> command_manager SQLite queue ->
device_api.pending_commands -> signed local-IP Master exchange -> NetworkService
-> addressed radio route -> Slave handler -> ACK and distinct execution RESPONSE
-> Master bridge -> device_api.ingest -> command_manager and Socket.IO -> cards.

ACK ACCEPTED/REJECTED/BUSY/DUPLICATE is not execution success. Final correlated
RESPONSE completes/fails; timeout remains unknown execution. Gateway scheduling
is durable; ordinary firmware deduplication is bounded/volatile. No physical
exactly-once promise across reset. Cards escape payload text and retain real state.

Confirmed on hardware/source before modification:

* COM12: expected ESP32-10777D842178, MASTER, IP192.168.1.104. LoRa disabled.
  DHT11 READ_ERROR; INA219 reports valid voltages/current/power; MQ135 raw only.
* COM8: ESP32-CC9B23E2DEC4, actual MASTER firmware/role with INA acquisition enabled,
  not the requested Slave profile. First-use password change still required.
  LoRa disabled, no station connection; DHT11/INA219 READ_ERROR. Native ADC input
  is not proof of an attached/calibrated MQ135.
* Master points to stale192.168.1.108:5001; current laptop Wi-Fi192.168.1.105.
  No Gateway process/listener was running. Server normal entry point starts MQTT,
  so this task needs a local-only launch path that does not call MQTT startup.
* Current USB config rejects all settings until first password change. Correcting
  an explicit build-role mismatch therefore needs a narrowly identity-confirmed
  physical commissioning operation, preserving accounts/secrets and all other fields.
* Existing production authentication uses revocable process-local sessions and
  CSRF. No supported loopback test session exists; a default-disabled, loopback-only
  test session may reuse existing accounts without modifying their database.
* Command Center has stale static 'driver unavailable' wording despite the compiled
  RV1 driver, and response cards lack the actual target/source labels. Its state
  chip labels must not imply response arrival is always successful execution.

No firmware/module settings were changed for this initial audit. Radio registers
must be inspected read-only before any RF/configuration changes. India/868MHz
antenna information supplied; actual channel/power/duty constraints are not inferred
from antenna label. No MQTT connection/test/settings change is authorized here.
