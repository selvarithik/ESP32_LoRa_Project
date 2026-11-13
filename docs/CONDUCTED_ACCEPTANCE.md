# Conducted LoRa acceptance, November 14, 2026

Gateway PING `CMD-23F28DF0E544` completed with a Slave ACK at 00:17:49.886617 IST and a separate execution response at 00:18:50.077066 IST. The response identified LoRa through the Master and verified MQTT into the Gateway. The Gateway stored a fresh Slave INA219 sample at 00:19:50.017334 IST, 4.680 V bus and 0.26 mV shunt. The receive-side RSSI byte for each was `00`, displayed as n/a. The Slave measured −34 dBm at the final checkpoint.

The tested Gateway exposes the existing authenticated LoRa Mesh Monitor. Complete both-node live reporting and node chat remain release gates. See the [firmware manual](https://github.com/selvarithik/ESP32_LoRa_ESP32_Firmware/blob/main/docs/MANUAL.md) for radio readback, firmware settings, timing, and restoration.
