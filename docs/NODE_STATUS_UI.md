# Live Telemetry / All Nodes status indicators

2026-10-19: Green ONLINE and red OFFLINE labels and dots; subtle expanding rings; motion disabled by prefers-reduced-motion. Sensor Offline badges are red, stale sensor samples remain amber to distinguish sensor freshness from node connectivity. Offline cards retain their measurements as explicitly labelled last stored readings.

Offline explanation uses observed state only: disabled node, no heartbeat yet, invalid last-seen time, exceeded heartbeat timeout, or Gateway-reported offline status. It does not claim a particular physical failure. Timeout matches the existing Gateway rule: enrolled nodes use three heartbeat intervals, legacy nodes 60 seconds. The same helper drives dashboard filters/counters and sensor connectivity. A new heartbeat clears the offline warning.

Changed dashboard.js, sensor-widgets.js, dashboard.css, sensor-widgets.css and cache versions in base/index/sensors templates. No firmware, login, broker profile, navigation or database edits required.

Validation: tests/node_status_ui.cjs passed four combinations (light/dark, 1440/375 px): distinct green/red styles, explicit offline reasons, last-stored-reading label, both dot animations, reduced-motion override, online recovery removing the error, no page exceptions and no horizontal overflow. Tests use controlled snapshots in a disposable Flask fixture; physical node disconnection was not forced. JavaScript syntax and git diff whitespace checks pass.

Refresh the normal Gateway page once to load the new script/style versions.
