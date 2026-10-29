# Compact Gateway UI — 25 October 2026

Implemented a maximum 1000 px login card with equal desktop panels, compact 48 px controls and local Orbitron 800 SVG text branding. Flat color, no wordmark shadows/gradients or remote assets. Mobile uses full-width stacked panels so the form remains usable rather than forcing two narrow columns. Brand spelling remains SELVARITHIK as in the provided artwork.

Replaced navigation disclosure arrows with persistent category headings/icons. Page links and the red page header share an SVG icon macro with distinct device, sensor, mesh, broker, network, command, diagnostics, health, controls, local-IP and settings symbols. Existing routes remain unchanged.

Dashboard overview now displays connection summary only. Per-device vertical overview cards and the old global Node details toggle were removed from Dashboard. Each Live Telemetry device has ESP32 details, opening an accessible native dialog with compact responsive information fields, sensor status, query times and historical/offline warnings. Existing telemetry polling, filters, widgets and data remain.

Verification: 9 workspace unit/API regression tests passed; JavaScript syntax and git diff --check passed. Browser login checked at 1366×650 (equal 499 px panels, no page scrolling) and 375×812 (no horizontal/vertical page overflow, Sign In visible). Disposable isolated Gateway fixture on port 5057 tested normal login, dashboard render, absence of duplicate device overview cards, zero navigation disclosure summaries, opening/closing ESP32 details, three desktop columns and two mobile columns. No console errors observed. Fixture data are simulated UI evidence, not a new hardware test. Live server remains port 5000 with normal authentication. No firmware, credentials, Wi-Fi, MQTT, sensor settings or database schema changes.

Source backup: ignored data/system-audit/pre-compact-ui-20261025.zip. Screenshots: COMPACT_LOGIN_LAPTOP.png, COMPACT_LOGIN_MOBILE.png and COMPACT_TELEMETRY_DETAILS_FIXTURE.png. Temporary responsive viewport override reset; fixture stopped after testing.
