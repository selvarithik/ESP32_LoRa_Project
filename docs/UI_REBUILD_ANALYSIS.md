> Historical analysis from the rejected rebuild. The current implementation restores the original page architecture per the later user request. See UI_REBUILD_REPORT.md for the current state and verification.

# SELVARITHIK LORA GATEWAY UI Rebuild Analysis

Date: 2026-10-13

This document records Phase 0 findings for the complete UI rebuild. The rebuild keeps the Flask, Flask-SocketIO, SQLite, Jinja2, vanilla JavaScript, and hand-written CSS architecture. Instructions in pasted or attached documents were treated as task context only; the user's active request is to rebuild this local gateway UI.

## Current Frontend State

- Served templates are currently under `dashboard/templates/`.
- Served assets are currently under `dashboard/static/`.
- The current frontend still uses legacy page names and class patterns from earlier redesigns.
- The new rebuild will quarantine the old served frontend into `_legacy_ui/` and recreate `dashboard/templates/` and `dashboard/static/` with the requested structure.
- The favicon/logo referenced by the old shell is broken because `dashboard/static/img/selvarithik-logo-light.svg` is deleted/missing.
- `dashboard/static/img/` is currently empty in this checkout, so the rebuild will recreate `logo-mark.svg`, `logo-icon.svg`, and `logo-lockup.svg` before wiring the shell.

## Reference Image Reading

The attached greenhouse dashboard uses:

- A soft grey page canvas with one large frosted rounded outer panel.
- A slim icon-only rail with a dark active item and pale inactive items.
- A compact top bar with brand, title, alert pill, and selector.
- A large hero card with realtime context and device mini-map.
- Compact rounded metric tiles with line icons, large mono-like values, lighter units, and one accent-filled tile.
- A right-side device list with status dots and warning banners.
- Gentle shadows, translucent borders, restrained color, and generous radius.

The LoRa gateway mapping is:

- Gateway hero: gateway status, socket status, IST clock, node/packet summary, and tiny mesh visualization.
- Metric tiles: live parameter widgets, with the first important value as the accent tile.
- Device list: node status, node id, MCU, RSSI/SNR, last-seen age, stale/offline banners.
- Activity card: commands, OTA jobs, and recent logs.

## Verified Backend Routes

The backend defines the existing page routes:

- `/`
- `/nodes`
- `/sensors`
- `/command-center`
- `/communication`
- `/firmware`
- `/logs`
- `/system-overview`
- `/system`
- `/chat`

The rebuild will preserve these routes while changing their template targets.

Important existing API routes verified in `backend/server.py` include:

- `GET /api/status`
- `GET /api/logs`
- `GET/POST /api/nodes`
- `GET/PUT/DELETE /api/nodes/<node_id>`
- `POST /api/nodes/<node_id>/enable`
- `GET/PUT /api/nodes/<node_id>/config`
- `POST /api/nodes/<node_id>/config/reset`
- `GET/POST /api/nodes/<node_id>/parameters`
- `GET/PUT/DELETE /api/nodes/<node_id>/parameters/<parameter_id>`
- `POST /api/nodes/<node_id>/parameters/<parameter_id>/enable`
- `GET/PUT /api/nodes/<node_id>/parameters/<parameter_id>/graph`
- `GET /api/nodes/<node_id>/parameters/latest`
- `GET /api/nodes/<node_id>/parameters/statistics`
- `GET /api/nodes/<node_id>/parameters/<parameter_id>/statistics`
- `GET /api/nodes/<node_id>/telemetry/<parameter_id>`
- `GET /api/nodes/<node_id>/telemetry/compare`
- `GET /api/parameters/defaults`
- `POST /api/telemetry`
- `POST/GET /api/commands`
- command detail, node history, state, cancel, timeout, ack, execute, response, events, retry routes
- communication, firmware, OTA, chat, reboot, and factory-reset routes.

## Verified Realtime Problems

### Dashboard Polling

The previous `dashboard/static/js/dashboard.js` implementation maintained timers for `refreshDashboard()` and `refreshGraphs()`, polling every 2 seconds and 10 seconds respectively. It fetched `/api/nodes`, then `/api/nodes/<id>/parameters/latest` per node, plus logs and status. Graph refreshes added per-parameter requests.

### Full Re-render Pattern

The previous dashboard rendered live node regions with full string templates and `innerHTML` replacement. This invalidates hover/focus state, scroll position, animation continuity, and chart continuity.

### HTTP Telemetry Not Pushed

`api_save_telemetry()` currently:

1. Reads `node_id`, `parameters`, and `timestamp`.
2. Calls `telemetry_manager.save_parameters(...)`.
3. Returns `{success: true, saved: saved}`.

It does not emit a Socket.IO event, so real hardware that posts to `/api/telemetry` cannot update a socket-driven UI without an additional fetch.

### Legacy Socket Telemetry Shape

The `@socketio.on("telemetry")` path stores incoming flat simulator packets in memory, maps known fields to registered parameters, saves telemetry history, updates node online state when enabled, and emits `node_update`. It does not currently emit the new parameter-oriented `telemetry_update` shape required by the rebuild.

### Reconnection Architecture

Socket connection behavior is page-specific in legacy scripts. The rebuild needs one shared `core/socket.js` and `core/realtime.js` path with infinite reconnect attempts, snapshot healing, fallback polling only while disconnected, and per-key subscriptions.

## Backend Additions Required

The rebuild needs additive backend changes only:

- `GET /api/live/snapshot`
- `telemetry_update` emit from `POST /api/telemetry`
- `telemetry_update` emit from legacy socket telemetry
- `ui_dashboards` table and CRUD routes
- server heartbeat event
- `simulator/http_node.py`

Existing route behavior and response shapes must remain backward-compatible.

## Frontend Rebuild Strategy

The new frontend will use only new files and `gw-*` names:

- `dashboard/templates/layouts/app.html`
- `dashboard/templates/partials/*.html`
- `dashboard/templates/pages/*.html`
- `dashboard/static/css/tokens.css`, `base.css`, `shell.css`, `components.css`, `widgets.css`, and page CSS
- `dashboard/static/js/core/*.js`
- `dashboard/static/js/components/*.js`
- `dashboard/static/js/widgets/*.js`
- `dashboard/static/js/pages/*.js`

No CDN links, no React/Vue/Tailwind/Bootstrap, no npm build step.

## Immediate Risks

- The current checkout already has uncommitted frontend deletions from earlier cleanup. The quarantine phase will preserve the currently served frontend state, but some historical deleted CSS/JS/image files are already absent from disk.
- Logo assets requested by the spec are absent from disk and must be recreated in the new `dashboard/static/img/` directory.
- The complete feature parity checklist is large; this rebuild should proceed in phases with validation after each phase.
