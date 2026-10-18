# EMQX authorization audit — 2026-10-19

Scope: read-only source, existing evidence and local runtime audit. No broker connection was created, no message was published, no worker was enabled, and no application configuration, secret store, database, ESP32 settings or firmware was changed. This report is the only new deliverable. Console actions and verification below are instructions for the owner, not actions performed by this audit.

## 1. Verified configuration and evidence boundaries

Both CONFIG_CONTRACT.md files are byte-identical, version 1.0.1 / schema 1. SHA-256:

`b91cac08abd7be3e0310140e53205b86aad728bbcf5de7e21a93e95b62ee9472`

The Gateway database was opened using SQLite `mode=ro`, without constructing Store, starting the server, running migrations or decrypting the secret file. Its current active settings are:

| Setting | Read-only database result |
|---|---|
| profile_name | ESP32_LORA_GATEWAY001 |
| host | n1161c10.ala.eu-central-1.emqxsl.com |
| port / protocol | 8883 / MQTT 3.1.1 over TLS |
| username | ESP32LORA |
| client_id | SELVA_GATEWAY_SERVER_001 |
| topic_prefix / gateway_id | selvarithik/gateway / GW001 |
| keepalive_s / timeout_s / qos_default | 60 / 10 / 1 |
| schema_version / revision / shared_revision | 1 / 6 / 1 |
| transaction / pending candidate | COMMITTED / absent |
| password storage | Active secret reference present; value not read |
| enrolled Master | ESP32-10777D842178; MASTER; enabled; enrolled |

Sources: `backend/database.py:11`, `backend/mqtt_store.py:56`, `backend/mqtt_store.py:72`. Database enrollment establishes the intended Master identity, not its current firmware role or broker connection.

Current runtime observations: localhost port 5000 is served by Python PID 4464; `/login` returns 200 and anonymous `/api/mqtt` returns 401. No TCP connection to remote port 8883 belongs to that Gateway process. The observed established 8883 connection belongs to MQTT Explorer PID 13460. This proves neither its MQTT authentication nor the identity it uses. Do not mistake MQTT Explorer for the permanent Gateway worker or reuse either production Client ID in Explorer.

Last recorded Gateway startup state is `disconnected / ACL_CONFIRMATION_REQUIRED`, in `docs/ACCESS_LIVE_SERVER_EVIDENCE.json`. Authenticated current in-memory worker status could not be read in this audit because there was no authenticated browser session; current thread existence and gate value therefore remain unverified. Current evidence establishes that the Gateway is not connected to port 8883 at observation time, rather than proving the exact internal failure reason. No login bypass or application import was used to manufacture a new service instance.

The most recent saved diagnostic, `docs/ACCESS_LIVE_BROKER_PROBE.json`, records verified TLS followed by `AUTH_FAILED` / “Bad user name or password”, Paho normalized reason 134. It is historical evidence, not a fresh connection in this audit. ACL changes cannot repair rejected authentication. Older `PHYSICAL_MQTT_EVIDENCE.json` used an isolated database and is not proof of current permanent-worker connectivity.

## 2. Client identities

| Participant | Value and confidence | Assignment / evidence |
|---|---|---|
| ESP32 Master | `ESP32-10777D842178`, last recorded active MQTT Client ID; fresh hardware confirmation required | `docs/ACCOUNT_FIRMWARE_BASELINE.json`; firmware uses stored active `profile.client_id` directly, `src/communication/canonical_mqtt.cpp:114`. It does not necessarily derive it from device_id. |
| Gateway permanent worker | `SELVA_GATEWAY_SERVER_001`, confirmed in current active database | Configured, not generated: `backend/mqtt_service.py:29`–36. |
| ESP32 candidate tester | first 40 characters of candidate client_id + `:test:` + first 8 transaction-ID characters | `src/communication/mqtt_candidate.cpp:46`. For the recorded Master ID: `ESP32-10777D842178:test:<tx8>`. No pending transaction currently supplies an exact tx8. |
| Gateway candidate tester | first 40 characters of candidate client_id + `:test:` + first 8 transaction-ID characters | `backend/mqtt_service.py:270`. With unchanged candidate ID: `SELVA_GATEWAY_SERVER_001:test:<tx8>`. |
| Gateway commit recovery | first 40 characters of pending client_id + `:recover:` + first 8 transaction-ID characters | `backend/mqtt_service.py:346`. With unchanged candidate ID: `SELVA_GATEWAY_SERVER_001:recover:<tx8>`. |

Candidate IDs use the candidate profile, which may differ from active. The examples above are conditional rules, not exact IDs to paste before a transaction exists. First-eight-character transaction truncation is not a guarantee against collisions. Duplicate Client IDs can cause an existing MQTT session to be disconnected. Do not connect a diagnostic client under an active production ID.

Safe live verification:

* Gateway: sign in normally, open `/mqtt`, or use browser developer tools on that authenticated same-origin page:

```javascript
fetch('/api/mqtt', {cache:'no-store'}).then(r => {
  if (!r.ok) throw new Error('Authenticated status unavailable');
  return r.json();
}).then(s => console.log({client_id:s.active?.client_id, revision:s.revision,
  shared_revision:s.shared_revision, runtime:s.runtime}));
```

* ESP32: use its authenticated `/api/mqtt` response and inspect only `active.client_id` and runtime status. Alternatively, close competing COM8 monitors and send only `{"op":"status"}` followed by newline through the existing USB serial console at 115200 baud. The handler is `src/core/commissioning.cpp:49`; its MQTT response contains `active_client_id`, revision and runtime (`src/config/mqtt_staging.cpp:75`–90). Keep DTR/RTS inactive. This is a read-only operation; do not use password, recovery, commissioning, time or MQTT mutation operations. Do not dump NVS or serial boot logs into a report. COM8 previously failed with Windows error 31; no device access was attempted here.
* EMQX: inspect the existing Clients/Subscriptions views for the exact IDs, without creating another connection. A device ID in enrollment is not a substitute for the configured MQTT Client ID.

## 3. Complete canonical topic registry and actual directions

One builder per side: `topic_prefix + '/' + gateway_id + '/' + message_type`. Evidence: firmware `src/config/mqtt_contract.cpp:73`, Gateway `backend/mqtt_contract.py:73`. A static audit parsed the current Gateway subscription tuple and firmware subscription list: all six Master and nine Gateway subscriptions belong to the 11-item registry; no wildcard subscriptions occur in these lists.

The table below states the CONTRACT permissions. `P` means publish; `S` subscribe; `—` forbidden by the contract. All use QoS 1. Contract evidence: `CONFIG_CONTRACT.md:117`–145, individual row numbers shown below.

| Exact topic | Master publish | Master subscribe | Gateway publish | Gateway subscribe | Contract line |
|---|---|---|---|---|---|
| selvarithik/gateway/GW001/telemetry | P | — | — | S | 126 |
| selvarithik/gateway/GW001/status | P | — | — | S | 127 |
| selvarithik/gateway/GW001/command | — | S | P | — | 128 |
| selvarithik/gateway/GW001/command_ack | P | — | — | S | 129 |
| selvarithik/gateway/GW001/config | P | S | P | S | 130 |
| selvarithik/gateway/GW001/events | P | — | — | S | 131 |
| selvarithik/gateway/GW001/discovery | P | — | — | S | 132 |
| selvarithik/gateway/GW001/chat/message | P | S | P | S | 133 |
| selvarithik/gateway/GW001/chat/ack | P | S | P | S | 134 |
| selvarithik/gateway/GW001/chat/status | P | S | P | S | 135 |
| selvarithik/gateway/GW001/chat/command | — | S | P | — | 136 |

Actual source cross-check:

* Master subscribes exactly to command, config, chat/message, chat/ack, chat/status, chat/command: `src/communication/canonical_mqtt.cpp:45`. It publishes telemetry, status, command_ack and events through packet mapping at line 122, config through comparison/probe/control replies at lines 94, 118–119, and chat/ack at lines 77 and 104. All enqueue operations use QoS 1, retain false (line 40).
* Gateway subscribes exactly to telemetry, status, command_ack, config, events, discovery, chat/message, chat/ack, chat/status: `backend/mqtt_service.py:39`, actual subscribe at lines 100–103. It produces config receipts/control/comparison, command packets, chat/message and chat/ack: lines 149–150, 160, 187, 213, 256. Its queue publish is QoS 1 / retain false at line 249.
* No production Master discovery publisher exists in that mapping: HELLO/HEARTBEAT map to status. No production Master-origin chat/message or chat/status emitter was found. No Gateway chat/status or chat/command emitter was found. These are reserved contract permissions, not proven active features.
* Master subscribes to chat/ack, chat/status and chat/command but `receive` has no dispatch branch for those kinds (`canonical_mqtt.cpp:79`–106). Gateway chat/status is a no-op (`mqtt_service.py:188`). An accepted subscription does not prove those functions work.
* The contract permits retained status/LWT; the current Master publisher always uses retain false and does not configure a last will in `begin` (lines 109–116). Do not claim working retained liveness/LWT.
* No observed source direction violates the contract. The missing emitters/handlers are implementation gaps. They are not silently repaired in this audit.

## 4. Exact minimum console rule plan

Use the **Client ID** authorization category, **Permission = Allow**, and the exact identities above. Do not add application-topic Allow rules under Username or All Users. All rows below are exact topics; there are no `+` or `#` grants. Each populated cell is one rule for that column's Client ID. A dash means do not create a rule. “Both” means the console action **Publish and Subscribe**, a single entry rather than two conflicting entries for the same identity/topic.

**Confirm the live ESP32 Client ID before applying its column.** If it differs from the recorded value, stop and prepare rules for that verified active identity without changing the device.

| Exact topic | Client ID ESP32-10777D842178 | Client ID SELVA_GATEWAY_SERVER_001 | Reason / source |
|---|---|---|---|
| selvarithik/gateway/GW001/telemetry | Publish | Subscribe | measurements; Master:122, Gateway:39/143 |
| selvarithik/gateway/GW001/status | Publish | Subscribe | status packets; Master:122, Gateway:39/143 |
| selvarithik/gateway/GW001/command | Subscribe | Publish | existing command path; Master:45/79, Gateway:150 |
| selvarithik/gateway/GW001/command_ack | Publish | Subscribe | receipt/result; Master:122, Gateway:39/143 |
| selvarithik/gateway/GW001/config | Both | Both | comparison, persistence receipts, switch; Master:45/83–94/118, Gateway:149–172/256 |
| selvarithik/gateway/GW001/events | Publish | Subscribe | diagnostics/events; Master:122, Gateway:39/143 |
| selvarithik/gateway/GW001/discovery | — | Subscribe | Gateway currently requests this subscription; Gateway:39 |
| selvarithik/gateway/GW001/chat/message | Subscribe | Both | text ingress/egress; Master:45/95–104, Gateway:175–187/213 |
| selvarithik/gateway/GW001/chat/ack | Both | Both | firmware subscribes and emits; Master:45/77/104, Gateway:39/173–187 |
| selvarithik/gateway/GW001/chat/status | Subscribe | Subscribe | actual startup subscriptions, even though handlers are incomplete; Master:45, Gateway:39/188 |
| selvarithik/gateway/GW001/chat/command | Subscribe | — | actual firmware startup subscription; Master:45; action handler absent |

This is **20 Client-ID/topic entries**, sufficient for current source operations and all startup subscriptions. QoS 1 is required for every entry by the contract. The documented basic Cloud rule editor may not expose a QoS selector; do not invent one. If the deployed authorization backend supports QoS constraints, allow only QoS 1. Otherwise record that basic ACL rules do not enforce QoS and application checks remain necessary. Topic authorization alone does not validate message payloads.

Optional contract-complete permissions, deliberately outside the current minimum: add Master Publish on discovery; upgrade Master chat/message and chat/status to Both; upgrade Gateway chat/status to Both; add Gateway Publish on chat/command. These yield 22 identity/topic entries in total. They permit reserved functions but do not implement them. Do not add them merely to hide missing handlers.

Candidate/recovery clients require separate exact-ID **Both** permission on the exact config topic on each relevant broker. The actual IDs are unavailable until the real candidate profile/transaction exists. Do not enter the literal `<tx8>` examples, use client-ID prefix wildcards, or expand topic grants. Read the pending transaction nonsecret ID, compute the rules from section 2, then review and add the three exact identities required by that transaction. Remove temporary grants only when recovery is no longer needed. Broker switching remains unverified under the minimum permanent-client rules.

Identity security prerequisite: a Client ID is supplied by a connecting client. Shared username/password authentication alone does not prove that a client is the Master or Gateway. If an authenticated client can select the other production ID, it can acquire that ID's ACL and disconnect the real session. Before asserting ACL trust, verify an authentication policy that binds the authenticated principal to its permitted Client IDs, or an equivalent reviewed identity control supported by this deployment. No such broker-side binding was verified here. Do not rotate credentials, change identities or add broad username permissions as an audit shortcut. The exact binding policy is a broker-administration prerequisite, not something the local source can prove.

## 5. Manual EMQX Cloud steps

Current “Blacklist, no rules” is OWNER-REPORTED, not independently inspected in the console. In blacklist mode, absent a matching denial, publish/subscribe operations are allowed; an empty list is not restrictive authorization.

1. Open EMQX Cloud, select the existing **ESP32_LORA_GATEWAY001** deployment. Check hostname/port against section 1. Save a nonsecret record of existing authorization rules, source ordering, mode and connected Client IDs. Do not export credentials or connection payloads.
2. Open **Access Control → Authorization → Default Authorization / Client Authorization** (the exact submenu depends on the deployed console). Review Username, Client ID and All Users rules, plus any extended authorization sources. Identify other legitimate deployment clients before changing a deployment-wide fallback.
3. Confirm the actual Master ID and the Gateway database ID. Review MQTT Explorer's configured ID locally; ensure it is distinct, and do not grant it broad production publish rights. Verify authentication identity binding and anonymous rejection. Authentication and authorization are separate controls.
4. Keep blacklist mode while entering the 20 exact Allow entries in section 4 under **Client ID → Add**. For each enter Client ID, full Topic, Action and Permission **Allow**, then Confirm. Check every saved rule against the table. Remove or narrow existing overlapping broad grants only through the owner's reviewed broker change; an earlier matching Allow may bypass a fallback denial.
5. Include exact candidate/recovery rules only for actual planned transactions. Account for any other legitimate existing applications before proceeding. A mode change without their complete rule sets could lock them out.
6. Only after the complete rules and source order have been reviewed, switch **Blacklist Mode → Whitelist Mode** if that control is supported. Unmatched operations must be denied. Keep the permanent worker gate off until verification below succeeds.
7. If the deployment cannot switch modes (including relevant Serverless/older versions), the documented alternative is an **All Users**, Topic **#**, Action **Publish and Subscribe**, Permission **Deny** fallback, after specific identity Allow rules. This is a denial, not an All Users grant. Default Authorization must be placed appropriately after extended sources; verify actual evaluation order. Do not apply both strategies blindly or leave an earlier broad Allow in place.
8. Review authorization statistics/logs for expected identities/topics, all startup subscription permissions and denied out-of-scope operations. Do not infer effective security merely because an Allow entry exists. Current EMQX Cloud docs describe the mode availability and first-match behavior: [Default Authorization](https://docs.emqx.com/en/cloud/latest/deployments/default_authz.html), [Cloud v5 authorization](https://docs.emqx.com/en/cloud/latest/best_practices/acl_v5.html).

Steps 1–8 were not performed by this audit. Negative authorization and duplicate-ID acceptance checks still require a reviewed broker test that avoids production client takeover or application command delivery. Use a broker-side policy check or controlled isolated identities/environment; do not test by impersonating a currently connected production Client ID. Authentication failure prevents reaching subscription authorization at all.

## 6. Gateway worker and safe owner start

Existing worker entry point: `backend/server.py:4272`–4276 → `backend/mqtt_adapter.py:8` → `backend/mqtt_api.py:25` → `Service.start`. API requests alone instantiate the service/store but do not start the worker. It uses `data/gateway.db` for the journal/profile and `data/mqtt-secrets.bin` for current-user Windows DPAPI-protected recoverable secrets (`mqtt_store.py:16`–45). The account database and login session key are separate. Do not decrypt or print secret contents.

The gate is read at service construction from `GATEWAY_MQTT_TRUST_ACL == '1'` (`mqtt_api.py:22`). `mqtt_service.py:74` leaves startup blocked otherwise. Setting an environment variable in another terminal cannot change the already-running process. The source does not automatically load a .env file; do not assume an edited file changes runtime.

After the owner has verified authentication, restrictive ACLs, identity binding and client uniqueness, gracefully stop the existing server in its own console. Do not start a second server/worker. In a local PowerShell session under the same Windows account that owns the DPAPI store:

```powershell
Set-Location -LiteralPath 'D:\esp32 selva\ESP32_LoRa_Project'
$env:GATEWAY_MQTT_TRUST_ACL = '1'
& '.\.venv\Scripts\python.exe' '.\backend\server.py'
```

This is an OWNER action after verification, not a command run by this audit. It starts normal application activity, including possible queued application traffic; inspect queues first. Startup may reconcile the existing durable transaction, so do not use it as a supposedly read-only diagnostic. Do not rerun initial commissioning. Keep the same profile/revisions/secret store. Existing authentication rejection must be resolved by the authorized broker/provisioning workflow without printing or replacing stored secrets merely to test.

To disable the gate for a later intentional restart, stop the server gracefully and remove this session-only variable with `Remove-Item Env:GATEWAY_MQTT_TRUST_ACL -ErrorAction SilentlyContinue`. This does not change an already-running worker or reverse broker authorization.

## 7. Acceptance checklist and evidence still required

| Stage | Exact evidence required | This audit |
|---|---|---|
| Contract/topic parity | Same contract bytes; registry/builders; exact subscription lists | PASS: hash and static topic/subscription check |
| Current device identity | USB status active_client_id and current MASTER role; broker Clients match | PENDING; last saved active ID only |
| TLS | CA chain and hostname verification plus successful handshake using active profile | Source verified; prior bounded probe passed; no fresh handshake |
| Authentication | Successful CONNACK for each intended authenticated identity | PENDING; last saved Gateway probe failed authentication |
| Effective authorization | Specific per-client directions, anonymous denial, other-Gateway/topic denial, no identity impersonation | PENDING owner broker verification |
| Subscription readiness | Master six QoS-1 subscriptions; Gateway nine QoS-1 SUBACK grants and runtime READY | PENDING; source checks at Master:45–46, Gateway:100–108 |
| Master publication | Ordinary, non-command telemetry queued; actual broker PUBACK counter/time advances | PENDING; queue acceptance alone is insufficient |
| Gateway receipt/validation | last_broker_frame_received_at advances; envelope topic/schema/age/auth checks pass | PENDING; Gateway mqtt_service.py:111–115/128–146 |
| Database commit | Matching source/message ID in device_receipts and expected telemetry_values rows; runtime last_database_persisted_at | PENDING; mqtt_service.py:147–149, device_api.py:255/280–289 |
| Application receipt | Master receives config PERSISTED for that committed packet | PENDING; PUBACK alone is not persistence |
| Dashboard | Same new measurement/source/timestamp visible after telemetry_update event | PENDING; device_api.py:256/289; HTTP fallback must not be mistaken for MQTT |
| Chat | Correlated recipient acknowledgement; state reflects actual recipient and persistence semantics | PENDING; a browser row or broker PUBACK is insufficient |
| Candidate switching | Exact temporary identities authorized; peer nonce proof; durable decision/recovery | PENDING; minimum active-client ACLs do not authorize testers |

Source TLS checks: Master `canonical_mqtt.cpp:115` sets SSL transport, MQTT 3.1.1 and `skip_cert_common_name_check=false`; Gateway `mqtt_contract.py:170`–176 uses PROTOCOL_TLS_CLIENT, the configured CA and asserts check_hostname/CERT_REQUIRED. The ESP32 network task waits for a plausible clock (`transport_manager.cpp:73`); a plausible clock does not prove NTP synchronization.

No unit suite, mocked UI suite, local broker suite, live broker test or physical hardware acceptance was run for this read-only audit. Existing tests were inspected, notably `tests/test_mqtt_contract.py:53`, `:133`–170 and `tests/test_mqtt_adapter.py:7`; their existence is not a new pass result. The one executed pure static check passed contract byte/hash parity, registry membership and subscription counts. Application emitters/handlers listed as missing above, fresh firmware identity/status, broker authentication, actual console rules/mode/source order, credential-to-client binding, and current authenticated worker status remain unresolved evidence. Keep ACL_CONFIRMATION_REQUIRED until the relevant broker prerequisites have been verified.
