# SELVARITHIK’S A&D Gateway quick manual

## 1. Set up the conducted bench

1. Connect the two E220 antenna ports with an SMA cable and at least 30 dB total attenuation.
2. Keep both RF ports terminated and remove radiating antennas. This release is for conducted bench use only.
3. In the read-only radio view, check CH 16 (866.125 MHz), 10 dBm, 2.4 kbps and address 0. Keep these settings unchanged.

## 2. Start the Windows Gateway

1. Extract the release ZIP to a writable folder. Copy `config.example.json` to `config.json` beside `Selvarithik_AD_Gateway.exe`.
2. Set `admin_pin` to a private password of at least 12 characters for the first startup. This creates the local `admin` account. Existing accounts are preserved. Keep the file private and out of Git.
3. For MQTT, fill the broker hostname, TLS port, username, password, CA PEM path, client ID, topic prefix and Gateway ID. Use a unique client ID and the same prefix and Gateway ID as the Master. After verifying the broker account's restricted Gateway topic ACLs, set `mqtt_acl_confirmed` to `true`. Leave the host empty for an offline dashboard. Restored data keeps its existing MQTT profile.
4. Double-click the EXE. Open [the local dashboard](http://127.0.0.1:5000/) and sign in. If you changed `server.port`, use that port. The EXE is unsigned and Windows SmartScreen may warn.
5. By default, data goes under `%LOCALAPPDATA%\SelvarithikGateway\data`. Use `--data-dir` for a separate bench or a matching restored Gateway and account database. Use the dashboard on the Gateway PC and keep the HTTP service off the internet.

## 3. Use Master and Slave chat

1. Join each ESP32 to the bench Wi-Fi using its local commissioning workflow. Read its station IP on USB serial at 115200 baud.
2. Provision a unique node PIN on each board over USB with `{"op":"chat_pin","pin":"<your-private-pin>"}`. Each board stores a verifier in NVS. Keep node PINs separate from the Gateway admin password.
3. On a device on the same trusted LAN, open `http://<esp32-ip>/node-chat` and sign in. Send 1–24 printable ASCII bytes.
4. The ticks mean **queued**, **sent** (the radio accepted the turn), **delivered** (authenticated peer receipt), or **failed**. The next free poll can take up to one interval, typically 60 seconds on the bench. Registration, pending commands and delivery receipts can require additional turns.

## 4. Read the dashboard

Open **LoRa Mesh Monitor**. RSSI `n/a` means a valid measurement is unavailable. The link bar uses reported signal strength. The airtime bar shows a modeled rolling budget, with actual RF airtime still unverified. Check counters for fragments, rejects, authentication failures and budget refusals. An offline or stale alarm calls for checking the node and its last authenticated report.

## 5. Flash or restore the ESP32 application

1. Read the board's partition table and active app slot first. Back up flash and check the image fits the verified slot.
2. Use `pio run -e CONDUCTED_BENCH` for the conducted image. Write only the active app slot, Slave first and then Master. Verify readback and the boot holdoff.
3. To restore the production firmware, use `pio run -e esp32dev` and write only the verified active app slot. Preserve NVS, the partition table and device settings. Production firmware also requires applicable approval before any over-the-air use.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| ESP32 has no Wi-Fi | Check serial for station IP and status. Verify the saved network and reconnect locally. |
| ESP32 page unreachable | Join the same LAN, check client isolation, and temporarily disable Android mobile data if it keeps switching away from the local Wi-Fi. |
| RSSI n/a | Check the raw byte and freshness. The production Master can report invalid 00 or FF even when packet delivery succeeds. |
| Command times out | Check Master TLS and MQTT subscriptions, then wait for the addressed poll and separate device ACK and execution response. |
| Node offline | Check power, Wi-Fi, Master MQTT, the conducted cable, and the last authenticated report. A Slave becomes stale after missed polls. |
| Airtime budget exhausted | Wait for entries to age out of the rolling window. Keep the configured limits in place. |
