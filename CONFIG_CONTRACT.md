# Shared configuration contract

Version: 1.0.1
Schema version: 1
Date: 2026-10-17
Authority: latest MASTER IMPLEMENTATION PROMPT, Sections 2, 5, 6, 8, 9, 12, 15 and 21.
State: normative software contract; implementation and live acceptance are separate gates.
Authoritative edit location: firmware repository CONFIG_CONTRACT.md. Copy entire UTF-8/no-BOM/LF file to Gateway, then verify SHA-256. Never independently edit the copy.

## Scope and precedence
Firmware: D:/esp32 selva/ESP32_LoRa_ESP32_Firmware (not a Git checkout).
Gateway: D:/esp32 selva/ESP32_LoRa_Project (main, existing uncommitted Part 1 changes).
Part B defines MQTT/profile/security/message semantics. Part A owns ESP32 layout.
Roles are MASTER and NODE. Gateway server is a participant, not a third device role.
Old UI label Slave maps to NODE only at the adapter boundary. nodes.node_id maps to
device_id, nodes.device_role to role, nodes.name to device_name. Existing route/DB
names remain compatibility interfaces; no duplicate editable canonical fields.

E220 remains disabled; preserve src/communication/lora_transport.cpp and both
existing packet codecs unchanged. Reserved settings are not evidence of radio support.
Gateway packet_manager.py numeric types/180-byte maximum/TTL<=10 and firmware
protocol.cpp string types/4096-byte maximum/TTL<=15 are distinct existing codecs.
The new MQTT bridge uses device_api's v1 firmware-compatible codec, not the legacy
180-byte codec. No claim of interoperability between the two LoRa codecs.

Current ESP32 /mqtt does NOT exist; add it, do not claim to preserve an existing page.
Existing routes remain available. Do not alter Gateway red header CSS or Private Chat layout.
No hardware flashing, partition changes, radio enablement or eFuse changes are implicit.

## Inventory and field semantics
The complete audited configuration field table follows later in this document.
The accompanying docs/GATE0_SETTINGS_INVENTORY.md records database declarations
and all discovered static Gateway route declarations. Table entries describe BOTH
current limitations and the normative target; existing code is not assumed conformant.
Every DeviceConfig member is inventoried, including reserved interfaces and legacy broker aliases.
All sizes below are UTF-8 bytes unless explicitly called characters. Integers reject booleans,
floats, numeric strings and out-of-range values. Unknown properties are rejected.
Blank/masked/missing secrets preserve stored values. Missing nonsecret required fields
in a full import are rejected; PATCH validates the complete merged candidate atomically.

## Canonical MQTT profile
Exactly these 15 keys, no metadata inside the object:
profile_name, provider, host, port, mqtt_version, tls, ca_cert, username, password,
client_id, keepalive_s, timeout_s, qos_default, topic_prefix, gateway_id.

The table specifies bounds/defaults. Provider values: EMQX/HIVEMQ/MOSQUITTO/CUSTOM.
MQTT 3.1.1 only; QoS 1 only; TLS true only. No fallback to plaintext or unverified TLS.
CA bundles are bounded PEM certificate input, never private keys; parse every certificate.
Peer hostname and certificate chain must be verified during connection.
Clock synchronization is necessary before time-validating certificates on ESP32.
No profile becomes operational merely because it validates syntactically.
New client_id has no automatic global constant; commissioning requires a unique value.
The supplied EMQX hostname is an operator hint, not verified active configuration.
No active broker profile was confirmed from source; host defaults to NONE.
Legacy environment values, when present, are migration inputs, never defaults to invent.
Do not read/print actual process credentials in reports.

Recoverable MQTT/Wi-Fi credentials cannot be hashed like login passwords.
Login credentials use salted password hashing. ESP32 Preferences in the inspected
build has no configured NVS encryption; physical chip eFuse security state is UNVERIFIED.
Do not claim flash encryption. Gateway storage protections must be assessed before
storing new recoverable secrets; do not put encryption keys next to ciphertext and
claim physical compromise protection. Secret fields are write-only; responses omit
them and expose presence booleans outside profile under secret_state. Fixed UI mask
is eight asterisks; blank/mask is never a replacement password. No password digest
is exposed for comparison. Provisioning logs that print passwords must be removed.
Existing bench override must not override a newly established secure credential.

## Storage, migration, revisions and exports
Firmware existing settings remain device/config_v1. New MQTT persistence uses one
versioned envelope under device/mqtt_v1; top-level schema_version, revision,
active, pending, previous, transaction, secret_state. Each profile uses only canonical keys.
Gateway target storage uses additive SQLite tables/transactional updates in data/gateway.db,
with recoverable secrets protected separately. Existing records/routes are retained.
Legacy mqtt_host->host, mqtt_port->port, mqtt_tls->tls, mqtt_user->username,
mqtt_password->password, mqtt_ca->ca_cert, mqtt_keepalive->keepalive_s are accepted
ONLY by a one-time migration reader. A legacy TLS-off/QoS-0 profile is not silently
activated as a verified new profile. Preserve it for rollback; report MIGRATION_REQUIRED.
Existing /api/config stays, but direct broker writes must be rejected with
STAGED_SWITCH_REQUIRED rather than replacing active settings on restart.

contract_version is document semantic version, schema_version is the wire/persistence
schema, revision is LOCAL persisted change count, shared_revision is the separately
agreed shared snapshot revision. Each is outside profile. Never conflate these with
existing protocol_version or the device configuration_revision.
Effective persisted changes increment revision (uint32; reject overflow). Repeated no-op
and duplicate requests do not. expected_revision is required on all mutations; stale
writes return 409 REVISION_CONFLICT. Secret changes increment local secret_revision.
Imports never activate a broker; they produce validated candidates. Exports omit all
secret material, secret hashes and tokens and state that secrets need separate provisioning.
Factory reset clears new MQTT state as well as existing device settings.

## Shared comparison and digest
Comparison identity is (gateway_id, master_id). Compare only equally scoped snapshots.
Shared broker fields: host, port, mqtt_version, tls, qos_default, topic_prefix, gateway_id,
and ca_cert represented as ca_fingerprints. Client_id, username, password, profile_name,
provider, keepalive_s, timeout_s and local secret_revision are deliberately excluded.
Certificate fingerprints: SHA-256 of each DER certificate, lowercase hex, sorted unique.
DNS host normalized lowercase, no trailing dot; topic/id strings case-sensitive.
For peer/device snapshots also compare role, device_id, master_id, node_address, enabled,
telemetry_seconds, heartbeat_seconds, retry_count, command_timeout_ms, max_hops and
reserved radio fields only when both report that same device and compatible capability.
Do not compare one Node's values to another Node or Master. Hardware-only/reserved
values do not prove an applied device setting. Local service/watchdog values are excluded.

Canonical digest object: {schema_version:1,shared_revision:N,values:{...}} with keys sorted
lexicographically recursively, no insignificant whitespace, ASCII field names and values
for compared strings, JSON true/false, base-10 integers, no floats/null for required values.
Missing required data yields UNKNOWN, not equality and not a silently substituted default.
Hash UTF-8 bytes using SHA-256, lowercase hex. No passwords or password hashes included.
Compare actual normalized values and shared_revision, not just digest/schema version.
Mismatch status: MISMATCH with exact message "Master config differs" and a sorted list
of differing nonsecret field paths. Unknown/unreceived peer snapshot displays UNKNOWN.
MATCH requires a validated fresh snapshot for the same participant/scope, not file presence.
Snapshots expire after 120 seconds without fresh receipt. Never overwrite either side.

## Topic registry
One builder per side: topic_prefix + '/' + gateway_id + '/' + registry suffix.
Reject any suffix absent from this table; reject wildcard IDs and invalid prefixes.
M=authorized enrolled Master, G=authorized Gateway worker. Nodes never connect directly.
User browsers do not get MQTT credentials or connect directly. QoS is 1 for every row.
All rows use envelope schema_version=1; retained status is informational only.

| message_type/suffix | Publisher | Subscriber | Retain | Payload data | Action |
|---|---|---|---|---|---|
| telemetry | M | G | false | packet | persist measurements |
| status | M | G | true allowed | packet OR connection_state LWT | liveness only |
| command | G | M | false | packet | supported command only |
| command_ack | M | G | false | packet | command receipt/result |
| config | G and M | M and G | false | control | comparison/switch/receipt only |
| events | M | G | false | packet | persist event/diagnostic |
| discovery | M | G | false | packet | refresh pre-enrolled identity |
| chat/message | G and M | M and G | false | chat | text only |
| chat/ack | G and M | M and G | false | chat_ack | delivery metadata |
| chat/status | G and M | M and G | false | chat_status | availability only |
| chat/command | G | M | false | chat_action | status/retry only |

config is deliberately bidirectional for nonsecret switch acknowledgements,
comparison snapshots and persistence receipts; this resolves the previous missing
application-ACK direction without inventing an extra topic. Ignore own-origin echoes.
Broker ACLs must enforce these directions for the specific gateway_id. Application
checks additionally enforce enrolled Master assignment and allowed operation/recipient.
Do not claim publisher authenticity from a claimed JSON sender without enforced broker ACLs.
Anonymous clients and unrestricted wildcard grants are not acceptable. ACL verification
and duplicate-client-ID tests remain live-broker acceptance requirements.

## MQTT envelope and payload validation
Maximum complete MQTT application payload: 6144 bytes; data.packet <=4096 serialized
bytes and packet.payload <=2048 UTF-8 bytes. JSON object only, depth <=8, reject duplicate
keys, nonfinite numbers, invalid UTF-8, unknown fields and unsupported schema_version.
Required envelope keys: schema_version (integer 1), message_id (safe ID 1..48),
gateway_id (profile identity), master_id (enrolled safe ID), device_id (assigned safe ID),
message_type (exact matching received topic suffix), timestamp (Unix UTC seconds,
0 allowed only for non-action status/telemetry before clock sync), data (object).
Optional: correlation_id (safe ID 1..48), configuration_revision (uint32),
expires_at (Unix seconds). Actions require timestamp>0, expires_at>timestamp,
expires_at<=timestamp+300, reject future >30s or expired. Action clocks must be valid.
message_id is stable on retry. Origin authorization and topic binding precede dispatch.

packet data is exactly {packet:<existing v1 object>}; validate with protocol.cpp/device_api.
Check embedded source/destination/origin IDs against envelope and permitted assignment.
TELEMETRY->telemetry; HELLO/HEARTBEAT/STATUS->status or discovery as registered;
COMMAND/CONFIG_GET/CONFIG_UPDATE->command; ACK/RESPONSE->command_ack;
EVENT/ALARM/DIAGNOSTIC->events. Do not route legacy packets based solely on untrusted suffix.
Safe operations: PING, GET_STATUS/STATUS, GET_TELEMETRY, GET_CONFIG, DIAGNOSTICS,
SET_TELEMETRY_INTERVAL, SET_HEARTBEAT_INTERVAL, restricted CONFIG_UPDATE.
Configuration arguments only telemetry_seconds, heartbeat_seconds, enabled; validate
the same ranges as DeviceConfig. Neither chat text nor arbitrary commands execute.

LWT status data: {connection_state:"OFFLINE"}; received time authoritative; no fake sensor data.
control data uses op enum COMPARE/SWITCH_PREPARE/SWITCH_READY/SWITCH_CONFIRM/
SWITCH_COMMITTED/SWITCH_ROLLBACK/PERSISTED/PROBE/PROBE_ACK. Each op has a strict schema:
COMPARE: snapshot (canonical digest object), digest (64 hex).
SWITCH_*: transaction_id UUIDv4, shared_revision uint32, digest 64 hex, participant
MASTER or GATEWAY; no profile/password transferred. PREPARE additionally deadline UTC.
PERSISTED: received_message_id safe ID and status PERSISTED, only after SQLite commit.
PROBE/PROBE_ACK: transaction_id UUIDv4, nonce 32 random hex, participant; no device action.
Unknown control keys/operations rejected. PROBE_ACK copies nonce and transaction_id.

chat: conversation_id 1..128 ASCII, sender_id and recipient_id safe IDs, text 1..500
characters <=2000 UTF-8 bytes. Authenticated account determines sender; cannot impersonate.
chat_ack: received_message_id, conversation_id, state from STORED/BROKER_ACCEPTED/
DELIVERED/READ/FAILED/EXPIRED plus optional safe error_code. READ only from recipient
read confirmation; stored locally never proves device delivery.
chat_status: recipient_id and state ONLINE/OFFLINE/UNKNOWN.
chat_action: conversation_id, received_message_id, action STATUS or RETRY. RETRY only
unexpired queued text. Current chat manager remains local history until adapter exists.
Legacy DELIVERED means Gateway DB storage; preserve historical records with explicit
legacy semantics instead of relabeling them as physical delivery.
New chat recipient authorization is admin/creator initially; existing broader history
access requires review before transport integration. No new user role escalation.

Dedup: unique (master_id,device_id,message_id), record content fingerprint; equal duplicate
returns prior outcome, changed content under same identity rejected. Existing receipts
persist 4096 IDs; firmware 32 RAM cache is not reboot-durable exactly-once execution.
Use idempotent setters only; no unsafe actuator commands. Application persistence receipt
clears telemetry only after commit, not MQTT PUBACK. QoS1 acceptance is separate state.

## Broker switching and protected provisioning boundary
Candidate edits never alter active or live connection. The Gateway is coordinator;
ESP32 local UI can stage a local candidate but cannot independently commit a shared switch.
States: IDLE -> PENDING -> TESTING -> READY_TO_CONFIRM -> COMMITTING -> COMMITTED.
Failure: any nonterminal state -> ROLLING_BACK -> ROLLED_BACK. Safe error outcomes
FAILED/TIMEOUT/RECOVERY_REQUIRED include a reason category without raw exceptions.
UUIDv4 transaction, expected_revision, previous active snapshot, candidate snapshot,
participant confirmations and deadline must be durable outside the profile object.
One transaction at a time; different request while busy returns 409. Same transaction
and content is idempotent; same ID different content returns conflict.

Candidate test deadline 60s, overall transaction 120s; up to 3 probe attempts, 5s apart,
within the deadline. Client connection uses bounded timeout_s; run outside HTTP handlers.
Test requires verified TLS+MQTT CONNACK+subscription acknowledgement+QoS1 PUBACK+
non-destructive nonce probe reply from the other authorized participant on candidate broker.
Connection alone is not READY_TO_CONFIRM. Keep last active profile available.
If the peer/channel/provisioning is absent, return RECOVERY_REQUIRED/COORDINATION_REQUIRED;
do not fabricate peer proof. A no-peer unit test may prove local validation, not commit.

Commit requires matching transaction/digest/shared_revision and independent peer evidence
on candidate broker. Persist coordinator decision before announcing it; peer persists
receipt and echoes COMMITTED. Missing final acknowledgement is an in-doubt transaction,
not proven atomicity: RECOVERY_REQUIRED, retain both profiles, query coordinator decision.
Never silently reverse a durably committed coordinator decision based only on timeout.
Before durable commit decision, failure/timeout rolls back to prior profile.
After restart with no trustworthy clock or undecidable commit, stop actions and show
RECOVERY_REQUIRED; do not extend deadline by reboot or guess a shared result.
Cancel/restore must validate transaction/revision; restoring after COMMITTED is a new staged
transaction. Loss of both brokers permits local recovery only through protected provisioning.
Cross-device atomic switching is PENDING until this handshake and all fault cases are tested.

Critical audited boundary: ESP32 serves plain HTTP Basic on port 80; no protected secret
provisioning channel was found. Existing Gateway outbound verified HTTPS does not provide
an encrypted browser-to-ESP32 configuration channel. Do not transmit new broker passwords
through this HTTP UI or ordinary MQTT. It may stage nonsecret candidates and report
PROTECTED_PROVISIONING_REQUIRED. Full new-credential provisioning remains PENDING until
a confidential authenticated local channel/deployment is reviewed. Do not add an insecure
fallback. Existing stored credentials may be retained for local tests without returning them.

## Reliability, resources and errors
Existing firmware transport queues: outgoing6/incoming6/results8; pending12; dedup32;
peers12. RAM-only backlog is lost on reboot, never advertised as durable.
New adapters use bounded queues and reject-new overflow with counters. No unbounded
outbox. Backoff target 1,2,4,8,16,32,60 seconds capped, jitter 0..25%; reset after stable
connection. Existing HTTP fallback is separately reported and preserved.
Safe error JSON: {ok:false,error:{code:ENUM,message:fixed-text,field:canonical-path}}.
No raw exceptions, credentials, hashes, request bodies or TLS private material in logs.
TLS_FAILED, AUTH_FAILED, DNS_FAILED, TIMEOUT, INVALID_PROFILE, REVISION_CONFLICT,
STAGED_SWITCH_REQUIRED, PROTECTED_PROVISIONING_REQUIRED, COORDINATION_REQUIRED,
QUEUE_FULL and NOT_AVAILABLE are distinguishable. No success claims from raw TCP alone.

## Gates and evidence
Gate 0 verifies definitions/inventory and identical contract bytes; it does not assert
runtime compliance. Gate 1 requires real PlatformIO build and firmware checks before
Gateway feature edits. Gate 2 requires Python regression tests. Gate 3 includes both
contract parity and real broker/hardware tests where available.
Known unavailable acceptance: E220, remote two-broker switch, secure credential provisioning,
real broker ACL/TLS/credentials, reboot-durable telemetry. Mark PENDING, never MATCH.
Do not modify partition layout to conceal application overflow; report build evidence first.

## Full canonical settings inventory

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

