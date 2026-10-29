# EMQX and HiveMQ preparation — not activated

No production broker connection, publish, subscription, ACL change or new Gateway
worker was started. Active profile/revision and protected stores were verified
unchanged. Explicit role builds start cloud paused; Slave cannot initialize it.

| Provider | Host | Native MQTT TLS | WSS information only |
| --- | --- | --- | --- |
| EMQX | n1161c10.ala.eu-central-1.emqxsl.com |8883|8084 /mqtt|
| HiveMQ |3e56a5883e564276920c2d356aa34c94.s1.eu.hivemq.cloud|8883|8884 /mqtt|

| Participant | Username | Client ID |
| --- | --- | --- |
| Master |ESP32_MASTER_01|CL_ID_ESP32_MASTER_01|
| Gateway |ESP32GATEWAY|CL_ID_ESP32GATEWAY|

Four canonical profiles in deployment/prepared are identical in both repositories.
Passwords are empty placeholders. Each provider has independent credentials and
permissions. Concurrent clients on one broker must have unique client IDs. No Slave
cloud connection is needed. Profiles retain TLS, MQTT3.1.1, QoS1, keepalive60,
timeout10, prefix selvarithik/gateway and GW001. WSS is documented only.

## Certificates inspected offline

Existing EMQX material is a public self-issued DigiCert Global Root G2 CA certificate,
BasicConstraints CA=true, expiring2038-01-15T12:00:00Z. It is not a private key,
client certificate or server leaf. SHA256:
cb3ccbb76031e5e0138f8dd39a23f9de47ffc35e43c1144cea27d46a5ab1cb5f.
The supplied2031-11-10 date does not match this file and cannot identify a trust chain.
HiveMQ preparation uses public ISRG Root X1 from the local Windows ROOT store,
expiring2035-06-04. Both remain candidate trust anchors: no live chain or hostname
was verified. preparation.json explicitly records broker_chain_verified=false.
Chain, hostname and current-time verification stay enabled. No insecure fallback.
Actual mutual-TLS requirements still need authorized broker-console verification.

## EMQX verification, deferred

Inspect Authentication and Authorization with authorized console access: both
usernames, Client-ID rules, Username rules, All Users rules and their precedence.
The owner reports All Users Publish+Subscribe selvarithik/#. This broad rule was
not independently verified or edited. MQTT_TOPIC_CONTRACT.md lists exact current
publish/subscribe paths for a least-privilege proposal, including subscriptions
required by readiness checks. Authorization does not implement missing handlers.
Do not delete working rules or change authorization modes automatically. EMQX
documents Client-ID/Username evaluation before All Users; native Whitelist mode
has version/deployment prerequisites. Confirm actual console availability first.
Gateway retains ACL_CONFIRMATION_REQUIRED until real verification.

## HiveMQ verification, deferred

Check the correct cluster's Access Management credentials and roles for both
participants against the same topic matrix. Confirm actual TLS chain, hostname and
cluster ports. EMQX permissions do not establish HiveMQ permissions. No console
session or live HiveMQ connection was performed.

## Secure staging after explicit approval

Do not repeat initial commissioning or replace the existing active deployment.
Read revision/state first. Firmware's existing USB helper stages a candidate:

```text
python tools/commission.py --port COM8 --operation mqtt --profile deployment/prepared/emqx-master.json --revision <current>
```

This future command was not executed. Confirm the physical device first. The helper
requests the password locally without echo and stages, not activates. No secret in
CLI/history, HTTP or ordinary MQTT. Substitute the HiveMQ file when appropriate.

Gateway: first stage the exact non-secret prepared profile through the existing
revision-checked candidate interface. Only while that exact profile is PENDING:

```text
.venv/Scripts/python.exe backend/commission_mqtt.py --profile deployment/prepared/emqx-gateway.json --revision <current> --pending-password
```

Enter the secret locally without echo. The existing Windows DPAPI store protects it;
never use the helper's initial-commission branch to overwrite an active profile.
Never commit secret stores. Device flash/NVS encryption/eFuse state was not checked;
no claim of encrypted device credentials at rest is made.

After direct radio tests, explicit live-MQTT approval and ACL verification, use the
existing stage/test/confirm/rollback transaction. Verify TLS, CONNACK, SUBACK, PUBACK,
peer confirmation, actual device ACK/RESPONSE, Gateway commit and dashboard display
separately. Invalid CA/hostname/credentials must fail closed. Test each broker
independently; keep old active settings on failure or unknown peer state.

The supplied secret appeared in conversation; rotating it through authorized broker
management is recommended, followed by protected local provisioning. No credential
rotation or provisioning was performed in this task.

Sources: [EMQX authorization](https://docs.emqx.com/en/cloud/latest/deployments/default_authz.html),
[EMQX ports](https://docs.emqx.com/en/cloud/latest/deployments/port_guide_serverless.html),
[HiveMQ setup](https://docs.hivemq.com/hivemq-cloud/quick-start-guide.html).
