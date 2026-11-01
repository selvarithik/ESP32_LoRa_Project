# Proposed interface - design review only

This folder is isolated from Flask routes and production static assets. It does not connect to devices or brokers and changes no settings. Open index.html to switch between Command Center and MQTT designs and toggle the command configuration. Narrow windows show the mobile screens. PNGs are static design renderings, not screenshots of an implemented application.

Inspected: existing shared header, Command Center template/styles, MQTT template, profile/runtime API, diagnostic API, local font assets and canonical MQTT contract. Existing red branding and company SVG are reused.

Existing support: selected-node command workflow, durable command history, correlated ACK and RESPONSE, saved profile templates, candidate test/confirm/cancel, connect/pause, verified TLS/authentication and bounded QoS 1 PROBE diagnostics.

Missing general MQTT support: arbitrary publish, dynamic subscribe/unsubscribe and an observed live message feed. Their design placeholders are disabled. No fake messages or topic counts stand in for those APIs. Verified TLS and canonical QoS 1 stay mandatory, regardless of the generic alternatives listed in the prompt.

Planned application edits after design review:
- dashboard/templates/partials/global-header.html and dashboard/static/css/geometric-header.css: compact shared header, existing navigation and actions retained.
- dashboard/templates/command_center.html; dashboard/static/css/command-center-chat.css and command-responses.css; dashboard/static/js/command_center.js: compact conversations, node filters, composer and expandable configuration, existing send/history APIs preserved.
- dashboard/templates/mqtt.html and scoped MQTT styles/scripts: connection/profile hierarchy, diagnostics and honest topic-area groundwork, preserving staging and the existing contract.

No production implementation, firmware upload, server restart, commit or push has been performed for this design task. Static screens were rendered at 1366x768 and 390x844 and visually inspected. Browser interaction acceptance tests have not been run on the proposed application, because it has not yet been implemented.
