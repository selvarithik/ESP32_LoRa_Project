> Current shared-build update: the RV1 section at the end supersedes historical
> DRIVER_UNAVAILABLE and software-only radio statements below. The UART driver is
> implemented/compiled but physically unverified. Explicit build/stored-role mismatch
> inhibits networking instead of changing NVS. JSON/MQTT schema remains1.

# Command protocol 1 - Command Center extension 3

## Architecture and compatibility
One existing NetworkService owns firmware dispatch; CommandManager delegates to it.
The Gateway retains command_manager.py, commands and command_events. The additive
command_delivery table stores scheduling only. No second command execution manager.
MASTER and NODE are canonical roles; Slave means NODE. Both build targets compile the
same role-aware source, with distinct initial role defaults. Existing NVS roles prevail.
Device ID remains the enrolled routing key. hardware_mac is the actual station/base
eFuse MAC in uppercase colon notation. ESP32-XXXXXXXXXXXX IDs reverse the six bytes
of ESP.getEfuseMac(); the Gateway resolves their MAC aliases without rewriting records.
Simulation identities use SIM prefixes and never stand in for actual MAC addresses.

## Wire adapter
The unchanged 15-field Message is protocol_version=1: message_id, source, destination,
origin_id, final_destination_id, next_hop, type, ttl, timestamp, sequence_number,
correlation_id, payload, payload_length, payload_crc32. Frame max 4096 bytes; compact
JSON payload max 2048 bytes; CRC32 covers payload bytes. Transport HMAC, TLS and source
assignment checks remain required: CRC is not authentication. No verbose JSON encoding
has been newly enabled over physical radio. The bounded binary radio core/model is
software-only and is not evidence of a working E220 driver or physical reassembly.

COMMAND payload: command_id equals message_id, command is a registry name, arguments
is an object. ACK/RESPONSE correlation_id equals payload.command_id. Gateway packets
keep timestamp and request bytes stable across attempts. Existing Gateway sequence=0
means unspecified; device sequence increments per boot. Trusted-clock transport expiry
and authenticated nonce checks apply; sequence alone is not replay authentication.

## Registry and execution
command_catalog.h / command_rules.h and device_control_contract.py are parity-tested.
Read operations: PING, GET_STATUS/STATUS, DIAGNOSTICS, GET_TELEMETRY, GET_CONFIG,
GET_CAPABILITIES, GET_SENSOR_STATUS, GET_MESH_STATUS, GET_NODE_STATUS, GET_ROUTE_INFO,
GET_NETWORK, WIFI_SCAN, GET_RADIO_STATUS, GET_POWER_STATUS.
Actions: CONFIG_UPDATE, SET_DEVICE_NAME, SET_TELEMETRY_INTERVAL,
SET_HEARTBEAT_INTERVAL, SET_SLEEP_SCHEDULE, WIFI_RECONNECT, RADIO_TEST, RESTART.
Aliases: GET_CONFIGURATION -> GET_CONFIG; SET_CONFIGURATION -> CONFIG_UPDATE;
REBOOT -> RESTART. Unknown commands are rejected. Secret configuration, arbitrary
code/GPIO access and remote cancellation are unsupported. WIFI_RECONNECT reports
CONNECTING, not an established connection. RADIO_TEST fails DRIVER_UNAVAILABLE.
GET_ROUTE_INFO explicitly reports unavailable physical routes, not invented routes.
PING optionally accepts message string <=128 UTF-8 bytes. Interval arguments: seconds
integer 2..3600 (telemetry), 5..3600 (heartbeat). Read and restart arguments are empty.
SET_DEVICE_NAME accepts device_name 1..64 UTF-8 bytes and optional expected_revision.
CONFIG_UPDATE uses only existing non-secret config fields and optional expected_revision.
GET_CONFIG is a bounded RUNTIME snapshot; full local settings remain /api/config.
The full config field/type/range list is CONFIG_CONTRACT.md. Writes use existing NVS
validation and persistence. Responses report configuration_revision and restart_required.
RESTART persists its intent, drains pending work and reports after software reset;
no pre-reset SUCCESS is manufactured. No firmware was flashed during this task.

## Acceptance versus execution
ACK: command_id, status ACCEPTED/REJECTED/BUSY/DUPLICATE, optional error_code.
Legacy RECEIVED means receipt, not execution. Admission checks shape, registry and
basic ranges before ACCEPTED; storage/conflict failures during execution remain FAILED.
DUPLICATE replays a cached result without executing again; changed request bytes under
a known ID are not executed. Firmware cache is bounded to 32 entries and volatile.
Only restart has a durable NVS intent/result marker. Ordinary operations cannot promise
exactly-once execution across a reboot. Configuration operations are value-idempotent;
revision counters can change if a request is repeated after cache loss.
RESPONSE: command_id, status SUCCESS/FAILED/UNSUPPORTED, data, execution_duration_ms
where measured. A response without an ACK completes execution without inventing ack_at.
Rejected/BUSY ACK cannot become success. Broker acknowledgement is not a device ACK.

## Gateway policy, persistence and UI
POST /api/v1/commands uses node_id, command_type, payload, optional command_id,
priority 1..10, max_retries 0..10, timeout_seconds 1..300,
ack_timeout_seconds 1..60 (default 5), response_timeout_seconds 1..300 (default
 timeout_seconds), expiry_seconds 1..300 (default 300). Capacity: 64 active commands.
The legacy /api/commands route delegates enrolled devices to the same validated API.
Command Center sends canonical arguments, shows history, ACK, execution result,
retry events and errors. Existing header, navigation and unrelated pages are retained.
Authenticated admin + CSRF is required to submit/mutate. Authenticated assigned device
transport is required for enrolled ACK/RESPONSE; browser state/ack/response simulation
routes cannot forge enrolled-device results. Cancel stops further dispatch only.

QUEUED -> SENT -> ACK_RECEIVED (public ACKNOWLEDGED) -> COMPLETED/FAILED.
Response may arrive without ACK. ACK timeout retries are bounded to 1+max_retries
attempts, spaced by ack_timeout_seconds. After ACK, only response deadline applies.
Expiry/deadline produces TIMEOUT: execution unknown. Late results are audited as
LATE_RESPONSE without rewriting TIMEOUT/CANCELLED to success. Explicit retries retain
identity/expiry; expired commands require a new command ID. SQLite schedules survive
Gateway restart. The existing server heartbeat checks deadlines without device polling.
Concurrent in-process state mutation is serialized and state updates compare prior state.

## Routing and hardware limits
Registered local-IP forwarding remains available. TTL is consumed at forwarding;
missing/stale route, hop-limit and queue errors become authenticated Master route-failure
events. They never impersonate Slave ACK. Child nodes cannot administer their Master.
Physical E220 remains DRIVER_UNAVAILABLE. SKU, frequency, UART pins/mode, supply,
antenna and regional parameters are not verified; no physical driver was activated.
Multi-hop physical routing is not implemented or claimed. Simulated fragmented radio,
loss/retry tests and real loopback HTTP tests are software evidence only. MQTT continues
using command and command_ack from the existing registry, TLS and ACL restrictions;
no new topics, ACL changes or live broker test was performed.

## ESP32 login
Browser login uses /api/auth/login/start and /api/auth/login/result. Password hashing
runs in one bounded worker; cookie/CSRF/session changes remain on the web loop.
Pending work is session-bound and credential-generation checked. Session readiness,
request timeout, polling deadline and actionable invalid-password feedback prevent
indefinite Verifying. Legacy /api/auth/login remains compatible. PBKDF2=100000 is
unchanged. admin/admin is initial commissioning only; saved passwords are not reset.
Physical password recovery, if needed, uses the existing USB commissioning helper.


## RV1 shared radio adapter — contract1.2.0
Both builds share E220Core, LoRaTransport, TransportManager, NetworkService,
protocol validators, CommandManager and SensorManager. No duplicate Slave protocol.

Gateway (signed local IP, or later approved MQTT TLS) -> Master dispatcher ->
authenticated next-hop RV1 fragments -> Slave handler -> ACK/actual RESPONSE ->
Master -> existing Gateway command manager/database/dashboard. Slave telemetry takes
the reverse path. An intermediate Master never replaces Slave execution results.

MessagePack array, exactly14 entries, in order:
[protocolVersion:uint8,type:string,ttl:uint8,timestamp:uint32,sequence:uint32,
messageId:string,source:string,destination:string,nextHop:string,origin:string,
correlationId:string,payload:object,hopCount:uint8,maxHops:uint8].
Strings/IDs <=48 UTF-8 bytes; payload JSON <=2048; encoded logical message <=3072.
MessagePack standard integer encoding applies. Decode reuses the production Message
validator. Hop metadata is radio-only; existing15-field Gateway JSON is unchanged.

Header30bytes: magic E2 7A, version1, flags0, transferLE32, immediate senderMAC6,
next-hop targetMAC6 (FF broadcast), fragment index8,count8,totalLE16,length8,span8,
whole-message CRC32LE. Followed by fragment bytes and first16 bytes of
HMAC-SHA256(header+fragment,mesh_key). COBS encoding adds zero delimiter.
CRC is corruption detection. Shared-key HMAC authenticates mesh membership, not
individual cryptographic ownership. This adapter does not encrypt payloads; never
send credentials in radio packets.

Frame+delimiter <= observed subpacket64/128/200;32 rejected fail-closed.
Span=subpacket-2 COBS allowance-30 header-16 tag. Two bounded3072-byte assemblies
handle out-of-order fragments; inconsistent duplicates, bounds and CRC failures
are rejected. Assemblies expire120s. Verify HMAC before admission. Completed-transfer
cache32; random transfer IDs. Fixed mode uses FFFF+observed channel broadcast prefix,
then logical target filtering. No invented address mapping. RSSI/SNR remain null;
physical appended-RSSI packet alignment is unverified.

One TX message, one completed RX, two assemblies,12 routes,32 duplicate-forward entries.
One fragment per loop, AUX-stable check, conservative UART/airtime guard. UART submission
is not RF delivery or application ACK. TTL consumed on forwarding; hop count increments
per radio hop, maximum <=15; duplicate/immediate-return forwarding is rejected.
Routes age with saved timeout and prefer fresh shorter paths. No invented routes.
Registration still requires allowed peers or explicit registration_open. Parent/source
assignment is checked. Master announces HELLO30s+jitter; Slave discovers a permitted
Master without rewriting saved assignment. Multi-hop is IMPLEMENTED_BUT_NOT_HARDWARE_VERIFIED.

PING/PONG semantic is COMMAND/PING plus ACK and RESPONSE, preserving existing types.
Discovery uses HELLO/addressed HELLO reply. Errors use rejection ACK, failed RESPONSE,
EVENT/ALARM, not new ERROR topics. Existing DISCOVERY definitions remain compatible.
Unclocked PING/basic status may run; privileged mutations need a trusted fresh clock.
RADIO_TEST refuses USE_ADDRESSED_PING_DURING_APPROVED_HARDWARE_TEST; GET_RADIO_STATUS
reports driver state. Route/node summaries are bounded. Saved retry_count and
command_timeout_ms bound existing retries; Gateway ACK/response deadlines remain separate.
Volatile duplicate cache cannot promise exactly-once side effects across power loss.

Native check_e220.py executes production framing/settings/reassembly/routes for both
roles. Legacy radio_frame.h and Python SimulatedRadio remain older software models;
their tests do not prove RV1 UART, HMAC, RF performance or physical multi-hop.
