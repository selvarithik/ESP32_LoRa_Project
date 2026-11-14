# Browser Comment Fixes

- Compact communication path and Gateway banner; existing live bindings retained.
- Gateway wordmark uses the login page's locally bundled Orbitron font.
- Device headers use neutral surfaces, chip icons, readable identity/metadata and
  check/disconnected icons paired with explicit online/offline text.
- Layout button moved into the always-visible filter toolbar. Saved preferences
  now cover communication path, banner, events, Problems, My widgets and density.
  Reset restores all sections; hiding widgets cannot hide the Layout control.
- Sensor actions have distinct blue, green, amber and destructive red treatments.
  View buttons have 44px minimum height.
- Selected Command nodes have stronger inset highlights and filled device icons.
- System tabs have filled active states across Settings, Health and Device controls.
- Settings navigation/header share a new sliders icon. Logout is more compact.
- Logs now renders only the event-history controls/table. Diagnostics renders the
  connection/device overview and a link to Logs. Existing routes remain unchanged.

## Verification

Passed 48 browser checks: 16 routes at 1440, 1071 and 375px. No JavaScript page
errors or horizontal body overflow in these checks. Verified panel dimensions,
View-button height, icons, active tabs, layout hide/reload/restore/reset and distinct
Logs/Diagnostics regions. Additional checks passed for Command-node selection,
sensor details popup and dark-theme selected tabs. Ten workspace/backend tests
passed, including a new Logs/Diagnostics regression. JavaScript syntax and
git diff --check pass (Git line-ending warnings only).

Browser tests: tests/browser_comments.cjs, against tests/command_center_fixture.py
on port 5084 with a temporary database and software-only devices. Screenshots are
in ignored tests/artifacts/browser-comments/. No real device commands, hardware
tests, production-data changes or backend/protocol edits were performed.
