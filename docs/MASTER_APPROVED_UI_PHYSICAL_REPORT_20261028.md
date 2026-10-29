# Master COM8: approved firmware physical deployment

Date: 2026-10-28, Asia/Calcutta. Device ESP32-10777D842178,
MAC 78:21:84:7D:77:10, ESP32-D0WDQ6 revision 1.0, verified 4 MB flash.

The owner explicitly authorized full-flash backup, huge_app migration and upload.
Only the Master on COM8 was accessed. The Slave was not uploaded or reconfigured.

## Backup and upload evidence

- Read the complete 4,194,304-byte flash image before any writes. The read protocol
  digest and an independent device-computed full-flash MD5 matched the host copy.
- Saved a Windows DPAPI-protected backup and verified decryption of the saved file
  byte-for-byte. No plaintext full-flash backup was written to disk.
- Backup: data/system-audit/approved-ui-migration-20261028/full-flash-before.dpapi.
  This private ignored file is protected for the current Windows account; it was
  not added to source control or sent to the broker.
- Rechecked physical MAC, flash capacity, security state, original OTA app0 boot
  selection and current full-flash digest immediately before writing.
- Flash encryption and Secure Boot were observed disabled. Device NVS encryption
  is not claimed. DPAPI protection applies to the computer-side backup.
- Verified the approved package hashes. Uploaded only partitions.bin at 0x8000
  and firmware.bin at 0x10000. No factory reset, full erase, provisioning, bootloader
  replacement, OTA-metadata reset or filesystem image write was performed.
- Application size: 1,340,960 bytes. Application SHA-256:
  1d052b6380ade8b5b40b8fd7fa4a35d2ea806fd87dfa24eb2d68a189b36b73fa.
- Verified application readback, partition-table readback, unchanged NVS and OTA
  metadata bytes, unchanged bootloader region and every flash byte beyond the
  application's sector-aligned write region before rebooting.
- The old filesystem area was not blank. Its complete raw bytes remain unchanged
  at the old offset and in the protected full backup. The current firmware uses
  embedded web assets and does not mount/format that area. No claim is made that
  old filesystem files were repacked for the new filesystem offset.

The physical layout is now huge_app: app0 0x10000/0x300000, no second OTA slot,
SPIFFS 0x310000/0xE0000. NVS remains 0x9000/0x5000, OTA metadata remains
0xE000/0x2000. Future filesystem use must inspect/export/repack old data first.

## Runtime and webpage checks

- Master booted with the existing MASTER role and DHCP address 192.168.1.105.
- Existing credentials worked: the owner signed in normally in Edge. No account
  password was reset, read back or changed.
- Authenticated Dashboard and Radio configuration pages loaded. The existing NASA
  vector wordmark is present. Computed header background and all eight navigation
  link colours were rgb(255, 0, 0). No sidebar company branding was present.
- Live page screenshot: docs/MASTER_APPROVED_UI_LIVE_20261028.png.
- The unauthenticated browser is redirected to Sign in; unauthenticated API status
  returns HTTP 401. A public login page HTTP 200 is not an authentication bypass.
- MQTT initially waited for valid UTC. Automatic time had not synchronized during
  the initial observation, so the existing physical USB time operation seeded
  volatile UTC. This did not write configuration. Unattended cold-boot time sync
  remains to be verified; certificate validation was never bypassed.
- Final USB status: EMQX connected, TLS VERIFIED, authentication ACCEPTED,
  subscriptions READY, zero reconnects, zero drops, empty outbox and 154 PUBACKs.
  These are bounded observations, not a permanent-stability claim.

## Live sensor evidence

At the recorded checkpoint, uptime was 374,324 ms and the Gateway had persisted
210 new values with source mqtt. The existing permanent worker was used and the
Gateway process was not restarted. All eight readings were also checked in the
authenticated Gateway Dashboard, with Master ONLINE and values marked Live.

| Measurement | New persisted values | Checkpoint value | Largest gap among new values |
| --- | ---: | ---: | ---: |
| Temperature | 9 | 32.3 C | 11.05 s |
| Humidity | 9 | 48 %RH | 11.05 s |
| Bus voltage | 32 | 3.228 V | 11.05 s |
| Shunt voltage | 32 | 0.37 mV | 11.05 s |
| Current | 32 | 0.0037 A | 11.05 s |
| Power | 32 | 0.011944 W | 11.05 s |
| MQ135 ADC raw | 32 | 418 counts | 11.04 s |
| MQ135 pin voltage | 32 | 490 mV | 11.04 s |

DHT11 initially reported READ_ERROR/NO_RESPONSE after boot, then recovered during
observation. Final device health was valid/OK and fresh temperature/humidity were
visible in the Gateway. Intermittent DHT faults are not declared permanently fixed.
MQ135 remains raw, warming up and uncalibrated. INA219 readings use the existing
configured shunt; no new calibration or measurement-accuracy claim was made.

## Preservation and scope

Device ID, role, DHT enable/pin, INA219 enable and MQ135 enable match the pre-upload
status. MQTT active fingerprint, client ID, configuration revision 77, shared
revision 2 and secret revision 7 match the baseline. Gateway MQTT document and
protected-store fingerprints are unchanged. NVS preservation was separately
verified byte-for-byte before the first reboot.

No Wi-Fi, MQTT profile, sensor, radio or sleep configuration mutation was sent.
No RF test or protocol/sleep change was performed. Radio remained disabled as
reported by the existing configuration. Software transaction/sleep tests do not
become physical acceptance results merely because the image is now installed.

Evidence JSON: docs/MASTER_APPROVED_UI_UPLOAD_20261028.json and
docs/MASTER_APPROVED_UI_ACCEPTANCE_20261028.json. Private detailed backup/runtime
evidence is under data/system-audit/approved-ui-migration-20261028/.
