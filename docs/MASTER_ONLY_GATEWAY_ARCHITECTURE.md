# Master-only Gateway work — 25 October 2026

Current architecture: Flask/Jinja with local assets, Socket.IO updates and SQLite. Account sessions/roles/CSRF are owned by account_settings. HMAC local_ip accepts physical device packets and persists through device_api. The MQTT service uses the canonical 15-field profile, topic builder, protected secret store and revisioned candidate journal. The permanent worker requires ACL confirmation. Shared ESP32 source has separate role builds; Master-only physical tests do not verify Slave behavior.

Existing routes reused: /, /nodes, /sensors, /communication, /mqtt, /command-center, /logs, /system, /system-overview, /device-controls, /local-ip, /accounts. Preserve /chat and /firmware without developing or testing those excluded features. Device IDs/foreign keys stay stable; hardware MAC aliases and name commands already exist. Current MQTT revision and all Wi-Fi/sensor/credential stores are preserved.

Implementation order: protected source snapshot; login visual redesign; shared grouped navigation and read-only operational overview; separate Network/Diagnostics entry points reusing existing settings/commands/log APIs; bounded active-profile MQTT diagnostic without activation; regression, browser and real Master command tests. Remove only the Dashboard recent-logs component. No database schema migration or new configuration contract is required.

Read-only overview must distinguish configured parent relationships from observed RF links. RF packet-loss/RSSI/SNR stay unknown without firmware evidence. A broker loopback verifies only the tested topic, not the full ACL matrix or physical Master MQTT delivery. Local-IP mode must not be silently disabled for cloud testing. The owner reports the Slave damaged: no further COM11 operations.

Source snapshot: ignored data/system-audit/pre-ui-reorganization-20261025.zip. It includes existing source modifications and excludes secret stores/databases. No commits or push requested.
