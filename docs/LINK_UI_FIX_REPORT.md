# Master/Slave link and Gateway UI fixes — 25 October 2026

## Current result

| Component | Identity/address | Verified result |
|---|---|---|
| Master COM8 | ESP32-10777D842178, 192.168.1.106 | Explicit Master image, MASTER saved role, authenticated Gateway receipts |
| Slave COM11 | ESP32-CC9B23E2DEC4, 192.168.1.105 | Explicit Slave image, NODE saved role, Wi-Fi link to assigned Master |
| Gateway | Dashboard 127.0.0.1:5000; device listener 192.168.1.104:5001 | Both physical devices ONLINE; real persisted local-IP telemetry |

These are observed DHCP addresses, not static assignments. The laptop changed
from .105 to .104 and Master changed from .104 to .106. The stale saved addresses
caused BIND_FAILED and incorrect peer destinations. Updated the existing listener
through its authenticated revision-checked page, the Master's server_host, and
the Slave's master_host. For future DHCP changes, use Local IP settings and update
peer destinations, or arrange router DHCP reservations; no static network values
were invented or forced onto the devices.

## Implemented changes

* Existing E220/RF remains disabled; the verified path is Slave -> Master ->
  Gateway using authenticated local Wi-Fi/IP. The Slave has neither Gateway
  direct permission nor a direct local-IP credential. Its received telemetry
  therefore verifies forwarding, not a direct-to-Gateway shortcut.
* Added the narrowly identity-confirmed USB network commissioning operation,
  needed because the Slave's first password change remains pending. It rejects
  MQTT, sensor, account and role fields. Account state was preserved; ordinary
  first-login protection remains active.
* Fixed the pinned WebServer raw-parser tail-read stall without changing the SDK.
  The raw callback consumes exactly validated Content-Length using the existing
  bounded reader and actual server client, then skips the SDK's full-buffer tail
  read. Retained size, content type, HMAC, identity and packet validation.
* Both explicit images were application-only uploads at 0x10000 with esptool hash
  verification. Preserved NVS, partition table, filesystem and second OTA slot.
  Slave settings/partition/OTA readback matched before/after in the same session;
  Master matched through a separate verified readback after upload.
* Renamed active Gateway page text and shared header/banner to Selvarithik A&D.
  Removed apostrophe and S glyphs from the existing SVG header wordmark, retaining
  its design. Historical asset filenames were not renamed. Firmware source page
  inspection found no matching apostrophe-S branding to remove.
* Restored MQTT links to desktop/mobile navigation and gave the existing MQTT
  page its own title. No broker settings or MQTT connection controls were changed.
* start_saved now records BIND_FAILED and lets dashboard startup continue. The
  dashboard shows a link to Local IP settings when the listener cannot bind.
  Saved settings are retained; it does not silently bind to every interface or
  select another IP. Unexpected configuration errors are still raised.

## Tests and actual evidence

| Category | Evidence |
|---|---|
| Gateway unit/API | 81 tests, no failures/errors/skips; includes bind failures and preserved settings |
| Local TCP software integration | 4 tests passed, including malformed/fragmented requests, auth, restart and timeout |
| Rendered UI checks | 9 in-scope pages passed branding checks; desktop/mobile MQTT links and MQTT title |
| Actual browser | Updated branding, MQTT navigation opening the existing page, Local IP apply/LISTENING, both nodes ONLINE and sensor display verified |
| Actual Windows bind failure | Unassigned address reproduced the OS failure; startup caller continued with FAILED/BIND_FAILED and no settings mutation |
| Native firmware logic | USB network allowlist/identity rejection and production bounded-body reader checks passed |
| Contract | Both copies byte-identical; SHA-256 4a6ac838e0fb437606e791d3bd21941cdfe64d560763f0f182e5b105fb5fedde |
| Physical round trip | CMD-29CEC62D93E4: Slave PING completed, ACK ACCEPTED at 17:23:38.126339, RESPONSE at 17:23:40.087010; result ok=true |
| Physical persistence | Real Master sensor samples and Slave MQ135 ADC/pin-mV samples persisted with source local-ip and advanced over repeated observations |
| MQTT/broker | Not tested; profiles, credentials, revision and protected Gateway files preserved |
| RF/LoRa | Not tested or enabled; IP verification does not establish RF operation |

Master program/image: 1,290,369 / 1,297,072 bytes; static RAM 74,596 bytes.
Slave program/image: 1,285,917 / 1,292,624 bytes; static RAM 74,540 bytes.
Application capacity is 1,310,720 bytes each; image headroom is 13,648 / 18,096
bytes. No huge_app selection or partition change was necessary.

Full non-secret evidence: LINK_UI_FIX_EVIDENCE.json, LIVE_PAIR_EVIDENCE.json,
MASTER_LINK_UPLOAD.json, SLAVE_LINK_UPLOAD.json and Gateway SLAVE_REAL_PING.json.
The protected before/after comparisons confirm sensor configuration, canonical
MQTT storage and account verifier data were retained. Only the requested role,
Wi-Fi/parent pairing, mesh authentication/allowlist and connection addresses were
commissioned; configuration revisions advanced normally.

## Remaining physical and timing limitations

Slave DHT11 reports READ_ERROR and has no valid temperature/humidity values.
Check its actual 3.3 V/GND/DATA-to-GPIO4 wiring and module pull-up. Master DHT11
also has intermittent read errors. Sensor settings were not changed to hide these
failures. Existing Slave profile inhibits INA219 acquisition; its stored sensor
flags remain intact, and Master INA219 current/power remain visible.

Slave ADC raw=0 and pin-mV around142 are actual ADC samples, not proof that a gas
sensor is physically attached or calibrated. MQ135 remains raw/uncalibrated.

Live delivery and command round trips work, but a long reliability soak was not
completed. Recent observations included transient HTTP retries/queue pressure and
some 20–47 second gaps between persisted samples. Do not claim guaranteed 10-second
delivery, uninterrupted operation, RF verification or production readiness.

## Starting the server

The server is currently running in local audit mode at http://127.0.0.1:5000 with
the existing temporary loopback test session; this launcher omits MQTT startup.
Do not start a duplicate server on port5000. After stopping the existing instance,
the normal owner command remains:

```powershell
cd "D:\esp32 selva\ESP32_LoRa_Project"
.\.venv\Scripts\python.exe backend\server.py
```

If a saved LAN address becomes unavailable, the dashboard now opens with a
listener warning instead of the previous BIND_FAILED traceback. Select the
computer's current private LAN address in /local-ip. Normal startup retains its
existing MQTT authorization policy; this fix does not grant broker permissions.
