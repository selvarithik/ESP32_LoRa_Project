# Gateway page refresh fix — 2026-10-19

The local ESP32 transport emitted `telemetry_update.parameters` as a raw object, while the dashboard and Sensors controllers consume a list of persisted parameter records. A connected Socket.IO connection also disabled periodic reconciliation, so the handler error left readings frozen until manual reload.

## Changes

- `backend/device_api.py`: after commit, emit normalized persisted/transformed records with `node_id`, `received_at`, metadata, values and timestamps. Duplicate packets do not emit duplicate telemetry updates.
- `dashboard/static/js/app.js`: shared bounded, non-overlapping background refresh lifecycle; pauses hidden pages, refreshes on return and restarts on browser cache restoration. Common requests bypass cache and have a 12-second timeout.
- Dashboard: reconcile every five seconds even with a connected socket; preserve readings on transient failure, preserve focused controls and filter selection, reject malformed live events safely, update inline chart samples from both socket events and snapshots.
- Nodes: periodic refresh and socket-triggered reconciliation, no repeated loading placeholder, keyed row patching with one listener per button. Search/filter and focused controls remain intact.
- Sensors: reconcile despite a connected socket; update sensor management records in place, keep the sensor editor intact, validate incoming event shape.
- Network summary, System overview, local-IP diagnostics, MQTT status, commands, firmware status and chat refresh paths: lifecycle/reconciliation fixes, while settings forms retain drafts. Logs keep their opt-in auto-refresh setting and no longer blank the table on each successful refresh.
- Shared socket reconnects after back/forward cache restoration. Script URLs were versioned so one browser reload fetches the fix. Navigation, red header and CSS design were preserved.

## Verification

| Category | Evidence |
|---|---|
| Backend tests | 77 passed in 37.280 seconds, including actual local-transport Socket.IO event schema, committed values, metadata and duplicate suppression. Two existing SQLite ResourceWarnings remain. |
| JavaScript | All page scripts passed `node --check`; `git diff --check` passed. |
| Page smoke | 33 checks: 11 routes at 1440, 768 and 375 px. All HTTP 200, no browser exceptions, no body overflow. |
| Local-IP configuration UI | Three widths passed actual Flask login/CSRF/private-bind validation/save/readback checks. |
| Refresh regression | Signed local TCP exchange -> SQLite -> real Socket.IO -> browser card; search/focus/DOM preservation; deliberately missed event reconciled while socket stayed connected; inline chart updated; outage retained readings; simulated page-cache restore; Sensors and Nodes background refresh; all monitoring/settings routes loaded. |
| Physical runtime | Existing ESP32 DHT readings continued after the Gateway restart; latest checked row was one second old. No physical sensor values or credentials were modified for browser tests. |

The browser refresh tests use a disposable database and a software device, separate from the physical runtime observation. Back/forward restoration is tested by browser lifecycle events; this is not an extended browser/network soak test. MQTT remains ACL_CONFIRMATION_REQUIRED; no broker connection tests or firmware upload were needed for this fix.

## Run again

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
# Separate terminal, disposable test service only:
.\.venv\Scripts\python.exe tests/refresh_fixture.py
# Then:
node tests/refresh_ui.cjs
```

For the 33-route smoke test, run `tests/gateway_fixture.py` on port 5059, set `GATEWAY_TEST_URL=http://127.0.0.1:5059`, then run `node tests/ui_smoke.cjs`.

The real dashboard remains http://127.0.0.1:5000/. Reload the browser once (Ctrl+F5), sign in normally, and open Dashboard. Subsequent sensor updates do not require manual page reload. Five-second polling is the recovery path; ordinary live events update immediately. Settings pages intentionally do not repeatedly overwrite configuration forms with server values.
