# Approved Gateway red/black design — 2 November 2026

Applied the supplied updated Figma Make design as a presentation layer over the existing Flask application, not a replacement React/sample-data application. The source archive was read as design input; its package scripts and external Google-font import were not executed or adopted.

## Implemented
- Warm white canvas, black navigation, Figma red #e7222e active page/hover treatment, dark device headers and a black SR Gateway banner.
- Existing NASA-style SVG header preserved; supplied Orbitron and Michroma fonts served locally. No CDN or additional runtime dependency.
- All previous navigation paths and individual pages preserved, including the existing tools. No Private Chat or OTA feature development.
- Desktop navigation collapse/expand animation, mobile drawer animation, existing sticky-header scroll collapse, keyboard focus and reduced-motion support.
- Dashboard System events uses the existing sanitized /api/live/snapshot log feed. No invented events, device values, frequency or packet-success claims.
- Existing telemetry, history graphs, counters, filters, widget configuration, command forms and ACK/execution response handlers retained. Detailed network diagnostics remain available in a collapsible dashboard section and their original pages.

## Verification
- Gateway Python unittest discovery: 195 passed.
- tests/selva_red_ui.cjs: 15 real Flask fixture pages at 1366, 768 and 375 px (45 page/viewport checks). Black navigation, red selection, every previous navigation link, desktop collapse/mobile drawer, existing header collapse, event feed, telemetry ingestion -> live card update, filters, page errors and reduced motion covered.
- Existing Command Center browser integration, readable-controls integration, state predicate and result-renderer tests passed. Software simulated devices only; no physical board command was issued for this design task.
- Production CSS/JS/font requests return HTTP200 and match the source bytes. Protected MQTT and local-IP configuration documents, secret-store files and all sensor/parameter/graph configuration rows were fingerprinted before/after and compared unchanged. No credentials or fingerprint values are published here.
- Side-by-side frozen release: dist/Gateway-red-ui-20261102. The previous release remains available. deployment/active-release.json selects the new release. The server is running at http://127.0.0.1:5000; normal authentication remains required.
- An encrypted, verified local Gateway backup was made before deployment. No ESP32 files, flash, Wi-Fi, MQTT profile, sensor configuration or database schema was changed.

## Limits
Browser screenshots in tests/artifacts/selva-red use isolated sample data. They are design/test evidence, not hardware readings. New physical MQTT/sensor delivery and RF/LoRa tests were not part of this design change. The existing saved LAN-listener BIND_FAILED condition remains visible; its saved address was deliberately preserved. Restart may require users to sign in again.

## Files
Shared templates: base.html, index.html, partials/navigation-links.html, partials/gateway-banner.html. New assets: static/css/selva-red.css, static/js/selva-red.js and the two supplied local font files. Test: tests/selva_red_ui.cjs. Release selection: deployment/active-release.json.
