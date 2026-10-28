# MQTT topic contract — schema 1

CONFIG_CONTRACT.md is canonical. Topics are topic_prefix + '/' + gateway_id + '/' + approved message type, built only by MqttContract::topic / mqtt_contract.topic. Telemetry=telemetry, commands=command, ACK/execution RESPONSE=command_ack, device heartbeat=status, diagnostics/events=events. Configuration coordinator uses config; discovery uses discovery. Existing unrelated registry entries are unchanged and out of this phase's scope.

TLS certificate-chain and hostname verification always enabled, MQTT3.1.1, QoS1, unique stable participant client IDs. Profile catalog selection stages candidates; test/confirm/rollback still applies. Publishing/queue acceptance/PUBACK are not device execution. Permanent Gateway worker requires authorized ACL confirmation. Broker tests this phase must be disposable local TLS tests or injected client tests; no changes to hosted deployment ACLs/credentials.

Runtime Connect/Pause is an authenticated revision-checked operation, separate from saving a profile. The Gateway connect request retains ACL_CONFIRMATION_REQUIRED until authorization is verified. The ESP32 local-IP-only mode must be explicitly disabled and restarted before MQTT runtime connect; no hidden hosted connection is started by a local-IP setup. Pausing preserves active profiles/credentials and does not prove pending application delivery. No secrets are sent through plaintext bearer/Basic-auth fallback by new firmware clients; local peer links use the signed local transport. Runtime enable state is not a new profile field.

Command extension 3 retains command for COMMAND and command_ack for ACK/RESPONSE. MAC aliases do not create MQTT topics.


## Audited publisher/subscriber matrix (shared builds, contract1.2.0)
Suffixes below use the one canonical builder. P=implemented publish path;
S=current subscription. MQTT3.1.1, QoS1, retain=false. No last-will claim.

| Suffix | Master | Gateway | Implemented payload/handler |
| --- | --- | --- | --- |
| telemetry |P|S|data.packet TELEMETRY|
| status |P|S|HELLO/HEARTBEAT/STATUS|
| command |S|P|Addressed COMMAND|
| command_ack |P|S|ACK or actual execution RESPONSE|
| config |P/S|P/S|Existing comparison/switch coordinator|
| events |P|S|EVENT/ALARM/DIAGNOSTIC|
| discovery |No emitter|S|Reserved receive adapter for HELLO/HEARTBEAT/STATUS|
| chat/message |S|P/S|Legacy preserved path, excluded from this phase|
| chat/ack |P/S|P/S|Legacy preserved path, excluded|
| chat/status |S|S|No publisher; Gateway no-op handler|
| chat/command |S|None|No implemented dispatch or publisher|

No Chat work was implemented or tested. Current readiness needs successful SUBACK
for every current subscription, including legacy ones. ACL omissions can prevent
READY. Authorization alone does not implement missing handlers.

Explicit role builds start cloud paused; Slave cannot initialize a cloud client.
Legacy esp32dev startup remains compatible. No profile or worker was activated.
Gateway retains ACL_CONFIRMATION_REQUIRED. Propose participant permissions exactly
matching its P/S rows at the canonical base, then verify actual console rule order
and deployment prerequisites before applying changes. The reported broad All Users
selvarithik/# allow was not verified or edited. See docs/CLOUD_PREPARATION.md.

Gateway COMMAND -> Master shared dispatcher -> registered addressed radio route ->
Slave shared dispatcher -> ACK/actual RESPONSE -> Master -> command_ack -> Gateway.
UART submission, queue acceptance, PUBACK, device ACK, execution RESPONSE, SQLite
commit and dashboard display require distinct evidence. Existing JSON is unchanged.
