# Gateway revision 3 corrections — 2 November 2026

Reference: the owner-provided local revision3 preview and the twelve browser annotations. Gateway presentation only; no ESP32/firmware, Wi-Fi, broker profile, sensor configuration or packet changes.

| Annotation | Implemented change |
|---|---|
| 1 | Round pale-blue SR avatar with the existing account menu/status dot, matching the earlier profile style. |
| 2 | Restored the previous blue Gateway banner gradient. |
| 3 | Larger local Orbitron branding: SELVARITHIK / AEROSPACE & DEFENCE. Existing NASA-style top-header SVG retained. |
| 4 | Added Gateway ID, last reported Master uptime and E220 frequency from actual completed register observations. Unknown, multiple or missing reports are labelled explicitly. |
| 5 | Figma-style red Nodes card, coloured icon blocks, white companion cards and actual fleet counters. No sample packet-success percentage adopted. |
| 6 | System events aligned at the top of the right column, using the existing log feed. Structured diagnostics become concise, escaped, allowlisted summaries; full records remain on Logs. |
| 7 | Restored automatic sidebar hover/focus expand/collapse. The menu button can pin/unpin expansion. |
| 8 | Scrollbars hidden while wheel/touch/keyboard scrolling still reaches every navigation item. |
| 9 | Compact device header padding, typography, status and quick facts; complete ESP32 detail dialog retained. |
| 10 | Search icon explicitly centred and sized within its button, including compact/mobile headers. |
| 11 | Same compact device-header treatment for every node. |
| 12 | Problems directly below System events in the right column. Mobile stacks the column responsively. |

## Evidence
- tests/gateway_banner.cjs: actual E220 channel mapping/bounds, unavailable and multiple Masters, historical uptime and diagnostic summary secrecy/escaping.
- tests/selva_red_ui.cjs: 60 actual isolated Flask/SQLite page/viewport checks at 1366, 1071, 768 and 375 px passed. Tests navbar hover expansion/collapse and pinning, hidden scrollbar, events right-column/top alignment, avatar shape, icon centre, banner/data provenance, live fixture telemetry ingestion/refresh, navigation preservation, sticky-header overlap, mobile drawer and reduced motion.
- Targeted approved-workspace Python tests: 4 passed. Existing Command Center and readable-controls browser integrations passed with software simulated devices. Previous full Python suite: 195 passed before this frontend refinement; no Python backend change was needed here.
- Production assets are byte-checked against source after deployment. MQTT/local-IP documents, secret stores and sensor/parameter/graph configuration fingerprints compare unchanged. The Gateway is running at http://127.0.0.1:5000 using the new side-by-side dist/Gateway-red-r3-20261102 release; previous releases are retained.
- Screenshots under tests/artifacts/selva-red are software-fixture previews, not physical sensor readings. No physical commands/RF tests or firmware upload were performed.

The frequency formula is E220-900 register channel0=850.125MHz, step1MHz, valid channel0..83. It is displayed only after a successful settings-read observation and remains historical evidence, not an RF-link/regulatory verification. Uptime is the last reported Master uptime, not an invented continuously running timer. No new polling connection is added: the existing operations feed supplies the banner through a local DOM event.
