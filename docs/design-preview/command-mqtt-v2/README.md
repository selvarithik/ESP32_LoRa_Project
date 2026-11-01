# Design review V2 - route metadata and contrast

Preview only. No production source, routes, configuration, firmware or running services were changed. V1 remains available beside this folder. Open index.html for the page switcher and expandable configuration preview.

The approved MQTT layout is preserved. Contrast is strengthened across both designs with darker secondary text, clearer borders, neutral metadata backgrounds and a distinct conversation background. Brand red, navy, blue, company SVG and the compact header remain unchanged.

Every command, ACK and execution-response bubble includes From Device, To, Status and Execution outcome. Four desktop columns use subtle dividers; mobile uses a two-column grid. Device identifiers keep their full value in SVG title tooltips when the visible text is shortened. Command IDs and event timestamps remain below the card.

The recorded PING example shows the message's state at its event time:
- Outgoing: GATEWAY -> ESP32; SENT; execution Pending.
- Device ACK: ESP32 -> GATEWAY; ACCEPTED; execution Not reported.
- Successful execution RESPONSE: ESP32 -> GATEWAY; COMPLETED; execution Executed.

Production mapping must use existing durable Gateway command records and actual correlated ACK/RESPONSE fields. Sending a request or receiving HTTP success cannot create device acceptance or an execution outcome. Gateway QUEUED storage, device ACCEPTED, and successful execution are distinct facts. The preview's ACCEPTED example is a recorded real ACK on an existing accepted Gateway command, not an invented gateway-acceptance API field. Failures must retain their real errors; unavailable outcomes stay Not reported.

Rendered and visually reviewed at 1366x768 and 390x844. These are static design screens with an offline review switcher, not live application testing. The actual responsive component, native title/accessible labels, history behavior and API integration will be implemented after design review.
