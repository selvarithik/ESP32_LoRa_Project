> Historical snapshot: BLE references below describe earlier revisions only. BLE is excluded and removed from active features as of 2026-10-19; see BLE_SENSOR_REPORT.md.

Historical report: newer local-IP implementation, application-only deployment and physical evidence are in [LOCAL_IP_REPORT.md](LOCAL_IP_REPORT.md).

# Login, accounts, setup and MQTT acceptance — 2026-10-19

## Current outcome

Software changes are implemented and the firmware builds. Gateway login is running at **http://127.0.0.1:5000/login**. The new firmware has **not been uploaded**, in accordance with the latest instructions. No live credential recovery, active secret replacement, flash erase, NVS reset, partition change or eFuse write was performed in this phase.

Two external blockers remain:

1. **Live MQTT authentication FAIL:** the existing secure-store credential is rejected by EMQX as **“Bad user name or password.”** Verified TLS succeeds. The same rejection occurred with the configured Gateway client ID, so it is not just a diagnostic-ID rejection. Paho VERSION2 reports normalized reason 134; the profile remains MQTT 3.1.1. Subscription readiness, broker PUBACK and end-to-end delivery are not established by this failed check. See `ACCESS_LIVE_BROKER_PROBE.json`.
2. **Physical acceptance NOT TESTED:** a final COM8 read failed with Windows error 31, “A device attached to the system is not functioning.” COM8 remains enumerated, but could not be opened. No reset/recovery/upload was attempted. Last verified station address was **192.168.1.105**, not the earlier DHCP address. See `ACCESS_FIRMWARE_LIVE_STATUS.json`.

The permanent Gateway worker remains **disconnected / ACL_CONFIRMATION_REQUIRED**. Its gate was not bypassed. Earlier successful physical MQTT/status/chat tests are historical, bounded diagnostics; they do not prove current credentials or continuous worker operation.

## Root causes and fixes

| Finding | Implemented fix | Evidence |
| --- | --- | --- |
| Gateway checked API authentication but did not protect normal page routes | One middleware protects dashboard, nodes, sensors, command/network/communication, firmware, logs, MQTT, system, chat and accounts; anonymous pages redirect, APIs return JSON 401 | Lifecycle tests and actual server HTTP checks |
| `/login` redirected to Account Settings | Dedicated responsive login form with visibility toggle, inline errors, disabled/loading state and fixed internal redirects | Real Flask/browser tests at 360/768/1440 px |
| GET logout was a no-op and signed cookies remained replayable | GET displays sign-out confirmation; CSRF-protected POST revokes a random server-side session; replay is rejected | Replay and real browser logout tests |
| Existing realtime connections could outlive account logout | Canonical session revocation disconnects matching Socket.IO sessions; idle sweep and role/password invalidation use the same registry; bootstrap accounts cannot open a normal realtime session | Actual Socket.IO test client disconnect assertion |
| No idle expiry; conflicting legacy credential repair path | 256-bit random session IDs, server-side idle expiry at 900 seconds, bounded registry, HttpOnly/SameSite cookies, Secure on actual HTTPS; legacy file creation/repair/authentication disabled | Session, cookie and idle tests; legacy helper is no longer a login provider |
| Account cap and explicit recovery missing | Eight-account cap and last-creator decisions serialized in SQLite; role checks retained; local preview/apply recovery with verified backup; no implicit empty-store default account | Limit, permission, preview, bootstrap, forced-change and other-account preservation tests |
| ESP32 Basic Authentication caused browser credential caching and repeated expensive verification | Browser session login/account/logout; no Basic bypass on administrative routes; PBKDF2 runs for login/account changes rather than normal requests | Firmware build, production session-core host tests, access UI tests; device execution pending |
| Password management normally required hidden terminal input | Browser Account page with current-password verification, confirmation, visibility toggle and feedback; optional explicit physical recovery retains forced first-use change | Access UI tests; physical NVS/reboot acceptance pending |
| Setup gave weak feedback and exposed unavailable controls | White/blue navigation and real status summaries; actual DHCP address; supported settings, field constraints, restart confirmation, saved revision and post-restart readback; unavailable Ethernet/BLE/E220 disabled | Source/assets checks and mocked firmware browser tests |
| MQTT status conflated connection and readiness | Separate TLS/auth/connection/subscription, queue, PUBACK, receive and persistence fields; QoS 1 SUBACK evidence required for READY; clock validity does not claim proven NTP synchronization | Unit tests and disposable TLS broker tests; new native ESP32 labels need physical verification |
| Generic network or broker refusals could be labelled TLS/auth failures | Shared native error classifier distinguishes MQTT 3.1.1 auth codes from other refusals and DNS/socket errors; Python also distinguishes normalized auth/refusal reasons | Production classifier host tests and Gateway callback assertions |
| Refresh could discard unsaved broker fields | Read-only refresh retains draft values; no client creation, publication or configuration action | Gateway read-only API assertions and ESP32 UI refresh assertions |
| Gateway MQTT form stopped rendering at its CA textarea | Removed assignment to the textarea's read-only type property; render all 15 fields, backend field errors/focus, operation loading and safe readiness controls | Focused real Flask MQTT UI test checks all 15 controls, invalid CA feedback and revision-preserving refresh |
| Disabled E220 branch accepted AUX failure, blocked on send and could parse overflow tails | Initialization fails closed; unsupported/disabled UART rejected; send requires ready AUX and immediate queue capacity; bounded receive discards through newline after overflow | Actual driver branch compiled/executed with host UART doubles; **not** RF/hardware evidence |

The ESP32 still has one local owner account, compatible with its existing credential model. Gateway roles remain `creator`, `administrator`, `user`; device roles remain `MASTER`, `NODE`. No unrelated account system, database, transport, topic or radio protocol was introduced.

## Reference and interface work

Inspected the provided Arduino reference folder:
`C:/Users/Admin/Documents/Arduino/ESP32 ZIEL TECH/TEST 2/new unziped/ZIEL_TECH_Industrial_Gateway_SD_MQTT_Backup_fixed`.

Adapted white cards, pale blue backgrounds, navy/blue navigation, 44-pixel controls, visible labels, password visibility, account feedback and responsive spacing. Gateway's existing red header and unrelated dashboard styling remain. Fonts/assets stay local; the reference's remote font import, credentials, configuration, hardware pins, security shortcuts and Registers/RS485 pages were not imported.

ESP32 routes now include `/login`, `/account`, dashboard, network, device, radio, nodes, system and MQTT. Configuration continues through existing APIs and NVS ownership. Wi-Fi/broker/mesh/token secret provisioning remains local USB/console; HTTP account password changes are explicitly requested and visibly warn that HTTP is unencrypted. Readback cannot be asserted while a device is unreachable or still rebooting.

Gateway Account Settings provides profile/identity/role information, account CRUD, current-password verification for own password changes, confirmation/visibility, default-password warning and reauthentication after updates. First-run bootstrap and recovery are deliberate local commands, not web backdoors.

Concept references were reviewed without importing deployment settings: [ESP-MQTT](https://github.com/espressif/esp-mqtt), [E220 library](https://github.com/xreef/EByte_LoRa_E220_Series_Library), [EMQX](https://github.com/emqx/emqx), [mqtt-io](https://github.com/flyte/mqtt-io), [harmony-api](https://github.com/maddox/harmony-api), [ECS](https://github.com/Dragolone/ECS), [LoRaMesher](https://github.com/LoRaMesher/LoRaMesher), [standalone E220 interface](https://github.com/dmahony/e220-standalone-wifi-esp32), [Serial Studio](https://github.com/Serial-Studio/Serial-Studio). Existing protocol and architecture remain authoritative.

## Preservation and migration

- Contract **1.0.1**, wire schema **1**, all 15 profile fields and 11 approved topics retained. Both contract copies remain byte-identical, SHA-256 **b91cac08abd7be3e0310140e53205b86aad728bbcf5de7e21a93e95b62ee9472**. Six production C++/Python canonical-byte/digest vectors pass. The existing full shared-setting matrix remains in `MQTT_IMPLEMENTATION_REPORT.md`.
- Actual Gateway profile remains revision **6**, shared revision **1**, `COMMITTED`, no candidate; existing hostname/8883/TLS, server client ID, prefix and GW001 retained. Firmware baseline was revision **53**, shared revision **1**, no candidate, identity ESP32-10777D842178 and its distinct client ID. No firmware write occurred; final hardware reread was unavailable.
- `accounts.sqlite3` received one additive `must_change` column. Existing identity/role/version rows were checked unchanged. Migration SQL does not replace password hashes. A consistent SQLite backup was created in Git-ignored `data/account-backups/` and verified before ALTER TABLE. No live account recovery was run.
- Existing `gateway.db`, `mqtt-secrets.bin` and `session.key` retained their original lengths and exact modification ticks across the Gateway restart/migration. This metadata check is not represented as a cryptographic file-content audit. See `ACCESS_LIVE_SERVER_EVIDENCE.json` and the baseline JSON files.
- Gateway secrets remain outside the database in current-user Windows DPAPI storage. New ESP32 username metadata is local to the existing `login_v1` credential record; legacy records default to the existing owner name without rewriting credentials at boot.
- The private-default scanner found zero occurrences of the existing securely stored Wi-Fi/MQTT passwords in checked source/document files and the final image; this is a scoped check, not a universal secret audit. No password copied from the prompt was embedded or substituted into active storage. Since a credential was pasted into chat, rotate it through authorized EMQX management as appropriate, then update protected stores through the approved coordinated provisioning process. No rotation was performed here.
- Historical read-only security inspection showed ESP32 flash encryption and Secure Boot disabled. No enabled-at-rest encryption claim is made for its Wi-Fi/MQTT NVS secrets.

## Test results

| Category | Status / result | Limit |
| --- | --- | --- |
| Gateway unit/API regression | **PASS: 67 tests** | Temporary databases; targeted 10-test access suite rerun after final recovery safeguards |
| Gateway login/account browser | **PASS: 360, 768, 1440 px** | Real Flask fixture + SQLite, invalid/valid login, visibility, CRUD, logout, API 401; not production credential recovery |
| Existing Gateway UI | **PASS: 33 route/viewport checks; 9 interaction groups** | Dashboard, nodes, sensors, commands, communication, firmware panels, logs, system, chat |
| Focused Gateway MQTT browser | **PASS** | All 15 fields, real backend certificate error/focus, mobile layout and read-only revision-preserving refresh; an initial timeout exposed the textarea bug and passed after repair |
| Actual Gateway public HTTP | **PASS** | Login 200; protected pages 302 to login; anonymous MQTT API 401; worker startup reports ACL gate |
| Firmware local/MQTT/access UI | **PASS: six viewport cases** | Mocked HTTP; never represented as real ESP32 handler/NVS evidence |
| Native production session core | **PASS** | Revocation, idle/sliding timeout, generation invalidation, timer wrap, CSRF comparison, bounded eviction |
| Native production MQTT error classifier | **PASS** | Authentication, non-auth broker refusal, TLS stack/certificate and generic transport cases |
| E220 production UART branch | **PASS with host doubles** | AUX failure, TX pressure/readiness, bounded RX, overflow-tail discard/recovery; no physical UART or RF |
| Contract/assets | **PASS** | Identical hash, six C++/Python vectors, all three source/gzip round trips |
| Disposable local TLS brokers | **PASS: 4 tests** | QoS 1 persistence/dedup, verified SUBACK readiness, certificate/hostname/auth rejection, two-broker switch with software Master |
| Current live broker diagnostic | **FAIL: MQTT AUTH_FAILED** | TLS verified; broker says bad user name/password; no subscription, publication or persistence asserted |
| Permanent hosted worker | **BLOCKED** | Required ACL verification absent; flag remains unset; credential rejection is an independent blocker |
| New firmware physical acceptance | **NOT TESTED** | No upload permitted; final COM8 error 31; new browser password persistence/reboot/CSRF/heap soak need hardware |
| Current real permanent-worker telemetry/dashboard/commands | **NOT TESTED** | Do not substitute historical bounded diagnostics or fixture rendering |
| E220 configuration/readback/Master-Node RF and DHT | **NOT TESTED** | Actual module/pins/power/antenna/region required; TransportManager radio path remains unavailable |

Existing SQLite connection ResourceWarnings and upstream Paho failed-handshake socket/amqtt fixture warnings appeared. One broker run concurrent with a full firmware rebuild failed its five-second SUBACK deadline and emitted an amqtt cancellation warning. An isolated rerun with unchanged assertions passed all four tests in 3.233 seconds. Timing stability under CPU contention is not claimed; warnings remain known limitations. A missing-header include-order build error was corrected before the final successful build.

## Build and partition decision

Final default `esp32dev` build **PASS**, espressif32 7.0.1 / Arduino 2.0.17, previously verified ESP32-D0WDQ6 revision 1.0 with 4 MB flash.

| Measurement | Actual value |
| --- | --- |
| PlatformIO application usage | **1,251,185 / 1,310,720 bytes (95.5%)** |
| Generated firmware.bin | **1,257,760 bytes** |
| Image headroom / program headroom | **52,960 / 59,535 bytes** |
| Static RAM | **59,492 / 327,680 bytes (18.2%)** |
| NVS | 0x9000 + 0x5000 (20,480 bytes) |
| OTA metadata | 0xe000 + 0x2000 |
| app0 / app1 | 0x10000 / 0x150000; each 0x140000 |
| SPIFFS | 0x290000 + 0x160000 (**1,441,792 bytes**) |
| Coredump | 0x3f0000 + 0x10000 |

`test/check_partitions.py` verifies actual built entries do not overlap, fit 4 MB, and match the image's flash-size header; image fits app0. Size accounting uses the same section sets as PlatformIO, rather than the generic ELF total that includes nonresident sections. See `ACCESS_BUILD_EVIDENCE.json`.

**Huge App not necessary:** required software fits without asset optimization or feature removal. No PlatformIO partition change was made. The compatible built-in Huge App layout was reviewed: app0 0x300000 bytes, no app1, SPIFFS moved to 0x310000 and reduced to 0xe0000 (917,504 bytes). Selecting it later would overlap former app1/filesystem areas and require a separately approved private backup/migration plan. No such physical change was performed. OTA development remains deferred; its present second-slot capacity is retained incidentally because the current image fits.

## Changed source scope

Firmware: `src/core/commissioning.h/.cpp`; `src/web/local_web_server.h/.cpp`, new `browser_auth.cpp`, `session_core.h`, `access_page.h`, MQTT page and generated gzip; native MQTT runtime diagnostics; disabled `lora_transport.h/.cpp`; `tools/commission.py`, `device_acceptance.py`; asset generator and session/UART/partition/access UI tests. Existing MQTT contract, packet formats, dependencies and partition configuration unchanged.

Gateway: `backend/server.py`, `account_settings.py`, `auth_manager.py`, new `account_sessions.py`, `account_backup.py`, `recover_account.py`; `mqtt_service.py` diagnostics; login/logout/account/MQTT templates/scripts/styles; access lifecycle/browser tests and narrow fixture/login/test-readiness updates. Prior user modifications remain; no broad reset, commit or destructive cleanup was used.

## Exact remaining owner actions

### Gateway access and optional recovery

Open **http://127.0.0.1:5000/login** with the existing Gateway account. These credentials are independent of ESP32 and MQTT. If locked out, inspect the deliberate recovery preview:

```powershell
Set-Location 'D:\esp32 selva\ESP32_LoRa_Project'
.venv\Scripts\python.exe backend/recover_account.py --user admin
```

Only if you intend to replace that account's credential, run:

```powershell
.venv\Scripts\python.exe backend/recover_account.py --user admin --apply
```

This backs up accounts first, replaces only that account verifier, increments its version and requires browser password replacement using the temporary bootstrap credentials specified in your prompt. Other accounts, Gateway data, MQTT profile/secrets and firmware NVS are not recovery targets. Use `--bootstrap --apply` only for an actually empty account database. Neither recovery nor bootstrap was run against live data by this phase.

### Firmware deployment — owner-run only

Reconnect the ESP32/resolve Windows error 31 and close serial monitors. Inspect/build:

```powershell
Set-Location 'D:\esp32 selva\ESP32_LoRa_ESP32_Firmware'
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' device list
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' run
```

When ready, this **writes firmware** using the unchanged partition layout:

```powershell
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' run --target upload --upload-port COM8
& 'C:\Users\Admin\.platformio\penv\Scripts\pio.exe' device monitor --port COM8 --baud 115200
```

Normal upload replaces its bootloader/table/OTA-metadata/application regions; do not run erase_flash or filesystem upload. No NVS/filesystem layout migration is required. Use the actual DHCP IP printed after boot; last known was 192.168.1.105. `/login` and `/account` require the **new** firmware. Existing local credentials are retained, not reset to bootstrap defaults.

If that local password is forgotten, only after installing the new firmware, a deliberate **credential-writing** USB recovery is available:

```powershell
& 'C:\Users\Admin\.platformio\penv\Scripts\python.exe' tools/commission.py --port COM8 --operation recover-account --confirm-device-id ESP32-10777D842178
```

It changes only the local account credential/name, invalidates sessions and forces browser replacement before normal access. It does not erase Wi-Fi/MQTT/mesh/device configuration. It was not run here. Normal password changes belong on the Account page with show/hide controls.

After choosing a password, optional checks using that existing clipboard credential without resetting it:

```powershell
& 'C:\Users\Admin\.platformio\penv\Scripts\python.exe' tools/device_acceptance.py --check-only
```

The helper supports new cookie/CSRF firmware and identifies legacy Basic firmware separately. The command without `--check-only` is a **credential-writing recovery**, not a read-only status check. Do not run it merely to diagnose MQTT.

### Broker and continuous worker

An authorized EMQX operator must first reconcile the rejected active credential and verify anonymous denial, per-principal/client topic directions and unauthorized-topic denial. Do not treat the password pasted into the prompt as permission to overwrite a live profile or force a revision. If credentials need changing, use staged public profiles on both sides and the existing local pending-secret helpers with their actual revisions. Restore a usable control path before expecting a coordinated switch; an already-broken active authentication path is not a successful switch proof. Do not rerun initial commissioning over active profiles.

Only after authentication and required ACL verification, stop the existing Gateway process in its console and launch the existing worker explicitly:

```powershell
Set-Location 'D:\esp32 selva\ESP32_LoRa_Project'
$env:GATEWAY_MQTT_TRUST_ACL='1'
.venv\Scripts\python.exe backend/server.py
```

Then verify actual worker connection, all QoS 1 subscriptions, validated physical packets, persistence and dashboard readback separately. The guard is an operator assertion, not evidence by itself. No authorized EMQX management access was available here; no hosted ACL or password changes were made.

Physical follow-up also includes browser password persistence over reboot, forced-change/logout/idle/CSRF handlers, combined web/two-TLS heap stress, Wi-Fi/broker outage soak and E220 hardware identification/configuration/readback/RF tests. There is no production-readiness or full end-to-end completion claim while these items remain blocked/unverified.
