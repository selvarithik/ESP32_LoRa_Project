# Gateway sensor icons, mapping and command recommendations

## Implemented changes
Ten additional icon choices: fan (airflow), flame (flame/heat), cloud-rain (rain), magnet (magnetic field), door (contact), weight (load cell), ruler (distance), volume (sound), compass (heading), beaker (pH/liquid chemistry).
There are now 23 choices; the 30 widget templates are unchanged. These are presentation choices, not new firmware drivers, calibrated measurements, physical sensors or automatic hardware detection. Existing wind/network/cpu choices now have their own SVG rather than a generic fallback.
No production database rows, sensor mappings, Wi-Fi, MQTT profiles or ESP32 firmware were modified.

## Mapping existing ESP32 data
1. Open Gateway → Sensor Management. Select the correct node and edit the existing parameter. Avoid creating duplicates for fields already discovered.
2. Data source is `node_telemetry`: the normalized telemetry received by the existing IP/MQTT transport, not a new transport.
3. Set Existing payload field (`source_field`) to an exact flat key below. Dotted keys, if present, are literal keys; this code does not implement nested JSON paths.
4. Choose label, numeric type, units, precision, icon and chart appearance. Use scale=1 and offset=0 for the current already-normalized measurements.
5. Enable the parameter and dashboard widget as required. Fresh values appear only when the device actually reports them. Match stale timeout to the actual reporting interval; do not present missing data as live.
6. Numeric conversion is raw received value × scale + offset. Display mapping does not reconfigure GPIOs, discover hardware or calibrate a sensor.

| Hardware | Existing payload fields | Physical connection/address |
|---|---|---|
| DHT11 | temperature, humidity | GPIO4; no I²C address |
| INA219 | bus_voltage, shunt_voltage, current, power | SDA21/SCL22; configured `ina219_address` is authoritative (common default 0x40 / decimal64; verify actual module/straps) |
| MQ135 | mq135_adc_raw, mq135_pin_mv | ADC GPIO34 with verified divider; no I²C address; raw/uncalibrated |

The node identity is e.g. `ESP32-10777D842178`. The firmware sensor identifier is node ID plus sensor type, e.g. `ESP32-10777D842178-DHT11`. The Gateway creates per-parameter sensor identifiers by adding the field, e.g. `ESP32-10777D842178-DHT11-temperature`. `parameter_id` and `source_field` select the reading; neither is the GPIO/I²C address. A LoRa node address identifies the radio node and must not be used as a sensor address.
Future Modbus sensors would additionally need slave address, register, data type, byte order and scaling in a real driver; adding an icon does not provide Modbus support. The current typed ESP32 ingestion validator supports DHT11, INA219 and MQ135 only.

## SQLite assessment
Already used at data/gateway.db by backend/database.py. Appropriate for this local, single-host Gateway, configuration, mapping, telemetry and command history. Keep SQLite on the Gateway computer; ESP32 configuration remains NVS. Define telemetry retention, indexes, backups and bounded writes as deployment grows. SQLite has one writer at a time. Consider PostgreSQL for sustained competing writers or multiple Gateway servers. WAL may help concurrent reading/writing on the same host, but was not enabled or changed in this task. Verify the bundled SQLite version before any separate WAL change.
Official references: https://sqlite.org/whentouse.html and https://sqlite.org/wal.html .

## Fifteen practical action candidates — proposal only
Keep the existing 21 primary commands. Do not create new aliases merely to inflate the command count. The following are candidate operations, not implemented or hardware-tested in this task. Reuse existing CONFIG_UPDATE/DIAGNOSTICS workflows where noted; only add dedicated wire commands when required by a complete handler, capability advertisement and acceptance tests.

| # | Action | Implementation recommendation |
|---|---|---|
| 1 | Synchronize device time | New SYNC_TIME; bounded clock validation, report applied UTC and source |
| 2 | Connect active MQTT profile | Reuse current local MQTT operation; remote action must keep active profile unchanged |
| 3 | Reconnect MQTT | New reconnect operation with backoff; no credential/profile overwrite |
| 4 | Pause/disconnect MQTT | Existing local operation; remote only with working alternate management path and recovery deadline |
| 5 | Test MQTT round trip | New MQTT_TEST on approved existing topics; correlate application response, not just PUBACK |
| 6 | Read E220 identity/public registers | Expose existing read-only radio inspection; no RF or register writes |
| 7 | Discover/register nearby Slaves | New DISCOVER_NODES trigger only after approved RF profile and physical verification |
| 8 | Run bounded I²C address scan | New I2C_SCAN diagnostics; shared-bus synchronization and explicit permission |
| 9 | Read a command's cached execution result | New GET_COMMAND_RESULT by command ID; unknown remains unknown |
| 10 | Cancel a not-yet-executed command | Gateway queue cancellation first; device cancellation only if actually cancellable |
| 11 | Reset selected diagnostic counters | New RESET_DIAGNOSTIC_COUNTERS; never erase logs, NVS or configuration implicitly |
| 12 | Enter sleep immediately | New SLEEP_NOW with drain, final response and verified timer wake before entry |
| 13 | Cancel a pending sleep entry | New CANCEL_PENDING_SLEEP while device is awake; cannot wake an already sleeping device |
| 14 | Change IP/MQTT transport safely | Reuse CONFIG_UPDATE trial/confirm/rollback and Gateway admin confirmation; no duplicate protocol-change command |
| 15 | Update public radio configuration | Reuse CONFIG_UPDATE with allowlisted E220 fields, readback and approved regional profile; no raw register-write command |

Changes that could disconnect the management path need explicit authorization, ACK, execution RESPONSE, bounded timeout and rollback. Never forward Gateway administrator passwords to ESP32. No BLE, OTA or Private Chat additions are included.
