# Physical USB network commissioning

The `network_config` serial operation commissions an explicit Master/Slave build
without resetting the account or bypassing first-login restrictions on web pages.
Physical USB possession and an exact `confirm_device_id` are required. The request
contains only `op`, `confirm_device_id` and a nonempty `config` object. Standard
typed configuration validation runs before any NVS save. Restart to reload the
transport's settings snapshot.

Permitted configuration fields: `wifi_ssid`, `wifi_password`, `wifi_dhcp`,
`master_id`, `master_host`, `mesh_key`, `local_ip_enabled`, `routing_policy`,
`server_host`, `server_port`, `server_https`, `local_ip_token`,
`allowed_peers_csv`. There are no MQTT, sensor, account, role or radio fields in
this operation. Role commissioning remains a separate identity-confirmed operation.

Read credentials from the existing protected local stores, send them directly
through USB, and never echo requests or place credentials in command arguments,
tracked files, HTTP forms or ordinary MQTT. The response contains only a result
code. Do not reset NVS, reinitialize accounts or rotate broker credentials to
establish this local link.

The local IP path uses the existing challenge/response HMAC protocol. A Slave is
assigned to a specific Master ID/address, shares a mesh authentication key with
that Master, and appears in the Master's explicit peer allowlist. The Gateway
enrollment must assign that same physical Slave identity to the Master. Keep
`MASTER_ONLY` when testing Slave -> Master -> Gateway; a direct Slave connection
is not evidence that forwarding works. A Master's QUEUED receipt is distinct
from Gateway persistence.

Tests: `python test/check_network_commission.py` checks the production allowlist,
size bounds and identity gate, including rejection of MQTT/sensor/account fields.
Firmware build and physical chain verification are separate evidence categories.
