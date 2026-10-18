# Part 1 Gateway integration

The Wi-Fi-first firmware is in `D:\esp32 selva\ESP32_LoRa_ESP32_Firmware`. Full audit, file manifest, validation results, protocol contract and exact two-board instructions are in that project's `docs/PART1_REPORT.md` and `docs/PART1_AUDIT.md`.

## Run

Use the existing virtual environment. Install `requirements-part1.txt`; MQTT is optional through `requirements-mqtt.txt`. Before a new account database without legacy credentials is created, set GATEWAY_ADMIN_PASSWORD to a password of at least 12 characters. Existing account credentials are preserved. Sign in at `/accounts`.

Set GATEWAY_BIND=0.0.0.0 to listen on the private LAN, then run `.venv\Scripts\python.exe backend/server.py`. The default remains loopback; debug mode is disabled. ESP32 server_host must be the PC's actual LAN IP/hostname, not localhost. Browser API mutations now require an administrator/creator session and X-CSRF-Token. Existing unauthenticated simulator/feedback clients must migrate to authentication or the versioned device API. Socket.IO connections require an account session.

Enroll the actual Master, then its Nodes, using `backend/provision_device.py --help`. Save the Master's generated gateway_token in its local configuration. The token is hashed in SQLite and never returned by ordinary node/status APIs. The local enrollment CLI requires trusted filesystem/operator access; the alternative enrollment API requires an administrator session and CSRF.

## Routes

| Route | Authorization | Behavior |
| --- | --- | --- |
| POST /api/v1/device/exchange | X-Device-ID plus Master bearer token | Validates and stores/handles one v1 envelope; returns up to one pending command |
| POST /api/v1/device/register, heartbeat, telemetry, status, ack, response, diagnostic, events, alarms | Same as exchange | Envelope ingress aliases; the packet type specifies its semantics |
| GET/POST /api/v1/devices | Administrator session; CSRF on POST | List/enroll identity and explicit Master assignment |
| POST /api/v1/devices/<id>/rotate-token | Administrator session + CSRF | Deliberate Master credential rotation, shown once |
| GET /api/v1/devices/<id>/status | Administrator session | Last-received status and ONLINE/STALE/OFFLINE/UNKNOWN health |
| GET /api/v1/devices/<id>/config | Administrator session | Last-received configuration status; use GET_CONFIG command for a fresh reply |
| POST /api/v1/devices/<id>/config | Administrator session + CSRF | Queues validated telemetry_seconds/heartbeat_seconds/enabled changes |
| GET /api/v1/devices/<id>/diagnostics | Administrator session | Recent diagnostic/event/alarm records |
| GET/POST /api/v1/commands | Administrator session; CSRF on POST | Existing command model, bounded safe Part 1 command set |

Master tokens authorize only that Master and enabled enrolled Nodes explicitly assigned to it. HELLO is device registration/status refresh for a pre-enrolled identity; it does not let arbitrary devices create identities or claim assignments. Receipt deduplication spans HTTP and MQTT and survives Gateway restart. Ingress source timestamps do not set liveness; actual receiver time does.

The envelope's payload is a JSON **string**, maximum 2048 UTF-8 bytes, with payload_length and CRC32 over the string bytes. The outer frame is at most 4096 bytes. The CRC is an integrity check, not authentication. Frame IDs/content stay stable across retries. Command ACK means received; only a RESPONSE produces COMPLETED/FAILED. HTTP polling runs every two seconds; it is not instant push.

Safe commands: PING, GET_STATUS/STATUS, GET_TELEMETRY, GET_CONFIG, DIAGNOSTICS, SET_TELEMETRY_INTERVAL, SET_HEARTBEAT_INTERVAL and the restricted CONFIG_UPDATE. Interval command payload is `{"seconds":15}`. Unsupported legacy Command Center options fail explicitly through this adapter. Existing OTA modules predate Part 1; this firmware neither invokes nor expands them.

## Optional MQTT

Set GATEWAY_MQTT_HOST, PORT, USER, PASSWORD, optional CA (local CA certificate path), and TRUST_ACL=1 only after enforcing per-device broker ACLs. Each Master publishes only its own `/status`, `/telemetry`, `/events`, `/responses` under `gateway/v1/devices/<master-id>/` and subscribes only to its own `/commands`. Only the Gateway publishes commands/application ACKs. No retained commands or anonymous access. The adapter uses clean sessions, bounded Paho outgoing queues, QoS 1 downstream and app-level receipt IDs. Firmware uses QoS 0 uplinks with app-level ACK/retry and retains HTTP polling. HTTP works without Paho installed when MQTT is disabled. Real broker/TLS validation remains pending.

## Validation

Run `.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'`: 34 tests pass against disposable databases. MQTT tests use a fake broker, not a live connection. Firmware builds and its local UI was browser-tested with mocked API replies; board communication, actual DHT readings, real broker/CA handshakes and soak tests remain hardware/operator checks.

Additive migrations reuse nodes, telemetry_values, sensor_parameters, commands, command_events and logs. New metadata columns and the bounded device_receipts table do not seed demo telemetry. The production database is migrated when the server is next started. Existing live data was not reset by tests.
