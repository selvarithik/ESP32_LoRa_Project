# Design V3 - compact response card

Preview only; no live app or firmware modifications. The approved MQTT structure is preserved.

Changes requested: remove the four-column route table. ACK uses the simple prior bubble with acceptance status and time only, without device metadata. Execution RESPONSE uses the supplied reference-card structure at a compact desktop width: command, from/to, ACK status, actual execution outcome, optional duration, collapsible payload, Copy JSON, error and footer. Plain warm-neutral conversation background replaces the dotted blue canvas. Brand red/navy, company SVG and navigation remain unchanged.

The example is a recorded RADIO_TEST rejection, not a new radio transmission. ACK acceptance does not imply execution success. Duration is shown as Not reported rather than invented. Device fields belong only to the response card. No backend connection is made by this preview.

Static desktop and mobile SVGs were rendered and visually inspected. Open index.html for the offline design switcher.
