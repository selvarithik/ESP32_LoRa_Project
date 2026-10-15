# Sensor Management, Live Cards and Sensor Details

Implemented in: D:\esp32 selva\ESP32_LoRa_Project
Preview: http://127.0.0.1:5000/
No commit was created. Existing working-tree changes were preserved.
Pre-edit source backup: D:\esp32 selva\sensor-feature-backup-20261015

## Workflow

Open Sensors to access Sensor Management. Sign in through Account Settings with
an administrator or creator account to edit definitions. Viewing remains available
under the gateway's existing read-access policy.

The catalog offers 30 templates and a five-step Add Sensor wizard. Select a template,
enter the actual parameter ID and sensor identifier, assign an existing node,
map a normalized payload field, configure numeric scale/offset or state/GPS display,
set units, precision, thresholds, reporting expectations and freshness timeout,
then optionally select Add to dashboard.

Test source inspects an actual stored field and its timestamp. It explicitly does
not claim to test a current physical connection. New custom sensor types are created
through the same form; no HTML or JavaScript edits are needed.

Definitions are the existing sensor_parameters records. Enable/disable controls
collection through save_parameters; display_enabled independently controls widget
visibility. Hidden sensors retain definitions and historical readings. Delete is
blocked while readings exist. Reordering uses accessible up/down controls and
persists position in the sensor's widget_config. Shared positions and visibility
are gateway-wide, matching the existing model; they are not per-user dashboards.

The dashboard's Add Widget picker searches configured enabled hidden sensors.
Removing a card clears display_enabled. Existing unrelated custom-widget features,
node details, counters, alarms and logs remain available.

## Data and UI

The first four existing core types selected at migration are Temperature, Pressure,
Battery Voltage and RSSI. Other configured metrics can be selected in management;
catalog templates alone do not create sensors.

Cards form a responsive two-column grid with real values, timestamped one-hour
history, metric accents, source freshness, and graph expansion. Separate automatic
history widgets were replaced by integrated card graphs.

Sensor Details uses the clicked sensor and the node's available parameters.
It supports 1/6/24-hour and 7-day history, unit-labelled numeric Y axes, timestamp
X axes, SVG point tooltips, exact readings and full-window numeric statistics.
Text/state/GPS metrics show recorded values and event history without numeric
averages. No additional chart or map dependency was added; the project already
used SVG graphs. No map integration existed to reuse.

History responses cap plotted/table-source records at the latest 10,000; numeric
statistics cover every reading in the window. The expanded table renders at most
1,000 rows and labels that limit. Dates follow the gateway's existing local
timestamp convention. Future hardware integrations should standardize timestamps
before mixing timestamps from different time zones.

The popup closes by close button, Escape or backdrop and restores focus/scrolling.
Requests are sequenced so a late response cannot overwrite a new sensor/range.
The existing WebSocket and polling mechanisms continue to update card values.

## Persistence and migration

An additive widget_config TEXT column is added to sensor_parameters. It stores
validated JSON for display metadata, source field, conversion, thresholds, stale
timeout and ordering. Existing tables and history are not dropped or reset.

feature_migrations records sensor-widgets-v1. During its first run only,
unconfigured legacy records select the four core types for initial visibility.
Configured definitions are preserved on subsequent startup.

Configuration writes use existing node parameter/graph APIs, existing account
sessions and CSRF protection; administrator or creator access is required.
The existing auth context supplies the CSRF token to the shared request helper.
No parallel sensor registry or credentials store was introduced.

## Endpoints

- GET /api/sensor-catalog: 30 templates, actual source capability information.
- GET/POST /api/nodes/<node>/parameters: reused definitions and creation.
- GET/PUT/DELETE /api/nodes/<node>/parameters/<parameter>: reused editing/deletion.
- POST /api/nodes/<node>/parameters/<parameter>/enable: reused enabled state.
- GET /api/nodes/<node>/parameters/latest: reused source observation.
- GET /api/nodes/<node>/telemetry/<parameter>?hours=1|6|24|168: optional window
  extension to the existing history endpoint, including full-window statistics.
  Existing requests without hours retain their previous response shape.
- GET /api/live/snapshot and telemetry_update WebSocket: reused dashboard updates.

## Exact files

Created:
- backend/sensor_widgets.py: catalog, additive migration, validated configuration,
  sensor-write authorization and historical-data deletion guard.
- dashboard/static/js/sensor-widgets.js: cards, SVG history, details popup and picker.
- dashboard/static/js/sensor-management.js: management, source observation and wizard.
- dashboard/static/css/sensor-widgets.css: scoped feature styling.
- tests/test_sensor_widgets.py: isolated backend feature tests.
- tests/sensor_widgets.cjs: isolated browser workflow.
- docs/SENSOR_MANAGEMENT_IMPLEMENTATION.md: this report.

Modified:
- backend/server.py: register feature, windowed existing history and mapped update metadata.
- backend/sensor_manager.py: atomic widget configuration persistence and close failed inserts.
- backend/telemetry_manager.py: managed field mapping/conversion and metadata exposure.
- backend/account_settings.py: expose existing session CSRF token in template context.
- dashboard/templates/base.html: shared CSRF metadata.
- dashboard/templates/index.html: requested telemetry section and integrated graph assets.
- dashboard/templates/sensors.html: management region alongside existing sensor table.
- dashboard/static/js/app.js: send existing session CSRF token on shared requests.
- dashboard/static/js/dashboard.js: configuration-driven cards and shared details popup.
- tests/gateway_fixture.py: isolated account database and authorized sensor-edit fixture.

## Validation executed

- Python regression: tests/test_gateway.py, 14 tests passed.
- Python feature: tests/test_sensor_widgets.py, 4 tests passed.
- Python account regression: tests/test_accounts.py, 1 test passed.
- Node browser workflow: tests/sensor_widgets.cjs passed against disposable port 5057.
  Covers sign-in, wizard create, telemetry mapping, selected sensor, unit labels,
  range changes, actual statistics, negative RSSI, Escape/backdrop, remove/re-add,
  desktop/mobile and light/dark, with no JavaScript exceptions.
- Live port 5000 read-only check: four core cards, popup and missing-history state,
  close/scroll restoration and no JavaScript exceptions.
- JavaScript syntax checks for changed feature code and Python compilation executed.
- Git whitespace check executed and whitespace introduced in sensor_manager corrected.

## Limitations

Only normalized node telemetry is exposed as a source adapter. Direct MQTT
subscriptions, Modbus polling, gateway CPU/memory diagnostics and hardware
connection tests were not present as working sensor integrations to reuse.
Templates for those metrics remain available for configuration against actual
published fields, and unavailable direct sources are labelled.

Packet loss, RTT, link quality and similar metrics are not guessed or computed
from unrelated values. They require a real configured upstream measurement.
No external notifications are sent. Per-sensor retention policies were not added
because the existing backend has no such policy engine; deletion retains history
by refusing to delete sensors with recorded samples.

The live gateway's stored readings are older than the requested short windows.
Empty graphs and N/A statistics are intentional. Synthetic readings were used
only in the disposable test database, never published to port 5000.
