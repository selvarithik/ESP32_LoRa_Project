# Shared configuration contract

Version: 1.4.0
Schema version: 1
Date: 2026-10-29
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
| dht enabled | dht_enabled | LOCAL | boolean | role builds true; legacy false | true/false | existing / grouped form; planned sections | device/config_v1 NVS; src/sensors/sensor_manager.cpp, src/web/local_web_server.cpp | not exposed; planned status/settings as relevant | no matching firmware-setting writer; do not equate legacy mesh settings | partial | PENDING: implementation and behavioral tests |
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

## Local IP extension 1 â€” contract 1.0.2 (2026-10-19)

This additive section preserves all preceding MQTT profile keys, wire schema 1,
approved topics and directions. Earlier inventory statements describe Gate 0.
Local IP uses the SAME protocol_version=1 packet already inside MQTT data.packet.
It does not replace the MQTT envelope or create alternate packet fields.

| Setting | Canonical field | Class | Type | Default | Validation / use |
|---|---|---|---|---|---|
| local IP mode | local_ip_enabled | LOCAL | boolean | false | firmware NVS, ESP32 Gateway/network group; when true local IP is selected exclusively and stored MQTT profiles are not started or changed |
| local peer credential | local_ip_token | SECRET | string | empty | 32..64 bytes, physical USB only, never GET/export/log; dedicated local-IP override, existing gateway_token fallback retained |
| Node IP route | routing_policy | LOCAL | string | MASTER_ONLY | MASTER_ONLY, DIRECT_ONLY, DIRECT_PREFERRED; firmware NVS/UI/worker; Master always uses Gateway; DIRECT_PREFERRED falls back sequentially after failure |
| listener enabled | local_ip.gateway.enabled | GATEWAY | boolean | false | Gateway local_ip_settings SQLite/UI; explicit owner enablement |
| listener bind | local_ip.gateway.bind_address | GATEWAY | IPv4 string | 127.0.0.1 | assigned private unicast or loopback IPv4; never 0.0.0.0/public/multicast/link-local; bind failure restores previous running configuration |
| listener port | local_ip.gateway.port | GATEWAY | integer | 5001 | 1024..65535; separate device-only listener; ESP32 uses existing server_host/server_port |
| listener revision | local_ip.gateway.revision | GATEWAY | uint32 | 1 | expected_revision required on settings mutations; stale rejected; overflow rejected |
| Node direct permission | local_ip.direct_allowed | GATEWAY | boolean | false | per enrolled Node, authenticated admin/creator + CSRF; separate Node credential required |

Existing server_host, server_port, server_https, gateway_ca, master_host, gateway_token,
mesh_key, wifi_dhcp/static IPv4, heartbeat_seconds, retry_count, command_timeout_ms,
message_max_age_ms, dht_enabled/dht_pin and allowed_peers_csv retain their names.
Changing public configuration persists then restarts safely. HTTP never provisions
new credentials; physical USB does. Existing active MQTT profiles/revisions/secrets
are retained. local_ip_enabled=false restores the previous transport selection.
Ethernet configuration is reserved, driver NOT_AVAILABLE; no PHY is assumed.
IP reachability through a mixed Wi-Fi/Ethernet LAN requires no packet changes.

Transport framing: HTTP/1.1 over TCP, one JSON packet per POST body, explicit
Content-Length 1..4096 bytes; Transfer-Encoding is rejected on new local exchanges.
Stream reads may fragment/combine arbitrarily; the HTTP parser delimits the body.
Firmware local peer ingress uses bounded raw chunks, rejects excess Content-Length
before collecting the body, caps assembly at 4096, and bounds chunk waits to 100 ms.
Gateway device-only listener handles one connection at a time, socket timeout 3 s,
OS listen backlog, no unbounded worker-thread pool. Reply body <=6144 bytes.
No NDJSON, unframed TCP JSON, MQTT topics or raw secrets on this listener.

Packet keys exactly: protocol_version, message_id, source, destination, origin_id,
final_destination_id, next_hop, type, ttl, timestamp, sequence_number, correlation_id,
payload, payload_length, payload_crc32. ASCII IDs 1..48 [A-Za-z0-9_.:-], optional
correlation_id empty or same ID grammar. protocol_version integer 1; TTL 1..15;
other numeric fields unsigned 32-bit integers (not bool/float/string). payload is
an encoded JSON object string <=2048 UTF-8 bytes; payload_length counts bytes;
payload_crc32 is IEEE CRC32. origin_id=source, final_destination_id=destination.
Reject duplicate JSON keys, nonfinite numbers, invalid UTF-8, nesting >8, unknown
packet fields, bad CRC/length, unknown type and unauthorized assignments.
Local Gateway receipt requires destination GATEWAY; commands use existing safe
command registry only. The existing local-IP control loop creates non-action
packets with timestamp=0 before authenticating a clock; the one-time challenge
bounds transport freshness. Once UTC exists reject >30 s future or >300 s old.
Actions and action results require a valid timestamp. Source queue expiry is
message_max_age_ms (<=300000), including offline periods; IDs/payloads stay stable.
The received packet is not re-created to change paths: direct/fallback use identical
GATEWAY destination, next_hop and source/message ID. Gateway persistent receipts
suppress equal duplicates across transports; changed content under an ID is rejected.

Authentication: Gateway GET /api/v1/device/local-challenge; peer ESP32 GET
/api/v1/local/challenge. Request header X-Device-ID identifies a provisioned peer.
Reply nonce is 32 random lowercase hex, single-use, expires at 30 monotonic seconds;
Gateway cache <=256, firmware <=8. Challenge includes unix_time and signature.
Key K is SHA256(UTF8(local_ip_token, or existing gateway_token fallback, or mesh_key for peer links)), raw 32 bytes.
HMAC-SHA256 input is UTF8(domain+'\n'+identity+'\n'+nonce+'\n') + exact body bytes.
Challenge domain LOCALIP1-TIME signs the decimal unix_time bytes. Verified Gateway
clock can initialize ESP32 UTC without NTP or Internet. Request domain LOCALIP1
signs the exact POST packet body. POST paths /api/v1/device/local-exchange (Gateway)
and /api/v1/local/exchange (peer ESP32); X-Local-Nonce and X-Local-Signature headers.
Authenticated reply domain LOCALIP1-REPLY signs exact reply body with that nonce;
header X-Local-Signature. Constant-time proof comparison. Never transmit K or token.
Dedicated local_ip_credentials.key_hash stores SHA256(K), a one-way verifier.
The MAC key is derived only from a device-specific DPAPI-protected local token file;
missing/corrupted files fail closed. The legacy device_token_hash is never used
as an automatic server-side fallback. Initial development K rows are migrated to
SHA256(K) only after validating the existing protected file, without token rotation.
Exclude verifiers and protected files from APIs/exports. Dedicated provisioning
never changes legacy device_token_hash or MQTT credentials. Shared mesh keys authorize the enrolled
trusted group, not mutually distrustful per-device identities. HMAC does not encrypt
measurements; trusted private LAN or correctly configured HTTPS is required.

Gateway authorizes enabled enrolled Masters and separately permitted Nodes with
individual token hashes; direct Nodes may only source their own packets and fetch
their own commands. Masters may relay only assigned Nodes. Unknown/revoked identities,
bad proofs/nonces, nonce replay, malformed/expired packets and queue pressure fail
closed with AUTH_FAILED/UNAUTHORIZED/INVALID_OR_EXPIRED_PACKET/QUEUE_FULL/STORAGE_FAILED.
No success receipt before SQLite commit. Successful response includes schema_version=1,
accepted=true, duplicate boolean, received_message_id, receipt=PERSISTED, commands
(at most one existing packet). Peer firmware replies receipt=QUEUED only after its
bounded queue accepts a frame; the existing later application ACK is a hop receipt,
not proof of Gateway persistence. No exactly-once promise across ESP32 power loss.
Master/Node firmware pending12, outgoing6, incoming6, results8; reject-new overflow;
retry_count<=5, bounded exponential retry (1,2,4,8 timeout multiples), source expiry.
Direct fallback never intentionally sends both paths concurrently, but an ambiguous
network failure can cause a retry via Master; persistent Gateway dedup is authoritative.
Command execution cache is RAM32; idempotent setters only. Gateway command journal
survives restart; completion requires a correlated RESPONSE, not queued/SENT/ACK.

GET /api/local-ip (admin/creator) exposes sanitized settings, counters and up to64
connection summaries; POST with expected_revision changes listener settings. POST
/api/local-ip/devices/<id> changes direct_allowed only. All mutations require CSRF.
/local-ip page is reached from System without changing the main navigation/header.
Listener stop clears nonces; reconnect needs a new challenge. Per-device last_seen,
last_error, message ID and receiver persistence remain separate from UI display.

Acceptance is recorded separately in docs/LOCAL_IP_REPORT.md. MQTT test execution
is deferred until local acceptance is reported. Missing Ethernet hardware, second
ESP32 and RF hardware are BLOCKED, never simulated physical PASS.


## Offline software completion extension 2 (2026-10-19)

Additive document version 1.1.0. MQTT schema 1, its fifteen profile fields and
approved topic builder/registry are unchanged. Existing local-IP extension 1 is
unchanged. This extension does not enable a physical radio or assert hardware tests.

| Setting | Type | Range | Default | Units | Persistence / readers | Remote change / reboot |
| wifi_dns2 | string | empty or unicast IPv4 | empty | address | device NVS; WiFi manager, device/Gateway controls | public config; reboot |
| sleep_enabled | bool | true/false | false | none | device NVS; PowerManager, device/Gateway controls | SET_SLEEP_SCHEDULE; no reboot |
| sleep_start_minute | uint16 | 0..1439 | 0 | local minute of day | device NVS; PowerManager, device/Gateway controls | SET_SLEEP_SCHEDULE; no reboot |
| sleep_duration_seconds | uint32 | 60..86400 | 3600 | seconds | device NVS; PowerManager, device/Gateway controls | SET_SLEEP_SCHEDULE; no reboot |
| sleep_days_mask | uint8 | 1..127 | 127 | Sunday bit0 through Saturday bit6 | device NVS; PowerManager, device/Gateway controls | SET_SLEEP_SCHEDULE; no reboot |
| utc_offset_minutes | int | -720..840 | 330 | minutes east of UTC | device NVS; PowerManager, device/Gateway controls | SET_SLEEP_SCHEDULE; no reboot |

Schedule is recurring fixed UTC offset, not an IANA/DST rule. A selected day's
start plus duration defines a sleep window, including midnight crossings. Active
period is the complement. Wake time is derived, never a duplicate independently
writable field. Missing trusted UTC means CLOCK_REQUIRED and no scheduled sleep.
During DRAINING no new nonessential telemetry is queued. Pending commands/transport
work and an MQTT switch defer sleep. Deep sleep disables ordinary Wi-Fi; timer
wake only. No promise of remote wake or radio power control without hardware.

See COMMAND_PROTOCOL.md and TELEMETRY_SCHEMA.md for version-1 packet and lifecycle
rules. Canonical external ACK state ACKNOWLEDGED maps the legacy SQLite state
ACK_RECEIVED without rewriting existing event history. A restart command is only
completed by a response produced after boot from its durable restart marker;
receipt/intent is not restart success. No marker means no scheduled restart.

New non-secret remote operations: GET_NETWORK, WIFI_SCAN, WIFI_RECONNECT,
GET_RADIO_STATUS, RADIO_TEST,
GET_POWER_STATUS, SET_SLEEP_SCHEDULE, RESTART. Device name updates use the existing
device_name field, never device_id. Radio test fails DRIVER_UNAVAILABLE until a
verified implementation is selected. Credentials remain
physical USB/protected-store only. Network disabling is local-only because it can
remove the only response path. Scanning and results are bounded and asynchronous.

MQTT profile catalog: up to four named saved templates per participant. Catalog
revision is independent of active MQTT revision. Saved password is write-only and
never an HTTP field; reuse the active protected secret or physical commissioning.
Selecting a saved template stages a candidate through the existing transaction;
it never writes active configuration. Deleting requires exact profile_name and
expected catalog_revision; deleting an active-named template is rejected. No topic
fields are independently editable: approved topics remain derived by the canonical
builder. Permanent worker start remains gated by ACL confirmation.


Existing wifi_dhcp/wifi_ip/wifi_subnet/wifi_gateway/wifi_dns/wifi_dns2 may be changed
through CONFIG_UPDATE with a revision check; they are non-secret. The firmware
validates the complete candidate network, persists it and reports restart_required.
The active link keeps its applied settings until explicit restart. Wi-Fi passwords,
mesh keys and broker secrets are never command arguments. DHCP is the default;
static settings require unicast host/gateway/DNS, contiguous nonzero mask and a
shared subnet without network/broadcast host addresses. Configuration recovery
keeps an invalid saved blob intact; owner commissioning repairs it explicitly.

## Sensor extension and scope amendment (2026-10-19)

MQTT profile/wire schema and topic registry remain unchanged. Dedicated sensor
packets use sensor_type DHT11, INA219 or MQ135 and a parameters object. DHT11
retains temperature (C, 0..50) and humidity (%RH, 0..100). INA219 requires
bus_voltage (V, 0..26) and shunt_voltage (mV, strictly between -320 and 320);
current (A, -320..320) and power (W, -8320..8320) appear together only when a
confirmed shunt resistance is configured. These protocol bounds are not safe
hardware load ratings. MQ135 exposes mq135_adc_raw (integer 0..4095) and
mq135_pin_mv (integer 0..3300); no ppm, calibrated gas concentration or safety
classification. Invalid sensor packets contain no parameter values. Each sensor
has independent validity/status; successful DHT does not imply INA/MQ health.

| Setting | Type | Range | Default | Used by |
| --- | --- | --- | --- | --- |
| ina219_enabled | boolean | true/false | MASTER true; SLAVE false (hardware inhibited) | ESP32 page/firmware; Gateway reported sensor status |
| ina219_address | uint8 | 64..79 | 64 (0x40) | ESP32 page/firmware; fixed SDA21/SCL22 |
| ina219_shunt_milliohms | uint16 | 0..1000; 0 unknown | 0 | ESP32 page/firmware; Gateway units derived from measurements |
| mq135_enabled | boolean | true/false | role builds true; legacy false | ESP32 page/firmware; GPIO34 requires verified voltage divider |
| mq135_warmup_seconds | uint32 | 60..604800 | 86400 | ESP32 page/firmware; conservative initial conditioning, not calibration |

New sensor enable/address changes require restart. Unknown shunt resistance
withholds current/power. Disabled MQ135 is never read. Wi-Fi and MQTT remain
independent of these sensors. BLE is removed from active scope. Four retired
BLE settings are ignored only on legacy NVS load, omitted from serialization
and rejected on public mutations. Private Chat and OTA development are excluded.

## Local connection indicators (2026-10-19)

| Setting | Type | Range | Default | Used by |
| --- | --- | --- | --- | --- |
| server_led_enabled | boolean | true/false | true | ESP32 local page, firmware NVS; GPIO2 onboard LED; no duplicate Gateway setting writer |
| server_led_active_high | boolean | true/false | true | ESP32 local page, firmware NVS; invert for active-low board variants |
| tm1637_enabled | boolean | true/false | false; inhibited in current hardware profiles | ESP32 local page, firmware NVS; MASTER only, CLK18/DIO19; current diagnostic wiring 3.3V; any 5V supply requires suitable logic-level shifting; NODE leaves pins untouched |

These settings apply on restart and do not alter MQTT profiles or wire topics.
The server indicator requires Wi-Fi plus an actual authenticated Gateway receipt
within 15 seconds. Broker connection, association and hop acceptance alone do
not qualify. The four-digit MASTER display cycles every 3 seconds through signed Wi-Fi RSSI
(dBm) and current Gateway connection duration MM:SS (capped 99:59).
Connection counts and sensor values are not shown; connection counts remain
available in runtime diagnostics only.
A connection establishment is a transition from no recent Gateway receipt to a
fresh receipt; it is not a TCP socket, data packet or sensor reading count.
No receipt / expired receipt alternates Conn and Cxxx (seconds waiting, capped
999); no Wi-Fi shows noFI. The connection duration is not server process uptime.
At startup, 8888 is a two-second segment self-test. Driver checks all TM1637
byte acknowledgements and idle line levels; ACK never proves visual health.
Display writes occur at most once/second, plus immediate state transitions.
DHT and enabled radio pin conflicts are rejected rather than sharing GPIO18/19.


## Command Center extension 3 (configuration contract 1.1.1, wire schema 1)
Existing packet fields and MQTT topic registry are unchanged. COMMAND payload is
command_id, command, arguments. ACK statuses: ACCEPTED, REJECTED, BUSY,
DUPLICATE; legacy RECEIVED remains receipt-only. RESPONSE: SUCCESS, FAILED or
UNSUPPORTED, data and execution_duration_ms. A RESPONSE never manufactures ACK.
GET_CONFIGURATION aliases GET_CONFIG; SET_CONFIGURATION aliases CONFIG_UPDATE;
REBOOT aliases RESTART. Additional read commands: GET_CAPABILITIES, GET_SENSOR_STATUS,
GET_MESH_STATUS, GET_NODE_STATUS, GET_ROUTE_INFO (unavailable routes are explicit).
SET_DEVICE_NAME uses device_name and optional expected_revision. Config fields and
ranges remain unchanged; secret updates require physical USB.
Gateway-local command policy fields: ack_timeout_seconds integer 1..60 default 5,
response_timeout_seconds integer 1..300 default timeout_seconds, expiry_seconds
integer 1..300 default 300. max_retries 0..10 bounds retransmissions. Capacity is 64
active commands. Durable SQLite scheduling survives Gateway restart. ACK stops ACK
retries and starts response deadline. Timeout/expiry means unknown execution outcome.
Retries preserve original command bytes and ID. Late results are audited as
LATE_RESPONSE without converting TIMEOUT to success. Cancel stops dispatch only;
remote cancellation is unsupported.
Identity: uppercase colon-separated station/base eFuse MAC. Existing ESP32-XXXXXXXXXXXX
IDs encode ESP.getEfuseMac() integer with reversed byte order. A reversible alias
layer preserves all enrolled IDs, keys, routing and historical database records.
SLAVE is a display alias for canonical NODE. Master/Slave builds select initial role
only; saved roles prevail. Physical LoRa remains DRIVER_UNAVAILABLE pending hardware.

Browser login extension: POST /api/auth/login/start validates anonymous session CSRF,
limits attempts and starts one bounded worker. GET /api/auth/login/result is bound
to the same session and CSRF; 202 means pending, 401 means invalid saved credentials,
200 rotates the authenticated cookie only after verification. Credential generation
changes invalidate a pending job. PBKDF2 iteration count remains 100000. Legacy
/api/auth/login remains compatible. UI request and verification deadlines are 30 s;
an abandoned completed job is reclaimed after 60 s. No password reset/default override.


## Shared E220 hardware profile extension (contract 1.2.0; logical wire schema 1)
Master/Slave images use the same source with mutually exclusive DEVICE_ROLE_MASTER
and DEVICE_ROLE_SLAVE definitions. Runtime stored roles/identities are not rewritten;
a build/stored-role mismatch disables radio/sampling until corrected by local provisioning.
Both build defaults enable DHT11 GPIO4 and raw MQ135 ADC1 GPIO34 (divider mandatory).
Master permits INA219 I2C SDA21/SCL22; Slave hard-disables INA219 even if NVS says enabled.
TM1637 is inhibited in current hardware profiles even if legacy NVS enables it. Its saved
option is preserved for a later explicitly reviewed build profile.
E220-900T22D uses UART2 RX16/TX17, M0=25/M1=26/AUX27. Radio defaults disabled until
physical commissioning. Enabling radio reads public registers 00..05 only at 9600 8N1
in mode 3, then checks stored baud/address/channel/air rate/power/fixed/LBT/RSSI settings.
No C0/C2 write or radio crypt-register read is performed. Mismatches inhibit RF and
restore initial mode. Successful explicit radio enable selects normal mode, without
rewriting module registers. AUX state, UART submission and RF completion are distinct.
Application ACK/RESPONSE alone confirms target acceptance/execution.
Logical packets and MQTT topics remain unchanged. HELLO implements discovery, COMMAND
PING plus RESPONSE implements ping/pong, EVENT/ALARM carries errors. No duplicate types.
Radio transport RV1 encodes the shared Message in a bounded MessagePack array, chunks
it into addressed authenticated fragments, adds HMAC-SHA256/128 and COBS UART framing.
Only initialized registered/allowed peers can issue application actions. Fragment headers
carry immediate sender/next-hop station MACs, transfer ID, index/count/span/length and
whole-message CRC32. HMAC is authentication; CRC only detects corruption. Two 3072-byte
assemblies and 32 completed-transfer entries are bounded; assemblies/replay entries expire
at 120 seconds. Peer/route age is governed by existing route_timeout_seconds. Relays must
use explicitly observed routes, consume TTL, preserve source/command IDs and suppress
forward duplicates. Physical multi-hop remains unverified until relay tests.
The four provider/side MQTT templates are preparation files only; no active profile,
revision, password, database or ACL changes occur. MQTT/WSS ports are documented separately;
existing transport is native TLS MQTT 8883. No WebSocket code/path is activated.

RV1 MessagePack array order is [protocol_version,type,ttl,timestamp,sequence_number,
message_id,source,destination,next_hop,origin,correlation_id,payload_object,
radio_hop_count,radio_max_hops]. Header/fragment integers are little-endian;
MessagePack follows its standard byte order. Radio-only hop metadata does not add
fields to the legacy 15-field JSON or MQTT payload. Each radio send increments hop
count; relays consume TTL and reject loops, expired routes and exhausted hop budgets.
Master/Slave builds initialize the optional MQTT client paused; only an explicitly
requested connect can start the cloud task. Slave never initializes a cloud connection.
This changes startup policy only, not stored profiles/revisions or the existing chat handlers.
Read-only radio_probe on physical USB always restores original mode and never enables RF.


## Role, sleep and transport-control extension 1.3.0 (2026-10-28)
Wire schema remains 1; broker profiles, topic registry and radio packet formats are unchanged.
One firmware image supports MASTER and NODE through persisted role. Build target names remain compatibility aliases.
Exactly 21 primary commands are exposed. Legacy aliases remain accepted for older clients but are not advertised.

| Setting | Type | Range | Default | Storage / use |
| --- | --- | --- | --- | --- |
| sleep_mode | string | DEEP, LIGHT | DEEP | NVS; ESP32/Gateway schedule forms; PowerManager |
| lora_sleep_mode | string | KEEP, DEEP | KEEP | NVS; schedule forms; E220 mode pins during ESP32 sleep |
| lora_work_mode | string | NORMAL, WOR_TX, WOR_RX | NORMAL | NVS; ESP32 radio form; E220 M1/M0 |
| lora_wor_cycle_ms | uint16 | 500..4000, multiples of 500 | 2000 | NVS; ESP32 radio form; E220 REG3 |
| lora_packet_bytes | uint16 | 64, 128, 200 | 200 | NVS; ESP32 radio form; E220 REG1; 32 unsupported by authenticated frame size |
| lora_apply_settings | bool | true/false | false | NVS; explicit local permission to write/read back public E220 registers; no key read/write |

E220 mode mapping follows manual page 11: M1/M0 00=NORMAL, 01=WOR_TX,
10=WOR_RX, 11=DEEP/configuration. Page 12 WOR_TX wording contradicts this table.
WOR settings must match on peers. No RF success or regional approval follows from configuration success.
AUX high is readiness only, never recipient ACK. SNR remains unavailable. RSSI only after actual received byte.
Sleep uses timer wake. No radio-triggered ESP32 wake is promised. LIGHT uses bounded timer chunks with worker pause and Wi-Fi suspended; DEEP restarts on wake.

Transport changes use CONFIG_UPDATE arguments exclusively:
prepare: transport_action, transaction_id, local_ip_enabled, expected_revision, timeout_seconds (30..180).
apply/confirm/cancel: transport_action, transaction_id, expected_revision.
transaction_id is 1..48 ASCII alphanumeric/hyphen/underscore. No password is sent to ESP32.
Direct remote writes of local_ip_enabled are rejected: TRANSPORT_TRANSACTION_REQUIRED.
Only authenticated Gateway-origin commands can execute transport transactions.
Gateway authorizes each action by rechecking the signed-in administrator password over HTTPS or loopback only;
password is removed before queue/persistence/logging and never forwarded. Ordinary LAN HTTP is rejected.
prepare persists PREPARED without changing transport or starting trial deadline; it expires after 10 minutes.
apply persists TRIAL plus old selection and deadline before changing runtime selection, without touching broker profile.
Device waits 3 seconds before runtime application to allow its old-path response to leave. Deadline starts on apply.
confirm requires a fresh matching-transaction PING via the selected transport and a successful Gateway receipt after apply.
Gateway checks a correlated COMPLETED PING result matching transaction and requested transport before allowing confirm.
Until confirm, reboot or deadline expiry restores old selection. Uncertain/corrupt journal fails closed into recovery.
Terminal transactions are idempotent; conflicting IDs, stale revisions and concurrent candidates are rejected.
Final commit is truthful only after device RESPONSE; Gateway submission alone remains queued/unknown.

Primary command order: PING, GET_STATUS, GET_CAPABILITIES, GET_CONFIG, GET_NETWORK,
GET_TELEMETRY, GET_SENSOR_STATUS, GET_POWER_STATUS, GET_RADIO_STATUS, GET_MESH_STATUS,
GET_NODE_STATUS, GET_ROUTE_INFO, DIAGNOSTICS, SET_DEVICE_NAME, SET_TELEMETRY_INTERVAL,
SET_HEARTBEAT_INTERVAL, SET_SLEEP_SCHEDULE, CONFIG_UPDATE, WIFI_SCAN, WIFI_RECONNECT, RESTART.
STATUS/GET_CONFIGURATION/SET_CONFIGURATION/REBOOT remain compatibility aliases; RADIO_TEST
remains an unadvertised rejection boundary, not an enabled extra operation.
On legacy E220 settings without explicit lora_apply_settings permission, NORMAL mode adopts
observed packet length/WOR cycle without rewriting the radio; configured legacy address,
channel, power, baud and flags must still match. WOR mode additionally requires matching cycle.


## Operational action extension 1.4.0 (2026-10-29)
This requested extension adds runtime operations; wire schema 1, broker profile fields,
canonical topics and radio packet formats remain unchanged. Existing 21 primary commands
and Gateway page layout/dropdown remain unchanged. Twelve accepted operational commands
are additionally advertised by GET_CAPABILITIES and the Gateway operational_commands API.
All require an authenticated Gateway administrator; no administrator password is forwarded.
They use the same COMMAND, ACK and execution RESPONSE envelope and deduplication cache.

| Command | Exact arguments | Execution semantics |
| --- | --- | --- |
| SYNC_TIME | unix_time integer 1700000000..2147483647 | Set volatile UTC; envelope time must match; steps above 300 seconds require local commissioning; blocked during transport/sleep coordination |
| MQTT_CONNECT | empty object | Enable existing runtime profile; SUCCESS only after connection and subscription readiness |
| MQTT_RECONNECT | empty object | Requires authenticated IP return path and selected local IP; SUCCESS requires a new client recycle plus subscription readiness |
| MQTT_DISCONNECT | restore_after_seconds integer 10..120 | Requires authenticated IP return path and selected local IP; report actual paused state; automatically restore previous runtime enablement at deadline |
| MQTT_TEST | empty object | Publish a normal STATUS on existing status topic; wait for correlated PERSISTED receipt on existing config topic via MQTT; PUBACK alone is insufficient |
| RADIO_INSPECT | empty object | Existing initialized driver returns explicitly cached public settings; otherwise bounded read-only probe, no RF/register writes; actual fault fails |
| DISCOVER_NODES | timeout_seconds integer 5..30 | Requires already initialized/enabled radio and open registration; send existing HELLO; report only responding radio peers; no response fails |
| I2C_SCAN | confirm boolean true | Probe addresses 8..119 on already initialized INA219 bus in its sole sensor-task owner; bounded timeout; results at most 32 addresses; no pin/address-setting changes |
| GET_COMMAND_RESULT | command_id ASCII ID 1..48 | Only same-source volatile cache; expired/absent outcome UNKNOWN; released response payload is never reconstructed |
| RESET_DIAGNOSTIC_COUNTERS | scope NETWORK, confirm boolean true | Reset NetworkService delivery-failure and duplicate counters only; queues, NVS and history remain intact |
| SLEEP_NOW | duration_seconds integer 60..86400, mode DEEP or LIGHT | Volatile one-shot request; RESPONSE confirms PREPARING_TO_SLEEP, never actual sleep entry; at least 5 seconds before entry and wait for pending work/coordinators; timer wake; saved schedule unchanged |
| CANCEL_PENDING_SLEEP | empty object | Cancel only the one-shot request while awake; cannot wake an already sleeping device or cancel saved schedules |

Operational waits use monotonic time; one asynchronous operation at a time, bounded at
90 seconds (MQTT connection), 15 seconds (MQTT test / inspection / I2C), or the discovery
window. Duplicate command IDs do not restart jobs. MQTT connect/reconnect failure requests
restoration of previous runtime enablement, never overwrites the profile. Runtime restoration
is volatile; reboot retains the existing firmware startup policy and saved profiles unchanged.
A Gateway command timeout remains UNKNOWN until a correlated actual device result arrives.

Three additional requested actions reuse existing operations rather than duplicate wire names:
1. Gateway queued-only cancellation: authenticated POST
   /api/v1/devices/<identity>/commands/<command_id>/cancel-queued. Only QUEUED with no sent_at;
   response explicitly does not claim target execution was cancelled.
2. IP/MQTT transport change: existing CONFIG_UPDATE transport_action prepare/apply/confirm/cancel
   with Gateway administrator reauthentication and proof/rollback, as specified in 1.3.0.
3. Public E220 configuration: CONFIG_UPDATE accepts only a radio-only set plus expected_revision:
   lora_address_high/low (0..255), lora_baud (1200,2400,4800,9600,19200,38400,57600,115200),
   lora_channel (0..80), lora_air_rate (0..7), lora_tx_power (10,13,17,22), lora_packet_bytes
   (64,128,200), lora_wor_cycle_ms (500..4000, step500), lora_work_mode NORMAL/WOR_TX/WOR_RX,
   lora_fixed_mode/lora_rssi/lora_lbt booleans. Existing radio must be disabled, uninitialized
   and local lora_apply_settings permission false. Result is saved PENDING_LOCAL_COMMISSIONING,
   not applied/readback-verified. No remote lora_enabled or lora_apply_settings changes; no
   regional authorization or hardware success inferred from accepting a numeric setting.

Sensor-icon colors are Gateway presentation preferences only; they are not shared device
configuration, telemetry units, sensor calibration or hardware capabilities.
