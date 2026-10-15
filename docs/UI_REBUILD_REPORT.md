# SELVARITHIK A&D Dashboard Update
Date: 2026-10-14

## Current Architecture
The user's later request superseded the from-scratch rebuild. The original
Flask/Jinja page structure is restored. The rejected modular frontend is
preserved outside the served dashboard in ignored _rejected_ui_rebuild/.
All ten routes remain available. The shell loads one dashboard.css stylesheet,
local Socket.IO, shared DOM/focus helpers, and existing page scripts.

## Latest Changes
- SELVARITHIK A&D branding, deep-blue sample-inspired header and dashboard banner.
- Company on the left, centered page name on desktop, search/date/time/connection
  on the right; responsive two-row header on narrow screens.
- Removed duplicate footer System link. Sidebar expands on hover/focus and
  retains mobile navigation.
- Graphs are independently added/removed, all chosen graphs remain visible,
  browser-persisted. Axes, real sample markers/tooltips, timestamps, statistics,
  and alternating blue/teal/purple series colors. No fabricated samples.
- Ten additional sensor presets/icons: pressure, flow, tank level, soil moisture,
  pH, light, gas, vibration, RPM and GPS. These are value-widget presets bound
  to real parameters, not ten new chart engines.
- Sensors merges parameter configuration with latest telemetry, receives socket
  deltas and uses fallback polling only when disconnected. View buttons use
  visible text-button sizing. Stable table rows preserve focus.
- Fixed drawer inert state during opening transitions, System loading/input race,
  and an undefined variable after command dispatch.
- Network topology now renders actual configured nodes and neighbor links.

## Earlier Cleanup and Fixes in This Working Tree
- Removed repeated hero headings, duplicate overview/Fleet blocks, oversized
  Command panels; retained original forms and routes.
- Dashboard snapshots plus socket deltas replace the two-second N+1 loop.
  Live cards are patched without replacing the container; stale data is gray
  after ten seconds. Command and Chat use the shared socket.
- Backend config_manager had chat-manager content instead of configuration
  functions. Restored persistent configuration load/save/reset and validation.
- Latest telemetry uses timestamp ordering rather than insertion ID; HTTP
  telemetry validation returns 400 for malformed requests.
- HTTP and legacy socket telemetry emit telemetry_update with real parameter
  metadata. Existing node_update and command/chat contracts remain.
- Configuration table and earlier dashboard-persistence backend additions remain;
  current chart/widget layout uses browser localStorage, not cross-device sync.

## Files
Changed templates: base, index, nodes, sensors, command_center, communication,
firmware, logs, system, system-overview, chat.
Shared frontend: dashboard.css, app.js, dom.js, realtime.js, accessibility.js,
local Socket.IO client/license and logo SVGs.
Page scripts: dashboard, nodes, sensors, command_center, communication, chat, system.
Backend: server.py, database.py, config_manager.py, telemetry_manager.py.
Support: README.md, .gitignore, docs, simulator/http_node.py and tests.

Deleted unused served files after reference audit: auth.css/auth.js/login.html
(login route redirects), separate chat/command_center/communication/firmware
stylesheets consolidated into dashboard.css. Historical versioned stylesheets
and redesign scripts already absent in the restored tree remain deleted.
Git status is the exact inventory; pre-existing changes were not reverted.

## Verification
- PASS: 14 isolated Python backend test groups, including ten page routes/assets,
  config CRUD, node/parameter CRUD, HTTP/socket telemetry, invalid telemetry,
  out-of-order latest data, all eight command types and lifecycle/retry,
  chat delivery/seen, logs, mesh settings, firmware release/download/job simulation.
- PASS: 30 browser page/viewport checks (all ten routes at 1440, 768, 375 pixels),
  HTTP 200, no page JavaScript errors, no horizontal body overflow.
- PASS: browser interactions for live update latency, stable DOM/focus,
  no connected polling, stale/recovery, telemetry popup/Escape, widget presets,
  add/remove graph persistence, sidebar hover, node form/filter, sensor live
  readings/View drawer, command send/history modal, network settings, firmware
  tabs/upload panel, logs filter, System save/confirmation, chat send/mobile.
- PASS: node --check for all top-level frontend scripts.
- PASS: py_compile for backend/protocol/simulator/test Python sources.
- PASS: git diff --check (Git emits line-ending warnings only).
- PASS: template audit finds dashboard.css as the only CSS reference and no CDN
  stylesheet/script dependency or manual-collapse handler.
Tests use a temporary SQLite database and firmware directory, not real devices.
Browser captures/results are generated under ignored tests/artifacts/.

## Limitations
Physical ESP32/LoRa delivery, radio performance, real OTA flashing and actual
machine reboot were not exercised. Browser testing is Edge/Chromium, not every
browser or assistive technology. A 60-second backend outage recovery soak and
formal AA contrast audit were not run. Charts/widgets persist in this browser.
No claim is made that every possible backend or hardware issue is eliminated.

## Run
python backend/server.py
Open http://127.0.0.1:5000/.
For isolated regression checks:
python tests/test_gateway.py
python tests/gateway_fixture.py
node tests/ui_smoke.cjs
node tests/ui_interactions.cjs
Stop the fixture after browser tests.
