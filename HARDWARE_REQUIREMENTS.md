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
