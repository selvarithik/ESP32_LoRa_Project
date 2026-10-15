# Command Center node conversations

Project: D:\esp32 selva\ESP32_LoRa_Project
Preview: http://127.0.0.1:5000/command-center
Source backup: D:\esp32 selva\command-center-backup-20261015
No commit or push was made.

## Files changed for this task

- dashboard/templates/command_center.html: replaces the separate history, response,
  lifecycle and configuration columns with a Nodes sidebar and one conversation.
  Existing command types, parameter fields and mappings are retained in the composer.
- dashboard/static/js/command_center.js: adapts the existing command APIs to node
  conversations, paginated history, actual audit events, response payloads,
  cancel/retry actions and shared live events.
- dashboard/static/css/command-center-chat.css (new): page-scoped desktop/tablet/mobile
  chat layout, bubbles, node list, independent conversation scroll and bottom composer.
- tests/command_chat.cjs (new): actual API/browser workflow against disposable test data.
- docs/COMMAND_CHAT_IMPLEMENTATION.md (new): this report.

No backend route, database schema, command state machine, communication adapter,
authentication logic, Sensor Management or telemetry layout was changed in this task.

## Layout and behavior

The left column lists registered nodes with search, All/Online/Offline filters,
selected state, firmware and actual last-seen timestamps. The right column keeps
the selected node's details at the top, a chronological conversation in the middle
and command selection/configuration at the bottom. Mobile opens the node list first
and provides a Back to Nodes button inside the conversation.

Command bubbles contain real command IDs, target, payload parameters, priority,
timeout, retries, dispatch status, ACK status and execution state. Response bubbles
are rendered only for a recorded response timestamp and stay linked by command ID.
ACK receipt is not inferred from command completion or treated as completion.
JSON payloads can be expanded and copied. Password/token/secret fields are redacted
from display and clipboard output.

Lifecycle system messages use actual command_events records, deduplicated by event
ID. Late snapshots cannot downgrade a newer command state. Node caches isolate
conversations. Live changes preserve the reading position unless the user is near
the bottom; older-history requests preserve their scroll position.

The backend permits creating a queued command for an offline target. The composer
therefore asks for explicit confirmation when the target is offline and never
claims delivery or execution from that action. Disabled nodes cannot be dispatched
from this UI. An active command for the selected node or an in-flight submission
disables Send. Zero maximum retries is preserved rather than replaced by a default.

Cancel and retry use the existing endpoints and retry budget. A retry is blocked
while another command is active for the selected node. Errors stay visible in
the conversation or the status notice. No commands were submitted to the live
port 5000 server during verification.

## Existing APIs and events reused

- GET /api/nodes
- GET /api/commands?node_id=...&limit=30&offset=...
- POST /api/commands with the existing node_id, command_type, payload, priority,
  timeout_seconds and max_retries fields
- GET /api/commands/<command_id>/events
- POST /api/commands/<command_id>/cancel
- POST /api/commands/<command_id>/retry
- Shared gateway.socket: command_update, node_update, connect and disconnect
- Existing gateway request helpers and shared DOM patch helper

Polling checks node metadata every eight seconds and reloads command history when
Socket.IO is disconnected. Page exit removes listeners and timers. History loads
30 records per page, with older records loaded at the top or via Load older.

## Tests actually executed

- node --check dashboard/static/js/command_center.js: passed.
- python -m py_compile backend/server.py backend/command_manager.py: passed.
- python tests/test_gateway.py: all 14 existing regression tests passed.
- node tests/command_chat.cjs: passed against the disposable gateway on port 5057.
  Covers command dispatch, zero retries, duplicate-send prevention, ACK without
  false completion, linked real response, JSON copy, event deduplication, node
  switching, history after refresh, timeout/retry/cancel, offline confirmation,
  35-record pagination, mobile Back to Nodes, light/dark and no page exceptions.
- Read-only browser checks on live port 5000: registered nodes, empty history,
  configuration expansion, mobile node selection and no horizontal overflow.
- Responsive widths checked: 1600, 1024 and 390 px.
- Desktop and mobile screenshots inspected.
- git diff --check for the edited existing page files: passed.

## Limitations

No physical device execution was exercised; command/ACK/response tests used actual
backend routes in the disposable fixture database. The live nodes were offline.
The page reports those states without fabricating a successful device response.

The UI preserves the project's current command API access policy. No new role
restrictions or communication transports were added. Unknown device capabilities
continue to be handled by the existing backend/device command implementation.
