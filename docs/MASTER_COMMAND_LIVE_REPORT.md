# Physical Master command and response check - 2026-10-26

Master COM8: ESP32-10777D842178. Slave not used.

Initial actual EMQX tests published with broker QoS 1 PUBACK and command-topic echo, but received no device ACK or RESPONSE. Root cause: canonical_mqtt.cpp checked a JsonVariantConst packet using is<JsonObject>(), which is unsupported and returns false. Changed this to is<JsonObjectConst>(). No protocol, profile or saved settings changes.

Regression executes the actual production command gate with ArduinoJson: valid const packet accepted; arrays, null, extra fields and wrong message types rejected. Native command admission/registry parity passed. Gateway command-center suite: 16 tests passed (simulated devices, separate from hardware evidence).

Corrected application uploaded to COM8 with flash hash verification. Protected NVS/partition/OTA bytes unchanged. Image 1,307,392 bytes; linked program 1,300,693 / 1,310,720 bytes; RAM 74,732 / 327,680 bytes. Partition layout retained.

Actual EMQX verified-TLS test: PING CMD-E420302D34CD and GET_SENSOR_STATUS CMD-21728F2ACA94 each received a correlated physical Master ACK and RESPONSE, then persisted as COMPLETED in the Gateway SQLite command history at 20:51 local. Active Gateway MQTT state/profile/revision unchanged.

Scope limitation: bounded engineering command client used a unique client ID and the saved protected profile. The normal permanent worker remains TELEMETRY_ONLY; this test does not enable ordinary continuous dashboard MQTT command dispatch or claim broader ACL permission. No restart/settings commands were sent. DHT11 hardware read failure remains unresolved.

Evidence: MASTER_COMMAND_FIXED_TEST.json in Gateway docs; MASTER_COMMAND_GATE_UPLOAD.json in firmware docs.
