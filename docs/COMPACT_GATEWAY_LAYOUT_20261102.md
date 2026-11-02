# Compact Gateway layout corrections — 2 November 2026

Implemented the eleven latest dashboard annotations on the Gateway only. Reference: docs/design-preview/selva-red-dashboard/selva Red Dashboard.html; its concept data and actions were not adopted.

- Device name/ID, quick facts, detail action and status share one compact desktop header row; duplicate name/ID text is suppressed. Mobile wraps for readability. Full details remain in the existing dialog.
- My widgets moved before Live Telemetry, preserving the existing widget handlers, saved layout choices and sensor configuration.
- Banner shortened (desktop104px target), exact solid #2A52BE, with SELVARITHIK AEROSPACE & DEFENCE on one responsive NASA-style line and existing reported Gateway/frequency/uptime facts.
- Top header is #B80F0A. Desktop menu button hidden; existing hover/focus navigation still expands/collapses. Mobile retains its accessible menu button. Navigation icons increased from19px to22px.
- Summary cards use the referenced compact white surfaces, right-aligned icon tiles and muted notes; all four actual live counters remain.
- Communication-path panel added before the banner using the reference's three-node/dashed-line design. The existing operations feed supplies real connection state. A bounded GET of the sanitized active-profile metadata supplies provider/TLS/QoS policy; it never stages or changes a profile. Dots animate only for verified broker and fresh reported MQTT link states; the panel explicitly distinguishes link state from command execution proof.

## Tests and deployment
60 real Flask fixture page/viewport checks passed (15 pages at1366/1071/768/375px), including colours, widget/workflow order, short banner, compact device header, desktop menu removal, hover expansion, mobile navigation, sticky-header bounds, live fixture telemetry ingestion/refresh and reduced motion. Four targeted approved-workspace Python tests passed, as did the existing Command Center and readable-control browser integrations. The banner/path unit tests cover unverified TLS, broker disconnect, unknown/multiple Masters, historical uptime, E220 channel bounds and sanitized diagnostic summaries. The earlier195-test full Python run remains historical; no Python backend changed in this UI task.

Production release: dist/Gateway-compact-ui-20261102, selected by deployment/active-release.json. Previous releases retained. The verified encrypted backup was created before deployment. Production CSS/JS requests return200 and match source. MQTT/local-IP documents, protected secret files and all sensor/parameter/graph settings fingerprint unchanged across deployment. No ESP32 code, flash, Wi-Fi or device settings were touched. No physical sensor/RF/command test was run for this UI task; screenshots are isolated fixture data.
