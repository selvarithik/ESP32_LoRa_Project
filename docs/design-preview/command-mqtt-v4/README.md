# Design V4 - matching compact message cards

Preview only. Sent commands and incoming responses now share one compact card design: 442 x 170 px desktop, 330 x 170 px mobile. This reduces the previous response-card height from 252 to 170 px, while retaining readable primary text.

Both use the same command header, plain two-column metadata, collapsed secondary details, status/error treatment and compact command-ID/time footer. Sent cards put priority, timeout, retry, dispatch and creation information behind Parameters & dispatch. Response cards keep payload expansion and Copy JSON. ACK remains a separate simple status-and-time bubble, with no device metadata. Warm neutral background and approved MQTT layout are retained.

The recorded failed RADIO_TEST example distinguishes ACCEPTED from execution FAILED; no new radio test is sent. Static desktop/mobile screens were rendered and visually inspected. No live application source, backend, firmware or settings were changed.
