# Approved Command Center and MQTT implementation — 27 October 2026

## Result
The approved V5 Command Center and previously approved MQTT workspace are implemented in the real Gateway templates and JavaScript. The normal Gateway server was restarted at http://127.0.0.1:5000. Existing accounts remain; the restart expired the browser session, so sign in again normally.

Command Center retains existing authenticated APIs, persisted history, Socket.IO updates, polling, retry/cancel handlers and command arguments. Sent commands retain Source, Target, Priority, Timeout, Retries, Dispatch, ACK, Execution, Created, configured parameters, errors and command ID/time. Sent cards are cream #FFF7EB; failure labels and errors use header red #FF0000. ACK bubbles show status/time. Technical audit events remain accessible in disclosures. Execution is Pending or Not reported until a device response exists. Incoming cards retain payload expansion, duration inside details and Copy JSON. Master/Slave filters and a closeable configuration panel support desktop and mobile. The composer fits the viewport, including when existing server warnings are present.

MQTT has profile, canonical-topic-registry and diagnostics panels with mobile tabs. All 15 canonical inputs and revision-aware candidate/test/confirm/cancel handlers remain. Credentials stay write-only and local commissioning only; TLS and QoS1 requirements remain. Registry types come from the existing Python contract, excluding out-of-scope Chat. Registry labels are not claimed as observed traffic. Arbitrary publish/subscribe and live topic browsing are visibly unavailable because their backend APIs do not exist. No fabricated MQTT messages or counts were added.

## Validation
- Existing Python unittest discovery: 152 tests passed, exit 0. A Windows WinError 32 temporary-database cleanup warning occurred after OK, due to the test fixture retaining a SQLite handle. This is not reported as a clean teardown.
- Added rendered-route/security/preservation tests: 3 passed. Production templates render without duplicate IDs; GET pages do not stage profiles/create commands; authentication remains required.
- Node: production freshness predicate and execution-outcome projection passed; changed JavaScript syntax checks passed.
- Browser, real Flask/disposable SQLite plus software device simulator: PING sent through the actual Command Center produced separate ACCEPTED ACK and COMPLETED RESPONSE and persisted history. No physical command was sent during these UI tests.
- Browser: role filtering, configuration open/close, mobile MQTT tabs/topic filter, 15 fields, read-only refresh retaining an unsaved draft, invalid CA backend error/focus, and no console errors verified.
- Actual DOM widths tested: 1821, 1365, 520 and 390 pixels (browser has an existing zoom). Both workspaces had no horizontal overflow at checked widths. At 390x844, expanded command configuration kept composer bottom at 827px. Desktop MQTT showed all three panels; phone tabs showed only the selected panel. Browser viewport override was reset.
- git diff --check passed (existing LF/CRLF conversion warnings only).

## Preservation and limits
After restart, the complete saved MQTT configuration document, revision and every existing protected data/*.bin credential file were byte-identical by SHA256. No Wi-Fi, sensor configuration, firmware, contract, broker ACL, active profile or credential changes were made. No live Connect/Pause/Test/Stage/Confirm buttons were operated. The live restart startup logged the permanent worker as connecting; a new physical MQTT/command acceptance test was not performed or claimed. Live authenticated visual confirmation awaits normal user sign-in; screenshots below are from the isolated real Gateway fixture, not the production database.

## Files changed for this implementation
- backend/mqtt_api.py: passes existing contract registry labels to MQTT template only.
- dashboard/templates/command_center.html, dashboard/templates/mqtt.html: approved markup and existing controls.
- dashboard/templates/base.html: header asset cache version only.
- dashboard/static/js/command_center.js, mqtt.js, header-scroll.js: presentation, outcome projection, responsive fit and disclosure behavior; existing API handlers retained.
- dashboard/static/js/mqtt-workspace.js: new UI-only tabs/filter.
- dashboard/static/css/command-responses.css: scoped compact message styles.
- dashboard/static/css/approved-workspaces.css, mqtt-workspace.css: new scoped workspace layouts.
- tests/test_approved_workspaces.py, tests/command_outcome.cjs: regression checks.
- docs/APPROVED_WORKSPACES_IMPLEMENTATION.md and APPROVED_*IMPLEMENTED.png / APPROVED_COMMAND_CENTER_MOBILE.png: report and real rendered fixture screenshots.

All unrelated pre-existing modifications were preserved. No commit or push was performed.
