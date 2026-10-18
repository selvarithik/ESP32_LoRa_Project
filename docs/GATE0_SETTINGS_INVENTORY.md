# Gate 0 settings inventory

2026-10-17. Source inspection, not proof of device configuration. Secrets intentionally not read. Canonical target names are distinguished from actual legacy storage. Every DeviceConfig member is accounted for below or in the legacy broker mapping.

| Setting | Canonical field | Class | Type | Default | Range/validation | ESP32 local UI | ESP32 firmware | Gateway UI | Python server | Current state | Test evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| profile.profile name | profile.profile_name | LOCAL | string | Primary Broker | 1..64 UTF-8 bytes | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| profile.provider | profile.provider | LOCAL | enum | EMQX | EMQX/HIVEMQ/MOSQUITTO/CUSTOM | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| profile.host | profile.host | SHARED | string | NONE | 1..253 ASCII DNS/IPv4; no scheme, path, whitespace, wildcard, localhost or unspecified address | planned /mqtt; existing root mqtt_host | planned canonical mqtt profile; legacy mqtt_host | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | partial | PENDING: implementation and behavioral tests |
| profile.port | profile.port | SHARED | integer | 8883 | 1..65535; bool rejected | planned /mqtt; existing root mqtt_port | planned canonical mqtt profile; legacy mqtt_port | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | partial | PENDING: implementation and behavioral tests |
| profile.mqtt version | profile.mqtt_version | SHARED | string | 3.1.1 | exactly 3.1.1 | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| profile.tls | profile.tls | SHARED | boolean | true | true only | planned /mqtt; existing root mqtt_tls | planned canonical mqtt profile; legacy mqtt_tls | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | partial | PENDING: implementation and behavioral tests |
| profile.ca cert | profile.ca_cert | SHARED | string | NONE | PEM CA certificate bundle, 1..4096 bytes; parse each certificate; trust verification mandatory | planned /mqtt; existing root mqtt_ca | planned canonical mqtt profile; legacy mqtt_ca | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | partial | PENDING: implementation and behavioral tests |
| profile.username | profile.username | LOCAL | string | empty | 0..128 UTF-8 bytes; component-specific | planned /mqtt; existing root mqtt_user | planned canonical mqtt profile; legacy mqtt_user | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | partial | PENDING: implementation and behavioral tests |
| profile.password | profile.password | SECRET | string | NONE | 1..256 UTF-8 bytes when replacing; absent/blank/all-stars preserve; reject NUL | planned /mqtt; existing root mqtt_password | planned canonical mqtt profile; legacy mqtt_password | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | partial | PENDING: implementation and behavioral tests |
| profile.client id | profile.client_id | LOCAL | string | NONE | 1..64 ASCII letters/digits/_.:-; unique per participant | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| profile.keepalive s | profile.keepalive_s | LOCAL | integer | 60 | 15..300 | planned /mqtt; existing root mqtt_keepalive | planned canonical mqtt profile; legacy mqtt_keepalive | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | partial | PENDING: implementation and behavioral tests |
| profile.timeout s | profile.timeout_s | LOCAL | integer | 10 | 2..30 seconds per operation; whole test bounded separately | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| profile.qos default | profile.qos_default | SHARED | integer | 1 | exactly 1; bool rejected | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| profile.topic prefix | profile.topic_prefix | SHARED | string | selvarithik/gateway | 1..128 ASCII bytes; nonempty slash-separated [A-Za-z0-9_-]+ levels; no wildcards | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| profile.gateway id | profile.gateway_id | SHARED | string | GW001 | 1..48 ASCII letters/digits/_.:-; no slash or wildcard | planned /mqtt; existing root absent | planned canonical mqtt profile; legacy absent | planned MQTT page | existing mqtt_adapter.py environment; planned canonical profile service | missing | PENDING: implementation and behavioral tests |
| device id | device_id | SHARED | string | MAC-derived; preserve stored identity | 1..48 ASCII [A-Za-z0-9_.:-], existing identity immutable | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/core/network_service.cpp, src/diagnostics/diagnostics_manager.cpp, src/identity/device_identity.cpp, src/mesh/mesh_manager.cpp, src/sensors/sensor_manager.cpp, src/web/local_web_server.cpp | /nodes or /system | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| device name | device_name | SHARED | string | "ESP32 LoRa Device" | 1..64 bytes | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/diagnostics/diagnostics_manager.cpp, src/web/local_web_server.cpp | /nodes or /system | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| role | role | SHARED | enum | NODE | MASTER/NODE only | existing / grouped form; planned sections | device/config_v1 NVS; src/main.cpp, src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/core/network_service.cpp, src/diagnostics/diagnostics_manager.cpp, src/roles/master.cpp, src/roles/node.cpp, src/web/local_web_server.cpp | /nodes or /system | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| mesh id | mesh_id | SHARED | string | "MESH-01" | 0..4096 UTF-8 bytes; legacy generic string bound | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/mesh/mesh_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| master id | master_id | SHARED | string | "" | empty or identity; NODE cannot refer to itself | existing / grouped form; planned sections | device/config_v1 NVS; src/command/command_manager.cpp, src/core/config_manager.cpp, src/core/network_service.cpp, src/diagnostics/diagnostics_manager.cpp, src/mesh/mesh_manager.cpp, src/web/local_web_server.cpp | /nodes or /system | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| preferred master | preferred_master | SHARED | string | "" | 0..4096 UTF-8 bytes; legacy generic string bound | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/mesh/mesh_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| backup master | backup_master | SHARED | string | "" | 0..4096 UTF-8 bytes; legacy generic string bound | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/mesh/mesh_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| node address | node_address | SHARED | string | "1" | empty or identity, unique per Master | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/mesh/mesh_manager.cpp, src/web/local_web_server.cpp | /nodes or /system | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| allowed peers csv | allowed_peers_csv | SHARED | string | "" | <=1024 bytes; comma-separated safe IDs; capacity 12 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/mesh/mesh_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| max hops | max_hops | SHARED | integer | 5 | 1..15 in v1 bridge; multi-hop unavailable | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/mesh/mesh_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| retry count | retry_count | SHARED | integer | 3 | 0..5 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| heartbeat seconds | heartbeat_seconds | SHARED | integer | 30 | 5..3600 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| route timeout seconds | route_timeout_seconds | SHARED | integer | 60 | 10..86400 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi enabled | wifi_enabled | LOCAL | boolean | true | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi ssid | wifi_ssid | LOCAL | string | empty | 0..32 bytes | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi password | wifi_password | SECRET | string | NONE; existing secret not inspected or exported | empty or 8..63 bytes; secret-preserving replacement | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| ethernet enabled | ethernet_enabled | LOCAL | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| ble enabled | ble_enabled | LOCAL | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| server host | server_host | LOCAL | string | "" | empty or DNS/IPv4 <=253, no scheme/path/loopback | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| server port | server_port | LOCAL | integer | 5000 | 1..65535 | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| server https | server_https | LOCAL | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| lora baud | lora_baud | SHARED | integer | 9600 | 1200,2400,4800,9600,19200,38400,57600,115200 | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/lora_transport.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora rx pin | lora_rx_pin | SHARED | integer | 16 | 0..39 reserved | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/lora_transport.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora tx pin | lora_tx_pin | SHARED | integer | 17 | 0..33 reserved | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/lora_transport.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora aux pin | lora_aux_pin | SHARED | integer | 27 | 0..39 reserved | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/lora_transport.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora m0 pin | lora_m0_pin | SHARED | integer | 25 | 0..33 reserved | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/lora_transport.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora m1 pin | lora_m1_pin | SHARED | integer | 26 | 0..33 reserved | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/lora_transport.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora channel | lora_channel | SHARED | integer | 0 | 0..83 legacy storage only; RF applicability unverified | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora air rate | lora_air_rate | SHARED | integer | 0 | 0..7 opaque register index; physical rate unverified | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora tx power | lora_tx_power | SHARED | integer | 22 | 0..30 legacy storage only; exact module settings unverified | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| protocol version | protocol_version | SHARED | integer | 1 | 1, frozen packet format | existing / grouped form; planned sections | device/config_v1 NVS; src/protocol/protocol.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| configuration version | configuration_version | SHARED | integer | 1 | 1 legacy; contract schema version separate | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| configuration revision | configuration_revision | SHARED | integer | 1 | 1..4294967295; no wrap; increment on effective persisted change | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/diagnostics/diagnostics_manager.cpp, src/web/local_web_server.cpp | /nodes or /system | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| enabled | enabled | SHARED | boolean | true | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/network_service.cpp, src/diagnostics/diagnostics_manager.cpp, src/web/local_web_server.cpp | /nodes or /system | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| registration open | registration_open | SHARED | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| admin password | admin_password | SECRET | string | NONE; existing secret not inspected or exported | write-only login input; legacy 10..64, target 12..64 with salted hash | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| setup password | setup_password | SECRET | string | NONE; existing secret not inspected or exported | 10..63 bytes | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| mesh key | mesh_key | SECRET | string | NONE; existing secret not inspected or exported | empty or 32..64 bytes | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| master host | master_host | LOCAL | string | empty | empty or DNS/IPv4 <=253, no scheme/path/loopback | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| gateway token | gateway_token | SECRET | string | NONE; existing secret not inspected or exported | 0..4096 UTF-8 bytes; legacy generic string bound | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| gateway ca | gateway_ca | LOCAL | string | empty | PEM <=4096 bytes required when corresponding TLS endpoint enabled | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| telemetry seconds | telemetry_seconds | SHARED | integer | 10 | 2..3600 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | device_api.py nodes/latest_status boundary | partial | PENDING: implementation and behavioral tests |
| command timeout ms | command_timeout_ms | SHARED | integer | 5000 | 1000..30000 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| message max age ms | message_max_age_ms | SHARED | integer | 60000 | command_timeout_ms..300000 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/core/network_service.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| dht enabled | dht_enabled | LOCAL | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/sensors/sensor_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| dht pin | dht_pin | LOCAL | integer | 4 | 4,13,14,18,19,21,22,23,32,33 | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/sensors/sensor_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi dhcp | wifi_dhcp | LOCAL | boolean | true | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi ip | wifi_ip | LOCAL | string | empty | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi subnet | wifi_subnet | LOCAL | string | "255.255.255.0" | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi gateway | wifi_gateway | LOCAL | string | empty | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| wifi dns | wifi_dns | LOCAL | string | empty | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/wifi_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| ethernet interface | ethernet_interface | LOCAL | string | "NOT_CONFIGURED" | 0..4096 UTF-8 bytes; legacy generic string bound | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| ethernet dhcp | ethernet_dhcp | LOCAL | boolean | true | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| ethernet ip | ethernet_ip | LOCAL | string | empty | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| ethernet subnet | ethernet_subnet | LOCAL | string | empty | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| ethernet gateway | ethernet_gateway | LOCAL | string | empty | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| ethernet dns | ethernet_dns | LOCAL | string | empty | IPv4 required when DHCP disabled; reserved Ethernet not consumed | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| ble name | ble_name | LOCAL | string | "ESP32 commissioning" | 0..4096 UTF-8 bytes; legacy generic string bound | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora enabled | lora_enabled | SHARED | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora uart | lora_uart | SHARED | integer | 2 | 0..2, reserved | existing / grouped form; planned sections | device/config_v1 NVS; src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora address high | lora_address_high | SHARED | integer | 0 | 0..255 | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora address low | lora_address_low | SHARED | integer | 0 | 0..255 | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora fixed mode | lora_fixed_mode | SHARED | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora lbt | lora_lbt | SHARED | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| lora rssi | lora_rssi | SHARED | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | disabled | PENDING: implementation and behavioral tests |
| mqtt enabled | mqtt_enabled | LOCAL | boolean | false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| internet probe host | internet_probe_host | LOCAL | string | empty | empty or DNS/IPv4 <=253, no scheme/path/loopback | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| internet probe ca | internet_probe_ca | LOCAL | string | empty | PEM <=4096 bytes required when corresponding TLS endpoint enabled | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| internet probe port | internet_probe_port | LOCAL | integer | 443 | 1..65535 | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| internet probe tls | internet_probe_tls | LOCAL | boolean | true | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/communication/transport_manager.cpp, src/core/config_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
| lora packet size | lora_packet_size | SHARED | null | NONE | unsupported; no register write allowed | existing if named, otherwise planned | no confirmed register semantics | existing if named, otherwise planned | no confirmed register semantics | partial | PENDING: implementation and behavioral tests |
| time.timezone | time.timezone | LOCAL | string | Asia/Kolkata | IANA zone; legacy validates nonempty only | existing if named, otherwise planned | config_manager.py node_configs; firmware NTP currently UTC | existing if named, otherwise planned | config_manager.py node_configs; firmware NTP currently UTC | partial | PENDING: implementation and behavioral tests |
| time.sync enabled | time.sync_enabled | LOCAL | boolean | true | true/false | existing if named, otherwise planned | config_manager.py node_configs; firmware not synchronized | existing if named, otherwise planned | config_manager.py node_configs; firmware not synchronized | partial | PENDING: implementation and behavioral tests |
| watchdog.enabled | watchdog.enabled | LOCAL | boolean | true | true/false | existing if named, otherwise planned | Gateway node_configs only; ESP32 watchdog always started | existing if named, otherwise planned | Gateway node_configs only; ESP32 watchdog always started | partial | PENDING: implementation and behavioral tests |
| watchdog.timeout s | watchdog.timeout_s | LOCAL | number | 60 | legacy 1..86400; ESP32 fixed 10 seconds | existing if named, otherwise planned | Gateway config_manager.py; main.cpp differs intentionally | existing if named, otherwise planned | Gateway config_manager.py; main.cpp differs intentionally | partial | PENDING: implementation and behavioral tests |
| mesh.uplink threshold | mesh.uplink_threshold | LOCAL | number | 30 | 0..100 percent | existing if named, otherwise planned | mesh_manager.py RAM; no physical adapter | existing if named, otherwise planned | mesh_manager.py RAM; no physical adapter | partial | PENDING: implementation and behavioral tests |
| mesh.downlink threshold | mesh.downlink_threshold | LOCAL | number | 30 | 0..100 percent | existing if named, otherwise planned | mesh_manager.py RAM | existing if named, otherwise planned | mesh_manager.py RAM | partial | PENDING: implementation and behavioral tests |
| mesh.measurement window | mesh.measurement_window | LOCAL | integer | 20 | 1..1000; no cross-device write | existing if named, otherwise planned | mesh_manager.py RAM | existing if named, otherwise planned | mesh_manager.py RAM | partial | PENDING: implementation and behavioral tests |
| command.timeout seconds | command.timeout_seconds | LOCAL | integer | 30 | 1..3600, overall operation deadline; NOT firmware ACK timeout | existing if named, otherwise planned | command_manager.py commands | existing if named, otherwise planned | command_manager.py commands | partial | PENDING: implementation and behavioral tests |
| command.max retries | command.max_retries | LOCAL | integer | 3 | 0..10; operation retry budget distinct from link retries | existing if named, otherwise planned | command_manager.py commands | existing if named, otherwise planned | command_manager.py commands | partial | PENDING: implementation and behavioral tests |
| command.priority | command.priority | LOCAL | integer | 1 | 1..10 | existing if named, otherwise planned | command_manager.py commands | existing if named, otherwise planned | command_manager.py commands | partial | PENDING: implementation and behavioral tests |
| offline buffer limit | offline_buffer_limit | LOCAL | integer | 12 | fixed pending slots in firmware; reject new on full; no reboot durability | existing if named, otherwise planned | network_service.cpp | existing if named, otherwise planned | network_service.cpp | partial | PENDING: implementation and behavioral tests |
| sensor.sample interval ms | sensor.sample_interval_ms | LOCAL | integer | 2000 | fixed DHT task rate, distinct from telemetry_seconds | existing if named, otherwise planned | sensor_manager.cpp | existing if named, otherwise planned | sensor_manager.cpp | partial | PENDING: implementation and behavioral tests |
| chat.message text | chat.message_text | LOCAL | string | NONE | 1..500 characters and <=2000 UTF-8 bytes on MQTT | existing if named, otherwise planned | chat_manager.py existing storage-only chat | existing if named, otherwise planned | chat_manager.py existing storage-only chat | partial | PENDING: implementation and behavioral tests |
| schema version | schema_version | SHARED | integer | 1 | exactly 1 for new MQTT envelope; not legacy protocol_version | existing if named, otherwise planned | new MQTT boundary | existing if named, otherwise planned | new MQTT boundary | partial | PENDING: implementation and behavioral tests |
| shared revision | shared_revision | SHARED | integer | 0 | 0..4294967295; agreed shared snapshot revision | existing if named, otherwise planned | planned synchronization metadata | existing if named, otherwise planned | planned synchronization metadata | missing | PENDING: implementation and behavioral tests |
| secret revision | secret_revision | LOCAL | integer | 0 | increments on local credential replacement; outside profile | existing if named, otherwise planned | planned secret metadata | existing if named, otherwise planned | planned secret metadata | missing | PENDING: implementation and behavioral tests |
| config digest | config_digest | RUNTIME | string | NONE | 64 lowercase SHA-256 hex or unavailable | existing if named, otherwise planned | planned comparison | existing if named, otherwise planned | planned comparison | missing | PENDING: implementation and behavioral tests |
| comparison.status | comparison.status | RUNTIME | enum | UNKNOWN | UNKNOWN/MATCH/MISMATCH | existing if named, otherwise planned | planned comparison | existing if named, otherwise planned | planned comparison | missing | PENDING: implementation and behavioral tests |
| comparison.fields | comparison.fields | RUNTIME | array | [] | nonsecret differing canonical paths only | existing if named, otherwise planned | planned comparison | existing if named, otherwise planned | planned comparison | missing | PENDING: implementation and behavioral tests |
| switch.transaction id | switch.transaction_id | RUNTIME | string | NONE | UUIDv4; durable transaction metadata | existing if named, otherwise planned | planned switch service | existing if named, otherwise planned | planned switch service | missing | PENDING: implementation and behavioral tests |
| switch.state | switch.state | RUNTIME | enum | IDLE | state registry below | existing if named, otherwise planned | planned switch service | existing if named, otherwise planned | planned switch service | missing | PENDING: implementation and behavioral tests |
| switch.deadline | switch.deadline | RUNTIME | integer | NONE | UTC seconds; max 120 s transaction | existing if named, otherwise planned | planned switch service | existing if named, otherwise planned | planned switch service | missing | PENDING: implementation and behavioral tests |
| mqtt connection | mqtt_connection | RUNTIME | enum | DISCONNECTED | DISCONNECTED/RECONNECTING/CONNECTED/DEGRADED/FAILED | existing if named, otherwise planned | transport worker | existing if named, otherwise planned | transport worker | partial | PENDING: implementation and behavioral tests |
| last seen | last_seen | RUNTIME | timestamp | NONE | server receive time authoritative, UTC for new payloads | existing if named, otherwise planned | nodes.last_seen | existing if named, otherwise planned | nodes.last_seen | partial | PENDING: implementation and behavioral tests |
| mqtt reconnect count | mqtt_reconnect_count | RUNTIME | integer | 0 | nonnegative; runtime only | existing if named, otherwise planned | planned MQTT service | existing if named, otherwise planned | planned MQTT service | missing | PENDING: implementation and behavioral tests |
| mqtt last error | mqtt_last_error | RUNTIME | enum | NONE | safe error category; never exception or credentials | existing if named, otherwise planned | planned MQTT service | existing if named, otherwise planned | planned MQTT service | missing | PENDING: implementation and behavioral tests |

| mesh.max hops | mesh.max_hops | LOCAL | integer | 5 | 1..10; legacy mesh limit, NOT firmware v1 limit | existing status or unavailable | no active radio routing consumer | existing relevant page | mesh_manager.py RAM via communication routes | partial | PENDING: cross-device behavior |
| mesh.retry count | mesh.retry_count | LOCAL | integer | 3 | 0..10; legacy mesh budget, NOT firmware link retry_count | existing status or unavailable | no active radio routing consumer | existing relevant page | mesh_manager.py RAM via communication routes | partial | PENDING: cross-device behavior |
| mesh.route timeout seconds | mesh.route_timeout_seconds | LOCAL | integer | 60 | integer >=1; legacy has no finite upper bound | existing status or unavailable | no active radio routing consumer | existing relevant page | mesh_manager.py RAM via communication routes | partial | PENDING: cross-device behavior |
| sensor.sensor id | sensor.sensor_id | SHARED | string | NONE | existing sensors identity; device assignment required | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.parameter id | sensor.parameter_id | SHARED | string | NONE | unique within device; existing sensor_parameters identity | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.sensor type | sensor.sensor_type | SHARED | string | DHT11 when enabled | firmware supports only actual DHT11 acquisition; other Gateway definitions are not firmware support | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.parameter name | sensor.parameter_name | LOCAL | string | NONE | existing display label; sensor_manager validation | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.parameter type | sensor.parameter_type | SHARED | string | NONE | existing parameter definition, not inferred hardware | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.data type | sensor.data_type | SHARED | string | NONE | existing parameter data type; reject invalid/nonfinite measurements | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.unit | sensor.unit | SHARED | string | NONE | use enrolled parameter units, no invented values | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.interval ms | sensor.interval_ms | LOCAL | integer | 2000 | Gateway sensor interval does not reconfigure fixed firmware task | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.decimal places | sensor.decimal_places | LOCAL | integer | 2 | display precision, existing sensor_manager validation | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.min value | sensor.min_value | LOCAL | number/null | NONE | display/range definition; no hardware calibration implied | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.max value | sensor.max_value | LOCAL | number/null | NONE | must agree with lower bound where configured | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.alarm enabled | sensor.alarm_enabled | LOCAL | boolean | false | Gateway alarm behavior; no physical control | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.low alarm | sensor.low_alarm | LOCAL | number/null | NONE | existing alarm threshold | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.high alarm | sensor.high_alarm | LOCAL | number/null | NONE | existing alarm threshold | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.display enabled | sensor.display_enabled | LOCAL | boolean | true | Gateway cards only | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| sensor.graph enabled | sensor.graph_enabled | LOCAL | boolean | false | Gateway graphs only | existing status or unavailable | sensor_manager.cpp fixed DHT fields; no generic sensor configuration | existing relevant page | sensor_manager.py / sensors and sensor_parameters tables | partial | PENDING: cross-device behavior |
| measurement value | measurement_value | RUNTIME | number | NONE | finite JSON number; absent on sensor failure | existing status or unavailable | sensor_manager.cpp | existing relevant page | telemetry_manager.py telemetry_values | partial | PENDING: cross-device behavior |
| sample timestamp ms | sample_timestamp_ms | RUNTIME | integer | NONE | monotonic milliseconds, not UTC | existing status or unavailable | sensor_manager.cpp | existing relevant page | device_api.py ingestion | partial | PENDING: cross-device behavior |
| timestamp | timestamp | RUNTIME | integer | NONE | UTC seconds; zero only for allowed unsynchronized status/telemetry | existing status or unavailable | protocol.cpp | existing relevant page | device_api.py validation; receive time authoritative | partial | PENDING: cross-device behavior |
| message id | message_id | RUNTIME | string | NONE | 1..48 safe ID; stable on retry | existing status or unavailable | protocol.cpp/network_service.cpp | existing relevant page | device_receipts | partial | PENDING: cross-device behavior |
| sequence number | sequence_number | RUNTIME | integer | NONE | uint32; sender boot sequence | existing status or unavailable | protocol.cpp | existing relevant page | device_api.py | partial | PENDING: cross-device behavior |
| correlation id | correlation_id | RUNTIME | string | NONE | empty or safe ID | existing status or unavailable | protocol.cpp | existing relevant page | device_api.py/commands | partial | PENDING: cross-device behavior |
| command id | command_id | RUNTIME | string | NONE | safe ID; no duplicate execution for same validated request | existing status or unavailable | network_service.cpp | existing relevant page | commands.command_id | partial | PENDING: cross-device behavior |
| command state | command_state | RUNTIME | enum | NONE | ACK receipt differs from completed execution | existing status or unavailable | network_service.cpp | existing relevant page | command_manager.py state machine | partial | PENDING: cross-device behavior |
| sensor status | sensor_status | RUNTIME | enum | NONE | actual driver state; no fake data | existing status or unavailable | sensor_manager.cpp | existing relevant page | nodes.latest_status | partial | PENDING: cross-device behavior |
| last error | last_error | RUNTIME | enum | NONE | safe category; no secret/raw payload | existing status or unavailable | transport_manager.cpp | existing relevant page | planned MQTT service | partial | PENDING: cross-device behavior |
| queue length | queue_length | RUNTIME | integer | NONE | bounded; actual occupancy | existing status or unavailable | network_service.cpp | existing relevant page | communication_manager.py; distinct server queue | partial | PENDING: cross-device behavior |
| uptime s | uptime_s | RUNTIME | integer | NONE | monotonic seconds | existing status or unavailable | network_service.cpp | existing relevant page | nodes.latest_status | partial | PENDING: cross-device behavior |

## Legacy broker migration boundary

| Legacy key (not canonical) | Canonical profile field |
| --- | --- |
| mqtt_host | host |
| mqtt_port | port |
| mqtt_tls | tls |
| mqtt_user | username |
| mqtt_password | password |
| mqtt_ca | ca_cert |
| mqtt_keepalive | keepalive_s |

Only a one-time migration reader may consume those legacy keys. New profile writes must use the 15 exact canonical names. mqtt_enabled stays outside the profile. Legacy HTTP API must reject direct active-broker writes with a staged-switch-required error.

## Database declarations: backend/database.py

### node_configs

```sql
node_id TEXT PRIMARY KEY,
            config_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
```

### chat_conversations

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            conversation_id TEXT UNIQUE NOT NULL,

            node_a TEXT NOT NULL,

            node_b TEXT NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            UNIQUE(node_a, node_b)
```

### chat_messages

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            message_id TEXT UNIQUE NOT NULL,

            conversation_id TEXT NOT NULL,

            sender_node_id TEXT NOT NULL,

            receiver_node_id TEXT NOT NULL,

            message_text TEXT NOT NULL,

            status TEXT DEFAULT 'SENT',

            created_at TEXT NOT NULL,

            sent_at TEXT,

            delivered_at TEXT,

            seen_at TEXT,

            packet_id TEXT,

            FOREIGN KEY (
                conversation_id
            )
            REFERENCES chat_conversations(
                conversation_id
            )
```

### ui_dashboards

```sql
id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            layout_json TEXT NOT NULL,

            updated_at TEXT NOT NULL
```

### nodes

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            mcu_family TEXT,

            mcu_model TEXT,

            hardware_revision TEXT,

            firmware_version TEXT,

            communication_type TEXT,

            communication_config TEXT,

            node_address TEXT,

            enabled INTEGER DEFAULT 1,

            status TEXT DEFAULT 'offline',

            last_seen TEXT,

            created_at TEXT,

            updated_at TEXT
```

### sensors

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            sensor_id TEXT NOT NULL,

            sensor_type TEXT NOT NULL,

            sensor_name TEXT,

            interface_type TEXT,

            gpio INTEGER,

            unit TEXT,

            interval_ms INTEGER DEFAULT 2000,

            enabled INTEGER DEFAULT 1,

            created_at TEXT,

            updated_at TEXT,

            UNIQUE(node_id, sensor_id)
```

### sensor_parameters

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            parameter_id TEXT NOT NULL,

            sensor_id TEXT,

            parameter_name TEXT NOT NULL,

            parameter_type TEXT NOT NULL,

            data_type TEXT NOT NULL,

            unit TEXT DEFAULT "",

            description TEXT DEFAULT "",

            enabled INTEGER DEFAULT 1,

            display_enabled INTEGER DEFAULT 1,

            graph_enabled INTEGER DEFAULT 0,

            decimal_places INTEGER DEFAULT 2,

            min_value REAL,

            max_value REAL,

            alarm_enabled INTEGER DEFAULT 0,

            low_alarm REAL,

            high_alarm REAL,

            created_at TEXT,

            updated_at TEXT,

            UNIQUE(node_id, parameter_id)
```

### sensor_graphs

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            parameter_id TEXT NOT NULL,

            graph_type TEXT DEFAULT 'line',

            time_range TEXT DEFAULT '1h',

            auto_scale INTEGER DEFAULT 1,

            y_min REAL,

            y_max REAL,

            show_grid INTEGER DEFAULT 1,

            show_legend INTEGER DEFAULT 1,

            show_points INTEGER DEFAULT 1,

            smooth_line INTEGER DEFAULT 0,

            animation_enabled INTEGER DEFAULT 1,

            update_interval_ms INTEGER DEFAULT 2000,

            max_points INTEGER DEFAULT 300,

            created_at TEXT,

            updated_at TEXT,

            UNIQUE(node_id, parameter_id)
```

### telemetry_values

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            parameter_id TEXT NOT NULL,

            timestamp TEXT NOT NULL,

            value REAL,

            text_value TEXT,

            data_type TEXT,

            quality TEXT DEFAULT 'GOOD',

            status TEXT DEFAULT 'NORMAL',

            source TEXT DEFAULT 'telemetry'
```

### commands

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            command_id TEXT UNIQUE NOT NULL,

            node_id TEXT NOT NULL,

            command_type TEXT NOT NULL,

            payload TEXT,

            state TEXT DEFAULT 'QUEUED' NOT NULL,

            priority INTEGER DEFAULT 1,

            retry_count INTEGER DEFAULT 0,

            max_retries INTEGER DEFAULT 3,

            timeout_seconds INTEGER DEFAULT 30,

            created_at TEXT NOT NULL,

            sent_at TEXT,

            ack_at TEXT,

            executing_at TEXT,

            response_at TEXT,

            ack_status TEXT,

            ack_message TEXT,

            timeout_at TEXT,

            completed_at TEXT,

            cancelled_at TEXT,

            error TEXT,

            result TEXT,

            updated_at TEXT NOT NULL
```

### command_events

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id TEXT UNIQUE NOT NULL,

            command_id TEXT NOT NULL,

            node_id TEXT NOT NULL,

            event_type TEXT NOT NULL,

            state TEXT NOT NULL,

            details TEXT,

            error TEXT,

            created_at TEXT NOT NULL
```

### logs

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,

            severity TEXT DEFAULT 'info',

            source TEXT DEFAULT 'SYSTEM',

            message TEXT NOT NULL,

            node_id TEXT
```

### telemetry

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT,

            timestamp TEXT,

            temperature REAL,

            humidity REAL,

            battery_voltage REAL,

            battery_percent REAL,

            current_ma REAL,

            power_mw REAL,

            rssi REAL,

            snr REAL,

            packets_tx INTEGER,

            packets_rx INTEGER
```

### firmware_releases

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            release_id TEXT UNIQUE NOT NULL,

            version TEXT NOT NULL,

            build INTEGER NOT NULL,

            hardware_family TEXT NOT NULL,

            hardware_model TEXT NOT NULL,

            hardware_revision TEXT NOT NULL,

            filename TEXT NOT NULL,

            file_size INTEGER NOT NULL,

            sha256 TEXT NOT NULL,

            signature TEXT,

            channel TEXT DEFAULT 'stable',

            release_notes TEXT DEFAULT '',

            minimum_bootloader TEXT,

            security_version INTEGER DEFAULT 0,

            mandatory INTEGER DEFAULT 0,

            status TEXT DEFAULT 'DRAFT',

            created_at TEXT NOT NULL,

            approved_at TEXT,

            retired_at TEXT,

            revoked_at TEXT
```

### device_firmware

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT UNIQUE NOT NULL,

            hardware_family TEXT,

            hardware_model TEXT,

            hardware_revision TEXT,

            current_version TEXT,

            current_build INTEGER DEFAULT 0,

            target_release_id TEXT,

            target_version TEXT,

            target_build INTEGER,

            ota_state TEXT DEFAULT 'IDLE',

            channel TEXT DEFAULT 'stable',

            last_check_at TEXT,

            last_update_at TEXT,

            rollback_release_id TEXT,

            failure_count INTEGER DEFAULT 0,

            last_error TEXT,

            updated_at TEXT NOT NULL
```

### firmware_update_jobs

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_id TEXT UNIQUE NOT NULL,

            node_id TEXT NOT NULL,

            release_id TEXT NOT NULL,

            from_version TEXT,

            from_build INTEGER,

            target_version TEXT NOT NULL,

            target_build INTEGER NOT NULL,

            state TEXT DEFAULT 'APPROVED',

            progress INTEGER DEFAULT 0,

            authorized INTEGER DEFAULT 0,

            started_at TEXT,

            completed_at TEXT,

            result TEXT,

            error TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL
```

### firmware_update_events

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id TEXT UNIQUE NOT NULL,

            job_id TEXT,

            node_id TEXT,

            release_id TEXT,

            event_type TEXT NOT NULL,

            state TEXT,

            progress INTEGER,

            message TEXT,

            error TEXT,

            created_at TEXT NOT NULL
```

Storage: data/gateway.db except accounts in data/accounts.sqlite3. Raw records and credential hashes were not inspected. Table field names remain database-local; device_api is the canonical bridge boundary.

## Database declarations: backend/account_settings.py

### accounts

```sql
id INTEGER PRIMARY KEY, username TEXT UNIQUE COLLATE NOCASE NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL, password_hash TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1
```

Storage: data/gateway.db except accounts in data/accounts.sqlite3. Raw records and credential hashes were not inspected. Table field names remain database-local; device_api is the canonical bridge boundary.

## Database declarations: backend/device_api.py

### device_receipts

```sql
source_id TEXT NOT NULL,message_id TEXT NOT NULL,fingerprint TEXT NOT NULL,received_at TEXT NOT NULL,PRIMARY KEY(source_id,message_id)
```

Storage: data/gateway.db except accounts in data/accounts.sqlite3. Raw records and credential hashes were not inspected. Table field names remain database-local; device_api is the canonical bridge boundary.

## Existing Gateway route declarations

| Source | Handler | Methods | Route |
| --- | --- | --- | --- |
| backend/account_settings.py | page | GET | /accounts |
| backend/account_settings.py | sign_in | POST | /api/accounts/sign-in |
| backend/account_settings.py | listing | GET | /api/accounts |
| backend/account_settings.py | mutate | POST | /api/accounts |
| backend/account_settings.py | mutate | PATCH,DELETE | /api/accounts/<int:account_id> |
| backend/device_api.py | exchange | POST | /api/v1/device/<operation> |
| backend/device_api.py | devices | GET,POST | /api/v1/devices |
| backend/device_api.py | rotate | POST | /api/v1/devices/<identity>/rotate-token |
| backend/device_api.py | commands | GET,POST | /api/v1/commands |
| backend/device_api.py | configuration | GET,POST | /api/v1/devices/<identity>/config |
| backend/device_api.py | status | GET | /api/v1/devices/<identity>/status |
| backend/device_api.py | diagnostics | GET | /api/v1/devices/<identity>/diagnostics |
| backend/sensor_widgets.py | catalog | GET | /api/sensor-catalog |
| backend/server.py | login | GET,POST | /login |
| backend/server.py | logout | GET | /logout |
| backend/server.py | api_auth_login | POST | /api/auth/login |
| backend/server.py | api_auth_logout | POST | /api/auth/logout |
| backend/server.py | api_auth_status | GET | /api/auth/status |
| backend/server.py | dashboard | GET | / |
| backend/server.py | system_overview | GET | /system-overview |
| backend/server.py | nodes_page | GET | /nodes |
| backend/server.py | sensors_page | GET | /sensors |
| backend/server.py | communication_page | GET | /communication |
| backend/server.py | chat_page | GET | /chat |
| backend/server.py | system_page | GET | /system |
| backend/server.py | logs_page | GET | /logs |
| backend/server.py | firmware_page | GET | /firmware |
| backend/server.py | command_center_page | GET | /command-center |
| backend/server.py | api_firmware_releases | GET | /api/firmware/releases |
| backend/server.py | api_create_firmware_release | POST | /api/firmware/releases |
| backend/server.py | api_firmware_release | GET | /api/firmware/releases/<release_id> |
| backend/server.py | api_firmware_release_status | POST | /api/firmware/releases/<release_id>/status |
| backend/server.py | api_firmware_devices | GET | /api/firmware/devices |
| backend/server.py | api_firmware_device | GET | /api/firmware/devices/<node_id> |
| backend/server.py | api_firmware_check | POST | /api/firmware/check |
| backend/server.py | api_firmware_update | POST | /api/firmware/update |
| backend/server.py | api_firmware_jobs | GET | /api/firmware/jobs |
| backend/server.py | api_firmware_job | GET | /api/firmware/jobs/<job_id> |
| backend/server.py | api_firmware_job_state | POST | /api/firmware/jobs/<job_id>/state |
| backend/server.py | api_firmware_device_check | POST | /api/firmware/device/<node_id>/check |
| backend/server.py | api_firmware_download | GET | /api/firmware/download/<release_id> |
| backend/server.py | api_firmware_config_get | GET | /api/firmware/config |
| backend/server.py | api_firmware_config_put | PUT | /api/firmware/config |
| backend/server.py | api_create_command | POST | /api/commands |
| backend/server.py | api_list_commands | GET | /api/commands |
| backend/server.py | api_get_command | GET | /api/commands/<command_id> |
| backend/server.py | api_get_node_commands | GET | /api/commands/node/<node_id> |
| backend/server.py | api_update_command_state | POST | /api/commands/<command_id>/state |
| backend/server.py | api_cancel_command | POST | /api/commands/<command_id>/cancel |
| backend/server.py | api_timeout_command | POST | /api/commands/<command_id>/timeout |
| backend/server.py | api_command_ack | POST | /api/commands/<command_id>/ack |
| backend/server.py | api_command_execute | POST | /api/commands/<command_id>/execute |
| backend/server.py | api_command_response | POST | /api/commands/<command_id>/response |
| backend/server.py | api_command_events | GET | /api/commands/<command_id>/events |
| backend/server.py | api_command_retry | POST | /api/commands/<command_id>/retry |
| backend/server.py | get_logs | GET | /api/logs |
| backend/server.py | status | GET | /api/status |
| backend/server.py | api_live_snapshot | GET | /api/live/snapshot |
| backend/server.py | api_get_ui_dashboards | GET | /api/ui/dashboards |
| backend/server.py | api_get_ui_dashboard | GET | /api/ui/dashboards/<dashboard_id> |
| backend/server.py | api_put_ui_dashboard | PUT | /api/ui/dashboards/<dashboard_id> |
| backend/server.py | api_delete_ui_dashboard | DELETE | /api/ui/dashboards/<dashboard_id> |
| backend/server.py | api_get_nodes | GET | /api/nodes |
| backend/server.py | api_get_node | GET | /api/nodes/<node_id> |
| backend/server.py | api_add_node | POST | /api/nodes |
| backend/server.py | api_update_node | PUT | /api/nodes/<node_id> |
| backend/server.py | api_delete_node | DELETE | /api/nodes/<node_id> |
| backend/server.py | api_enable_node | POST | /api/nodes/<node_id>/enable |
| backend/server.py | api_get_node_config | GET | /api/nodes/<node_id>/config |
| backend/server.py | api_save_node_config | PUT | /api/nodes/<node_id>/config |
| backend/server.py | api_reset_node_config | POST | /api/nodes/<node_id>/config/reset |
| backend/server.py | api_system_reboot | POST | /api/system/reboot |
| backend/server.py | api_system_factory_reset | POST | /api/system/factory-reset |
| backend/server.py | api_get_parameters | GET | /api/nodes/<node_id>/parameters |
| backend/server.py | api_add_parameter | POST | /api/nodes/<node_id>/parameters |
| backend/server.py | api_get_parameter | GET | /api/nodes/<node_id>/parameters/<parameter_id> |
| backend/server.py | api_update_parameter | PUT | /api/nodes/<node_id>/parameters/<parameter_id> |
| backend/server.py | api_delete_parameter | DELETE | /api/nodes/<node_id>/parameters/<parameter_id> |
| backend/server.py | api_enable_parameter | POST | /api/nodes/<node_id>/parameters/<parameter_id>/enable |
| backend/server.py | api_default_parameters | GET | /api/parameters/defaults |
| backend/server.py | api_get_graph | GET | /api/nodes/<node_id>/parameters/<parameter_id>/graph |
| backend/server.py | api_save_graph | PUT | /api/nodes/<node_id>/parameters/<parameter_id>/graph |
| backend/server.py | api_save_telemetry | POST | /api/telemetry |
| backend/server.py | api_latest_parameters | GET | /api/nodes/<node_id>/parameters/latest |
| backend/server.py | api_all_parameter_statistics | GET | /api/nodes/<node_id>/parameters/statistics |
| backend/server.py | api_parameter_statistics | GET | /api/nodes/<node_id>/parameters/<parameter_id>/statistics |
| backend/server.py | api_parameter_history | GET | /api/nodes/<node_id>/telemetry/<parameter_id> |
| backend/server.py | api_compare_telemetry | GET | /api/nodes/<node_id>/telemetry/compare |
| backend/server.py | api_communication_status | GET | /api/communication/status |
| backend/server.py | api_communication_mesh | GET | /api/communication/mesh |
| backend/server.py | api_communication_settings | GET | /api/communication/settings |
| backend/server.py | api_update_communication_settings | PUT | /api/communication/settings |
| backend/server.py | api_set_communication_master | PUT | /api/communication/master |
| backend/server.py | api_get_communication_master | GET | /api/communication/master |
| backend/server.py | api_get_gateway_connection | GET | /api/communication/gateway |
| backend/server.py | api_update_gateway_connection | PUT | /api/communication/gateway |
| backend/server.py | api_register_mesh_node | POST | /api/communication/mesh/nodes |
| backend/server.py | api_remove_mesh_node | DELETE | /api/communication/mesh/nodes/<node_id> |
| backend/server.py | api_update_mesh_link | POST | /api/communication/mesh/link |
| backend/server.py | api_get_mesh_neighbors | GET | /api/communication/mesh/<node_id>/neighbors |
| backend/server.py | api_select_communication_route | GET | /api/communication/route |
| backend/server.py | api_communication_send | POST | /api/communication/send |
| backend/server.py | api_communication_receive | POST | /api/communication/receive |
| backend/server.py | api_communication_statistics | GET | /api/communication/statistics |
| backend/server.py | api_communication_outgoing_queue | GET | /api/communication/queue/outgoing |
| backend/server.py | api_communication_incoming_queue | GET | /api/communication/queue/incoming |
| backend/server.py | api_communication_clear_queues | POST | /api/communication/queue/clear |
| backend/server.py | api_chat_users | GET | /api/chat/users |
| backend/server.py | api_chat_conversations | GET | /api/chat/conversations |
| backend/server.py | api_chat_messages | GET | /api/chat/messages |
| backend/server.py | api_chat_send_message | POST | /api/chat/messages |
| backend/server.py | api_chat_get_message | GET | /api/chat/messages/<message_id> |
| backend/server.py | api_chat_mark_delivered | POST | /api/chat/messages/<message_id>/delivered |
| backend/server.py | api_chat_mark_seen | POST | /api/chat/messages/<message_id>/seen |
