# Conducted release status

**Conducted bench use only. This release is not cleared for over-the-air operation.**

## Done and verified

- Both E220s read back channel 16, 10 dBm, 2.4 kbps, and address 0. Both started with zero transmissions during boot holdoff.
- Both text directions reached authenticated delivered ticks in the November 14 conducted retest.
- The Gateway received a separate Slave PING ACK and execution response, followed by fresh Slave INA219 data via the Master and EMQX.
- A fresh EMQX subscriber received 14 retained node topics plus Gateway availability. Both node configurations and metrics reached the Gateway. The Gateway process disconnect produced an offline Last Will and recovered online.
- The standalone Master receiver captured raw DF (−33 dBm). Production Master observations still include invalid 00 or FF. The release displays n/a for those values.
- The recorded acceptance run passed 201 Gateway tests, eight firmware checks, 33 Gateway browser views and the exercised chat HTTP cases. The phone screenshots use fixtures. See the [conducted verification report](https://github.com/selvarithik/lora-e220-docs/blob/main/CONDUCTED_VERIFICATION.md).

## Pending verification

| Item | Test plan and pass criteria |
| --- | --- |
| Concurrent valid chat and rate limiting | Submit two valid messages concurrently to each board. Exactly one is accepted within five seconds. The other returns the rate-limit response and creates no duplicate delivery. Repeat after the window. |
| Slave configuration queue after `aa10f02` | Flash the approved conducted image in a later authorized session. Queue both chat directions during registration. Verify that the Slave configuration survives the chat turns and arrives in SQLite and retained MQTT. |
| Board offline recovery | Disconnect COM10 and verify the Master availability path, including broker Last Will if configured for that client. Disconnect COM8 and verify its missed-poll alarm after three configured intervals. Both node statuses must recover from fresh authenticated reports. The earlier Gateway-worker Last Will test is separate. |
| Master-side RSSI | Compare full UART captures after a production transmit turn with the standalone listener at identical attenuation. Require valid, repeatable RSSI or document the unresolved 00/FF trailer alongside the DF baseline. |
| Full suites | Run all native firmware, Gateway API and browser suites on clean builds. Record every result and any hardware-only exclusion. |
| Actual E220 airtime and occupied bandwidth | Request the exact PHY parameters from EBYTE or measure both on a conducted setup. Validate the worst-case airtime model and recompute the poll interval and budget against measured evidence. |
| WPC category and type approval | Verify applicability of G.S.R. 853(E), 865–868 MHz, and device approval with the relevant authority or accredited lab before considering over-the-air use. |
| Radio key persistence | In a separately authorized conducted session, power-cycle both modules and verify authenticated delivery. The E220 key is write-only. |
| Noise RSSI | Noise RSSI stays disabled. If it becomes a requirement, verify it under a separately approved configuration and keep it distinct from packet RSSI. |
| Second Windows PC | Extract and run the ZIP on another Windows PC with a fresh config. Verify startup, sign-in, dashboard and local icons without developer tools. |
| Signing and license | Sign a future build with an authorized code-signing certificate and verify the signature. Add a license only after the owner selects one. |
| LAN security | Keep HTTP on a trusted LAN or loopback, provision unique PINs over USB, and verify unauthorized requests are rejected. Keep port forwarding and public tunnels off. |
