# Command Center control audit — 2026-10-25

The complete template inventory is AUDIT_CONTROL_INVENTORY.json. Its 194 rows are
static inspection, not proof every field/button was tested live. Chat, MQTT and
OTA navigation entries remain out of this audit's execution scope.

| Control | Actual handler/API | Validation and state | Evidence |
|---|---|---|---|
| Node list/filter/select | command_center.js renderNodes/selectNode; GET /api/nodes | Enabled state and configured heartbeat age; selection loads history | Fixture UI and real Master selection |
| History/older messages | loadHistory; GET /api/commands?node_id=… | Bounded pagination; stale updates do not replace newer rows | Fixture UI |
| Send | composer submit; POST /api/v1/commands for enrolled nodes, legacy /api/commands otherwise | Registered target, command registry, typed payload, priority, retries, ACK/response/expiry bounds; existing auth/CSRF | Fixture invalid inputs and separate ACK/RESPONSE; physical Master PING |
| Stop dispatch | commandAction; POST /api/commands/{id}/cancel | Existing server authorization/state checks; cancellation is not a promise to undo physical execution | Software/API tests; no physical cancellation test |
| Retry | commandAction; POST /api/commands/{id}/retry | Existing server authorization/state rules; disabled while another command is active | Software/API tests; physical retry not exercised |
| Event history | loadEvents; GET /api/commands/{id}/events | Correlated command ID, event deduplication | Fixture UI and real stored Master command evidence |
| Payload details | Native details/summary | Escaped sanitized JSON; command and response kept separate | Fixture UI |
| Copy JSON | Delegated data-copy button handler | Existing sanitized response data only; disabled before a response | Source inspected; clipboard action not live exercised |
| Registry command name | Composer's registered custom-command branch | Unknown command names rejected by backend; no arbitrary privileged text execution | Software registry tests |
| Scan band/result limit | Removed ignored inputs | Backend did not consume the two values | Source inspection |
| Restart delay/reason | Removed ignored inputs | Backend did not consume the two values | Source inspection; no physical restart |
| Config section | Removed ignored input | Backend did not consume the value | Source inspection; no live configuration mutation |

All protected mutations retain existing account-role/CSRF checks. Device traffic
uses the existing signed local-IP protocol. An ACCEPTED ACK means acceptance, not
successful execution; the final correlated RESPONSE determines the command state.
Sensor READ_ERROR inside a successfully executed status query remains sensor data,
not an invented command failure or a valid sensor reading.

Other pages' account/credential, network, radio, restart and sleep mutations were
inspected but not all exercised on physical hardware. They remain pending live
acceptance where not covered by an explicitly named test. The mock node-state UI
results cover presentation/recovery, not real RF delivery or uninterrupted uptime.
