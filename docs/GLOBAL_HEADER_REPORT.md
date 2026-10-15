# Shared Header and Gateway Banner

## Latest Branding Follow-Up
The later request supersedes the banner-everywhere and theme-button details below.
The banner now appears only at `/`, is titled `SelvaRithik's A&D Lora Gateway`,
and contains no theme text/button. All other pages retain their own headings.
The sidebar uses the original `selvarithiks-ad-red-on-white.svg` beside uppercase
navy company text; the header uses `selvarithiks-ad-white-on-red.svg` before the
page title. Both are copied unchanged from the supplied ZIP and use contain sizing.
Sidebar interaction follows Sidebar-9: 0.35s width/highlight expansion and delayed
label reveal, extended to keyboard focus with reduced-motion support.

Revalidated: 60 route/theme/viewport cases, existing page interaction suite,
keyboard expansion/collapse, expanded branding fit, reduced-motion behavior,
JavaScript syntax and git diff --check. No backend changes in this follow-up.

## Scope
Only the shared header, heading area, gateway banner, favicon links and shared
theme handling changed. The sidebar markup and page-specific controls/layouts
remain intact. The old Dashboard-only banner was removed to prevent duplication.
No backend, protocol, authentication or API logic changed in this update.

The actual application has ten routes: /, /nodes, /sensors, /command-center,
/communication, /firmware, /logs, /system-overview, /system and /chat.
There are no MQTT, RS485 or Registers page routes in this project; none were
invented, renamed or substituted.

## Files Changed or Added
- dashboard/templates/base.html: includes reusable shared components and favicons.
- dashboard/templates/index.html: System Overview heading/description; removes
  redundant page-local banner only.
- dashboard/templates/partials/global-header.html
- dashboard/templates/partials/page-heading.html
- dashboard/templates/partials/gateway-banner.html
- dashboard/static/css/dashboard.css: replaces previous header/banner rules.
- dashboard/static/js/app.js: respects saved light/dark theme; updates indicator.
- dashboard/static/js/realtime.js: truthful LIVE/OFFLINE socket status text.
- dashboard/static/img/sr-white-transparent.svg and favicon.svg: exact originals
  extracted from the supplied logos-svg (1).zip, without changing SVG paths,
  viewBox, color or transparency.
- dashboard/static/img/favicon.ico (32px), favicon-192.png, favicon-512.png and
  apple-touch-icon.png (180px): rendered from the archive's square favicon SVG.
- tests/export_favicons.cjs: repeatable asset conversion.
- tests/global_header.cjs: new shared-component regression checks.
- tests/ui_interactions.cjs: updates the old header assertion to the new contract.

No files were deleted in this update. Earlier working-tree changes are unrelated
to this scoped update and were preserved.

## Behavior
The sticky 60px navy header starts after the unchanged desktop sidebar.
The current page title is left aligned; search, digital clock and actual socket
status are right aligned. Mobile retains the existing navigation opener.
Descriptions come from each page's existing Jinja block. Dashboard alone uses
System Overview / Real-time status of all gateway subsystems.

The banner uses the supplied white SR mark and the explicitly requested text
"Ziel Techniek Industrial Gateway". The ZIP contains SELVARITHIK assets, not a
Ziel Techniek logo. No replacement logo or font was generated/downloaded.
The theme indicator switches and persists the active light/dark theme. Theme
styling in this change is scoped to the shared components, not a redesign of
the page-specific content.

Favicons are served at /static/img/... using Flask's existing static handler.
No root-level routes were added merely to mimic the example HTML paths.
The explicit links work on the local IP address too.

## Tests Actually Performed
- PASS: 60 checks: all ten routes at 1440, 768 and 360 pixels in light and dark.
- PASS: HTTP 200, no browser page errors or failed asset/API responses in those
  checks; one header/heading/banner per route; no body horizontal overflow.
- PASS: header is 60px, starts at x=72 on desktop and x=0 on mobile; heading is
  below header, banner is below heading; header controls fit.
- PASS: clock advances; connected socket displays LIVE, disconnect displays
  OFFLINE; theme button changes theme and label.
- PASS: six logo/favicon URLs; PNG and ICO dimensions match requested sizes.
- PASS: SHA-256 of both copied SVGs matches original ZIP entries.
- PASS: existing interaction suite: live telemetry, stable focus/DOM, staleness,
  widget/graph operations, sidebar, node form, sensor drawer/live values,
  command/history popup, Network settings, Firmware tabs/upload panel,
  Logs filters, System configuration and Chat send/mobile.
- PASS: 14 isolated backend regression test groups.
- PASS: node --check for all top-level frontend JavaScript files.
- PASS: git diff --check, with only existing Git line-ending warnings.
- Inspected desktop and mobile screenshots, including dark shared components.

Tests run against a disposable database on port 5057, not production data.
No hardware radio delivery, physical OTA flashing or real reboot was exercised.
Screenshots and JSON results are under ignored tests/artifacts/.
