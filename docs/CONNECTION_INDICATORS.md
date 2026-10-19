# Connection LED and Master TM1637

The GPIO2 blue LED is working, confirmed by the owner after the first app-only COM8 upload. That first TM1637 image attempted RSSI/ack-age writes, but the owner reported a blank display. Driver write attempts are not successful physical display verification.

The follow-up diagnostic build implements the owner's requested **connection time, connection count and Wi-Fi RSSI, with no sensor values**. It checks every byte ACK and idle CLK/DIO levels and shows8888 for a two-second startup segment test. Two attempts were blocked before any flash write while COM8 was unavailable. After the owner reconnected the board and corrected the display connection, the diagnostic image uploaded successfully with flash hash verification. The owner confirmed all three screens visible. The live driver reports every byte acknowledged with zero ACK failures. The earlier blank display is resolved; no single electrical/software root cause was isolated.

## Wiring and voltage

Current confirmed wiring: TM1637 VCC3.3V, common GND, CLK18 and DIO19; board ESP32-D0WDQ6 rev1.0,4MB flash. The owner checked labels and firm connections. Onboard LED GPIO2 is active high. GPIO18/19 are reserved for the display only on MASTER; NODE never constructs the display driver or touches those pins.

The [TM1637 manufacturer's datasheet](https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/unit/digi_clock/TM1637.pdf) specifies nominal5V operation and characterizes at4.5..5.5V. A module can therefore be blank at3.3V even when code is correct. Do not move VCC to5V while CLK/DIO directly connect to ESP32: module pull-ups can expose the GPIOs to5V. If this module requires5V, use suitable bidirectional level shifting with its3.3V side connected to GPIO18/19 and5V side to the module, common ground, and verified module supply. Do not claim electrical compatibility or visible operation without testing the actual module.

Current DHT11 GPIO4, INA219 SDA21/SCL22 and disabled/disconnected MQ135 GPIO34 remain separate. No sensors appear on the TM1637; their Gateway telemetry continues independently.

## Display legend in the revised build

| Screen | Meaning |
| --- | --- |
| 8888 at boot | Two-second segment self-test; not a measurement |
| -67 | Signed Wi-Fi RSSI in dBm |
| 01:23 | Current continuous confirmed Gateway connection duration, MM:SS, capped99:59 |
| n001 | Gateway connection establishments since boot, capped999 |
| Conn / C123 | Waiting for Gateway; Cxxx is waiting seconds, capped999 |
| noFI | Wi-Fi unavailable |

Connected screens advance every3s and refresh about once/second. The colon distinguishes connection duration. Connection count increments on a transition from unavailable/stale to a fresh Gateway receipt; it is neither packet count nor sensor count. Duration resets at a new connection and is not the server process uptime.

LED ON requires Wi-Fi and an authenticated Gateway receipt less than15s old; association/broker connection alone is insufficient. Wi-Fi loss turns it off at the next250ms check; lack of receipts turns it off after15s. No deliberate router or Gateway outage was caused; expiry/Wi-Fi-loss behavior is covered in host assertions.

## Settings and diagnostics

Local settings server_led_enabled, server_led_active_high and tm1637_enabled default true; apply on restart. Existing conflicting peripheral assignments in older NVS disable new indicators during migration rather than causing a configuration reset. Mutations that introduce pin conflicts are rejected. No duplicate Gateway setting writer or MQTT field is introduced.

Existing /api/status and physical USB status include indicators. ACK-aware firmware reports ACKNOWLEDGED_VISUAL_UNVERIFIED, NO_ACK or LINE_NOT_HIGH, plus idle-line states and failure count. An ACK indicates bus communication, not visible digits. Physical visual confirmation remains an owner observation, separate from the firmware flag.

Driver is the maintained [TM1637 v1.2.0 library](https://github.com/avishorp/TM1637/tree/v1.2.0), pinned at82214be06742bf187fab4f29aaabb64c289eaae0. A small subclass preserves its bit/byte implementation while checking acknowledgements that setSegments originally discarded. Calls have bounded bit delays. DHT/I2C acquisition stays on its separate worker. No BLE, Chat or OTA development is introduced.

## Checks and preservation

Portable host tests pass for stale receipts, Wi-Fi loss, millis wraparound, screen values/colon/caps and pin conflicts. Mocked local UI1280/375 checks typed indicator checkboxes; MQTT UI360/1280 unchanged and passes. Contract copies match and canonical C++/Python MQTT digests remain compatible. Gzip checks and final PlatformIO build pass; partition offsets, filesystem and both application slots remain unchanged. A protected full4MB backup was completed before the first upload; a first high-speed read failed harmlessly and the lower-speed backup succeeded.

The first uploaded build's physical runtime reported fresh Gateway receipts, LED-on requested, RSSI/ack-age write attempts, all six DHT/INA measurements still persisted via signed local-IP, MQTT revision53/fingerprint unchanged. Owner confirmed LED working and display blank. See build and physical evidence JSON for exact sizes, deployment stage and pending checks.

## Final live result and MQ135 follow-up

Final deployed diagnostic build: program1,234,377 /1,310,720 (94.2%); image1,241,088, headroom69,632; static RAM60,236 /327,680 (18.4%). Partition/NVS/filesystem layout preserved. MQTT revision53 and active fingerprint unchanged. GPIO2 LED and three display screens are owner-confirmed; no physical radio/offline outage/sleep claim is made.

The owner subsequently confirmed fitting two10kOhm resistors: MQ135 AO →10k→GPIO34, GPIO34→10k→GND, common ground. This nominally halves AO voltage, about2.5V at the pin for5V AO. The onboard adjustable potentiometer alone was not accepted as proof of AO voltage protection. Only after divider confirmation was mq135_enabled saved over USB and the board restarted. It now reports real raw ADC counts/pin millivolts and WARMING_UP_RAW_ONLY; both parameters persist through the signed local-IP Gateway path. No ppm, CO2 concentration, air-safety classification or completed sensor calibration is claimed. The timer is not proof of manufacturer-specified conditioning. Configuration revision changed intentionally4→5; INA219 R100=100milliohms and other settings remain preserved.


Latest display update: removed the connection-count screen. Connected operation now alternates only signed Wi-Fi RSSI and current Gateway connection duration MM:SS every three seconds. Connection count remains available in diagnostics. Previous three-screen physical evidence describes the earlier image. The two-screen image was uploaded application-only on COM8 with flash hash verification; runtime frame sampling confirms RSSI and connection time only. See DISPLAY_TWO_SCREEN_EVIDENCE.json. Visual inspection is not automated.
