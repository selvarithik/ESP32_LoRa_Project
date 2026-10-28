> Historical baseline: BLE is removed from active scope. Current shared builds and
> E220 implementation status are in SHARED_FIRMWARE_REPORT.md; old missing-feature
> descriptions below are not current runtime specifications.

# Software completion baseline — 2026-10-19

Inspected existing source before implementation. This phase has no attached ESP32 and will not use serial, upload, erase or reset hardware. Earlier physical evidence is historical. Private Chat and OTA are excluded; their current file hashes are recorded separately to verify no edits in this phase.

| Feature | Baseline classification | Actual source / function |
|---|---|---|
| Master and Node entry | Implemented, build-tested previously | src/main.cpp setup; roles/master.cpp and node.cpp call shared NetworkService |
| Addressed packets, CRC/TTL and validation | Implemented, host-tested | protocol/protocol.cpp Message::fromJson; packet_validation_core.h |
| Command ACK/response/retries | Partial: normal commands work; restart/sleep absent; volatile dedup | core/network_service.cpp execute/handleCommand, backend/device_api.py pending_commands |
| Local IP with authenticated device ingress | Implemented, software-tested, historical physical evidence | transport_manager.cpp localRequest; backend/local_ip.py |
| Wi-Fi | Partial: scan/retry/DHCP/static exist; mask/subnet validation/DNS2/diagnostics incomplete | wifi_manager.cpp; config_manager.cpp validate |
| TLS MQTT | Implemented runtime/staging/recovery; live worker ACL-gated | canonical_mqtt.cpp, mqtt_staging.cpp; backend/mqtt_service.py and mqtt_store.py |
| Saved multiple MQTT profiles | Missing catalog; active/candidate staging exists | MqttStaging, Store.stage |
| DHT11 and intervals | Implemented, old physical evidence; no injectable host sensor yet | sensors/sensor_manager.cpp; telemetry_seconds validated 2..3600 |
| Display names | Device config exists; remote update not supported | DeviceConfig.device_name, CONFIG_UPDATE allowlist |
| Live dashboard/status | Implemented, browser-tested | dashboard.js, sensor-widgets.js, live snapshot API |
| Slave discovery | Explicit authorized HELLO, volatile peers; no multi-device simulator | NetworkService::accept/loop |
| LoRa | Blocked by unavailable exact E220 SKU/frequency/region/power/pins verification | lora_transport.cpp compile-disabled UART implementation; no integrated mock driver |
| BLE | Missing runtime scan/commands; reserved fields only | DeviceConfig.ble_enabled, DiagnosticsManager NOT_AVAILABLE |
| Sleep schedule | Missing | No scheduler or persistent schedule fields |
| Ethernet | Blocked by unknown PHY/module/pins | IpNetwork::ethernetAvailable false |
| Offline multi-device acceptance | Missing | Existing unit/host/local TCP/UI tests; no Master+multiple-Node simulator |

Build is PlatformIO espressif32 7.0.1 / Arduino; actual target previously identified ESP32-D0WDQ6, 4MB flash. Existing default app capacity 1,310,720 bytes, second slot present. BLE native-library inclusion may require a larger source-only build layout; no physical partition deployment is permitted in this phase.
