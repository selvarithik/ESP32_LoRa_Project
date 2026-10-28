# Current shared firmware hardware profile — Stage A build only

This section supersedes the historical acceptance snapshots below.
One source tree builds esp32_master (DEVICE_ROLE_MASTER) and esp32_slave
(DEVICE_ROLE_SLAVE). Canonical saved roles remain MASTER and NODE. Conflicting
stored role/foreign saved MAC identity inhibits network joining; NVS is preserved.
Each board derives its own identity from eFuse. No Slave MAC was read this stage.

| Item | Master | Slave | Wiring / condition |
| --- | --- | --- | --- |
| Board |Owner: original ESP32 DevKit30pin, expected COM8|Owner: DevKit38pin, expected COM10|Verify actual chip/flash/port before upload|
| DHT11 |Initial enabled|Initial enabled|DATA4, three-pin module3.3V/common GND|
| MQ135 |Initial enabled|Initial enabled|ADC34 through verified divider; heater supply per module|
| INA219 |Initial enabled; saved calibration retained|Always inhibited, including saved enable=true|Master SDA21/SCL22,3.3V, saved address|
| TM1637 |Inhibited|Inhibited|Disconnected; no GPIO18/19 activity|
| E220-900T22D |Compiled, initially RF disabled|Same shared driver, initially RF disabled|UART2 RX16<-TXD,TX17->RXD,M0 25,M1 26,AUX27|
| Blue LED |Existing indication retained|Existing role behavior retained|GPIO2; verify board polarity|

Initial defaults do not overwrite saved sensor flags. Slave never starts Wire or
initializes INA219. Master R100=100milliohms was previously owner-confirmed and
saved; unknown shunt withholds current/power. No fabricated sensor samples.
Master MQ135 two10k divider was previously confirmed; verify the Slave divider and
measured ADC maximum separately. Its potentiometer does not protect analog voltage.
Raw ADC/pin mV are uncalibrated, not ppm/AQI/safe-gas readings. GPIO34 is input-only.
Pin count alone does not prove GPIO16/17 availability; check actual board/PSRAM.

EBYTE specifies module supply2.3..5.5V, UART3.3V, with adequate supply/antenna needed
for rated22dBm. Verify actual supply/current capacity, common GND, UART voltage,
antenna, channel/frequency and regional legality before RF enablement. No5V TTL GPIO.

Read-only inspection uses C1 00 06 for public registers00..05 at9600 8N1, mode3.
No register writes or radio encryption-register reads. A later approved probe changes
mode pins temporarily, restores observed levels and does not enable RF. RF initialization
requires saved public settings to match observed settings. Subpacket32 is safely
unsupported;64/128/200 are software-tested. Do not change module settings to hide a
mismatch. Observed settings, ACK timing, RSSI alignment and radio delivery remain
physically unverified. READY_LINK_UNVERIFIED is not a successful peer link.

Both generated4MB tables preserve NVS0x9000/0x5000, otadata0xe000/0x2000,
app0 0x10000/0x140000, app1 0x150000/0x140000, SPIFFS0x290000/0x160000,
coredump0x3f0000/0x10000. Nonoverlapping, ending at4MB. Images fit; huge_app was
unnecessary. No partition/NVS/filesystem write or OTA development was performed.

Later: explicit Master-only upload approval, verify COM8 identity/flash and wiring,
read public radio settings with RF disabled, reconcile saved configuration securely.
Before Slave upload, obtain explicit BOOT-button confirmation and verify COM10.
Then test direct discovery/heartbeat/telemetry, PING ACK plus actual RESPONSE, retry,
lost ACK, expiry, reboot and radio outage. Extra relay hardware is needed before
claiming multi-hop. Live MQTT requires separate approval and verified ACLs. Sleep,
power-loss, heap/stack pressure and concurrent sensor/radio soak remain physical tests.

Sources: [EBYTE module](https://www.ebyte.com/product/1076.html),
[EBYTE manual](https://www.ebyte.com/Uploadfiles/Files/2021-7-6/202176188184448.pdf).

---

## Historical acceptance notes (older uploaded images)

# Hardware requirements and verified wiring

Target: PlatformIO esp32dev / ESP32-D0WDQ6 revision 1.0, 4 MB flash. COM8 was connected for the 2026-10-19 sensor acceptance; Master and Node share one image selected by saved role. Name changes never change identity.

- DHT11: three-pin module, VCC 3.3 V, DATA GPIO4, common GND. Physical readings and Gateway ingestion verified.
- INA219: VCC 3.3 V, SDA21, SCL22, common GND, address 0x40. Owner confirmed onboard R100 shunt = 100 milliohms. USB commissioning saved this value; current and load-side power are derived from shunt/bus registers. Accuracy against a reference meter or known load remains pending. No external shunt addition is implied.
- MQ135: module VCC 5 V. Owner confirmed AO disconnected from GPIO34 after the direct connection was identified. Keep mq135_enabled=false until a measured, suitable voltage divider protects the ADC pin; target its useful ADC range, not merely the absolute maximum. Raw counts/pin millivolts only; no ppm/AQI or safe-gas assertion. A boot-based timer is not proof of heater conditioning; follow the exact module manufacturer requirements and calibrate separately.

Do not connect INA219 to unknown high voltage/current. Firmware protocol bounds are not load, terminal or shunt thermal ratings. VIN+ goes to measured supply positive; VIN- to load positive. Verify supply/current limits and wiring against the actual module before load testing.

E220 remains DRIVER_UNAVAILABLE. Exact module SKU, frequency, antenna, region, UART pins, supply and AUX/mode wiring must be verified before activating a physical driver. The compact radio codec and mock radio are software tests only. Ethernet likewise requires verified external hardware.

Recurring sleep uses timer wake and stops Wi-Fi; no remote wake is promised. Real sleep/wake, physical second Node, E220 delivery, power interruption and soak tests remain pending. Private Chat and OTA development are excluded.

The deployed default.csv layout is unchanged: both 0x140000 application slots and existing NVS/filesystem offsets remain. LTO permits the completed sensor image to fit; huge_app is unnecessary. App-only writes used 0x10000 after device/layout/active-slot guards and a full DPAPI-protected local flash backup. No partition/NVS/filesystem image was flashed. Existing OTA capacity is preserved without adding OTA functionality.

References: [TI INA219 data sheet](https://www.ti.com/lit/ds/symlink/ina219.pdf), [Espressif ESP32 electrical specifications](https://documentation.espressif.com/esp32_datasheet_en.html), [ADC guidance for the pinned IDF generation](https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32/api-reference/peripherals/adc.html).

Current follow-up (connection indicators task): owner fitted a two10kOhm divider from MQ135 AO to GPIO34/GND; sampling is now enabled and raw counts/pin mV are persisted by the Gateway. This supersedes the earlier disconnected/disabled snapshot above. TM1637 at CLK18/DIO19 is MASTER-only and the owner confirmed visible connection time/count/RSSI after the ACK-aware diagnostic upload. See docs/CONNECTION_INDICATORS.md for voltage limitations, display legend and actual test evidence. Do not connect5V logic directly to ESP32 GPIOs.


Command Center extension 3 hardware checks (pending): upload the correct role image
without erasing NVS or changing partitions; verify login worker latency/session security,
first-use forced change and existing saved credentials; run Master-local PING/status/config
and Node PING/telemetry/config, restart response after reboot, Wi-Fi outage/soak, lost
ACK/response and power loss. Check heap/stack under concurrent login/telemetry. Confirm
E220 SKU/frequency/pins/electrical/regional settings before enabling any physical radio.
Validate physical fragmentation, authentication, ACK/RESPONSE routing and hop limits.
MQTT physical tests require verified EMQX ACLs and TLS; ACL_CONFIRMATION_REQUIRED stays.
No OTA, BLE or Private Chat work was implemented or extended.
