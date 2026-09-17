SELVARITHIK'S LORA GATEWAY
FULL PROJECT README / TECHNICAL DOCUMENTATION
============================================================

Project repository
------------------
GitHub: https://github.com/selvarithik/ESP32_LoRa_Project
Branch documented: main
Documented commit: 49166ec3b71e5da9ecc5be0763ce34fd8d807b73
Commit message: Redesign IoT gateway web UI

Purpose of this document
------------------------
This README documents the project as it exists in the repository source code on
main at the commit above, together with the target ESP32/E220 firmware architecture
and phased development plan supplied for the project. It describes the current
Gateway implementation, backend modules, data flow, web pages, REST APIs,
Socket.IO events, database model, command lifecycle, communication/mesh layer,
firmware/OTA management layer, private chat behavior, simulator, runtime
procedure, known source-level limitations, and the intended ESP32 firmware
workflow for the production system.

IMPORTANT DOCUMENTATION RULE
----------------------------
There are two different states described in this README:

    CURRENT = functionality evidenced in the repository source code.
    TARGET  = functionality specified in the ESP32/E220 functional plans and
              intended to be implemented in later firmware phases.

The TARGET architecture must not be interpreted as proof that every feature is
already implemented. For example, the current server-side communication manager
is transport-independent and explicitly provides a callback integration point
for a future physical transport; it does not directly control an E220 radio.
Likewise, the current Gateway database and web UI provide substantial command,
telemetry, mesh, firmware/OTA and chat management, while the ESP32 firmware that
will run on the physical ESP32-WROOM-32 + E220-900T22D is a separate implementation
workstream.


1. PROJECT OVERVIEW
===================

SELVARITHIK'S LORA GATEWAY is a Python/Flask-based gateway control center for
managing registered embedded nodes and their telemetry, commands, communication,
mesh topology, firmware metadata/OTA jobs, logs, and gateway-to-node private chat.

The project is organized as a modular server application with a browser-based
HTML/CSS/JavaScript dashboard and a small Socket.IO simulator for development.
The current repository contains four main areas:

    backend/     Python gateway server and manager modules
    dashboard/   Jinja2 HTML templates + browser CSS/JavaScript
    protocol/    Shared telemetry message construction
    simulator/  Development node simulators

The top-level repository currently contains these directories/files:

    .gitignore
    backend/
    dashboard/
    protocol/
    simulator/

The GitHub tree also contains the separate backend manager modules for nodes,
sensors, telemetry, commands, communication, routing, mesh, firmware, OTA,
chat, database and configuration-related operations.


2. HIGH-LEVEL ARCHITECTURE
==========================

The runtime architecture is approximately:

    Embedded node / simulator
            |
            | Socket.IO telemetry event in current test environment
            v
    Flask + Flask-SocketIO gateway server
            |
            +--> node_manager.py
            |       Node identity/status/configuration
            |
            +--> sensor_manager.py
            |       Parameter definitions and graph configuration
            |
            +--> telemetry_manager.py
            |       Historical/latest values and statistics
            |
            +--> database.py
            |       SQLite persistence in data/gateway.db
            |
            +--> command_manager.py
            |       Command lifecycle + ACK/response audit trail
            |
            +--> communication_manager.py
            |       Transport-independent packet/queue/ACK layer
            |
            +--> packet_manager.py
            |       Packet encoding/decoding/validation/CRC
            |
            +--> mesh_manager.py
            |       Mesh nodes, links, master, topology, settings
            |
            +--> routing_manager.py
            |       Direct/relay route selection and link scoring
            |
            +--> firmware_manager.py
            |       Release metadata + firmware files + SHA-256/manifest
            |
            +--> ota_manager.py
            |       OTA policies, states, device state and jobs
            |
            +--> chat_manager.py
                    Gateway private chat persistence/status

The browser dashboard communicates with the backend through normal HTTP JSON
requests and also uses Socket.IO for live events. The backend therefore uses
both REST-style APIs and Socket.IO; this is NOT a REST-only application.

The server creates a Flask application using the dashboard templates as its
Jinja2 template folder and dashboard/static as its static folder. It creates a
Flask-SocketIO server with cors_allowed_origins="*". The current development
entry point starts Socket.IO on 127.0.0.1:5000 with debug mode enabled.


3. CURRENT RUNTIME MODEL
========================

The current source runs in local/development mode.

Server host:
    127.0.0.1

Server port:
    5000

Browser URL:
    http://127.0.0.1:5000

Time zone used by the browser common application layer:
    Asia/Kolkata

Database:
    data/gateway.db

Firmware storage:
    data/firmware/releases/<release_id>/firmware.bin

Firmware staging:
    data/firmware/staging/

OTA configuration:
    data/firmware/ota_config.json

The server is started by executing backend/server.py directly. The code ends
with socketio.run(app, host="127.0.0.1", port=5000, debug=True,
allow_unsafe_werkzeug=True).

This should be treated as a development/local configuration. The repository
source is not presented as production-hardened internet-facing deployment
configuration.


4. DIRECTORY STRUCTURE
======================

Project root
------------

ESP32_LoRa_Project/
|
+-- .gitignore
|
+-- backend/
|   +-- chat_manager.py
|   +-- command_manager.py
|   +-- communication_manager.py
|   +-- config_manager.py
|   +-- database.py
|   +-- firmware_manager.py
|   +-- mesh_manager.py
|   +-- node_manager.py
|   +-- ota_manager.py
|   +-- packet_manager.py
|   +-- routing_manager.py
|   +-- sensor_manager.py
|   +-- server.py
|   +-- telemetry_manager.py
|
+-- dashboard/
|   +-- static/
|   |   +-- css/
|   |   |   +-- chat.css
|   |   |   +-- command_center.css
|   |   |   +-- communication.css
|   |   |   +-- firmware.css
|   |   |   +-- style.css
|   |   |
|   |   +-- js/
|   |       +-- app.js
|   |       +-- chat.js
|   |       +-- command_center.js
|   |       +-- communication.js
|   |       +-- dashboard.js
|   |       +-- firmware.js
|   |       +-- logs.js
|   |       +-- nodes.js
|   |       +-- sensors.js
|   |       +-- system-overview.js
|   |       +-- system.js
|   |
|   +-- templates/
|       +-- base.html
|       +-- chat.html
|       +-- command_center.html
|       +-- communication.html
|       +-- firmware.html
|       +-- index.html
|       +-- logs.html
|       +-- nodes.html
|       +-- sensors.html
|       +-- system-overview.html
|       +-- system.html
|
+-- protocol/
|   +-- messages.py
|
+-- simulator/
    +-- node_001.py
    +-- node_002.py


5. BACKEND MODULES
==================

5.1 server.py
-------------
server.py is the main Flask/Socket.IO application entry point.

Responsibilities include:

    * Create the Flask application.
    * Register browser page routes.
    * Register REST APIs.
    * Receive Socket.IO telemetry events.
    * Emit live node/command/chat updates.
    * Create system log records.
    * Connect the managers together.
    * Start the development server.

The server imports:

    Flask
    Flask-SocketIO
    node_manager
    config_manager
    telemetry_manager
    sensor_manager
    database
    firmware_manager
    ota_manager
    command_manager
    communication_manager
    mesh_manager
    routing_manager
    chat_manager

The server has a module-level in-memory dictionary named "nodes". Incoming
telemetry is also copied into this dictionary by node_id. Historical telemetry
is separately stored in SQLite through telemetry_manager.


5.2 node_manager.py
-------------------
Node Manager is responsible for the registered node inventory and basic node
status.

Supported MCU values defined in source include:

    ESP32-WROOM-32
    ESP32-S3
    ESP32-C3
    ESP8266
    Arduino UNO
    Arduino Nano
    Other

Supported communication values include:

    LoRa
    IP/TCP
    Wi-Fi
    ESP-NOW
    BLE

Node records contain, among other fields:

    node_id
    name
    mcu_family
    mcu_model
    hardware_revision
    firmware_version
    communication_type
    communication_config
    node_address
    enabled
    status
    last_seen
    created_at
    updated_at

Node status behavior:

    * Newly enabled nodes are initially offline until telemetry is received.
    * Disabled nodes use status "disabled".
    * Incoming telemetry from an enabled registered node changes it to online.
    * The offline timeout is 60 seconds by default.

Node Manager supports add, update, get, delete, enable/disable and status
updates, plus checking for stale/offline nodes.


5.3 sensor_manager.py
---------------------
Sensor Manager handles the configuration of logical sensor parameters. A
physical sensor can expose multiple parameters.

Examples represented by the default catalog include:

    Temperature        FLOAT   °C
    Humidity           FLOAT   %RH
    Air Quality        INT     AQI
    Battery Voltage    FLOAT   V
    Battery Current    FLOAT   mA
    Battery Power      FLOAT   W
    Battery Level      FLOAT   %
    Pressure           FLOAT   hPa
    Current             FLOAT   mA
    Voltage             FLOAT   V
    Power               FLOAT   W
    RSSI                INT     dBm
    SNR                 FLOAT   dB
    Network Status      ENUM
    Wi-Fi Signal        INT     dBm
    CPU Temperature     FLOAT   °C
    Uptime              UINT32  s
    Free Memory         UINT32  bytes
    Sensor Status       ENUM
    Device Status       ENUM

A parameter can have:

    parameter_id
    sensor_id
    parameter_name
    parameter_type
    data_type
    unit
    description
    enabled
    display_enabled
    graph_enabled
    decimal_places
    min_value
    max_value
    alarm_enabled
    low_alarm
    high_alarm
    created_at
    updated_at

When a parameter is added, a default graph configuration is also created.


5.4 telemetry_manager.py
-------------------------
Telemetry Manager is the persistence and readout layer for parameter values.

A telemetry value is stored in telemetry_values with:

    node_id
    parameter_id
    timestamp
    value
    text_value
    data_type
    quality
    status
    source

Numeric parameter data types handled as numeric values include:

    FLOAT
    DOUBLE
    INT
    UINT
    UINT32

The manager provides:

    save_value()
    save_parameters()
    get_history()
    get_compare_data()
    get_latest_value()
    get_latest_values()
    get_statistics()
    get_all_statistics()

History defaults to 300 rows unless another limit is supplied.

Statistics returned include:

    current
    minimum
    maximum
    average
    sample_count
    last_update

Alarm state calculation is:

    timestamp missing                 -> NO_DATA
    quality != GOOD                   -> SENSOR_ERROR
    value is None                     -> NO_DATA
    alarm disabled                    -> NORMAL
    value below low_alarm             -> LOW
    value above high_alarm             -> HIGH
    otherwise                         -> NORMAL


5.5 command_manager.py
----------------------
Command Manager is the server-side command lifecycle/state-machine layer.
It does not by itself prove a physical radio transmission occurred; it manages
the command record, lifecycle transitions and server APIs around that lifecycle.

Command states:

    QUEUED
    SENT
    WAITING_ACK
    ACK_RECEIVED
    EXECUTING
    RESPONSE_RECEIVED
    TIMEOUT
    FAILED
    CANCELLED
    COMPLETED

Terminal states:

    COMPLETED
    FAILED
    CANCELLED
    TIMEOUT

Default command values:

    timeout_seconds = 30
    max_retries     = 3
    priority        = 1

Validation ranges defined by code:

    timeout_seconds = 1 .. 3600
    max_retries     = 0 .. 10
    priority        = 1 .. 10

Generated identifiers use formats similar to:

    CMD-XXXXXXXXXXXX
    EVT-XXXXXXXXXXXX

The command manager validates node IDs, command types and JSON payloads, stores
commands in the commands table and records immutable lifecycle events in
command_events.

Retry is explicitly supported from TIMEOUT and FAILED back into QUEUED.


5.6 packet_manager.py
---------------------
Packet Manager defines the transport-independent application packet format.

Protocol version:
    1

Packet type numbers:

    TELEMETRY  = 1
    CHAT       = 2
    CONTROL    = 3
    ACK        = 4
    NACK       = 5
    DIAGNOSTICS= 6
    ERROR      = 7
    CONFIG     = 8
    DISCOVERY  = 9
    ROUTING    = 10

The packet object includes fields such as:

    v
    id
    type
    source
    destination
    next_hop
    ttl
    priority
    flags
    ts
    payload
    crc

Packet constraints defined in code:

    Maximum application encoded size = 180 bytes
    Default TTL                       = 5
    Maximum TTL                       = 10
    Node/packet identifier limit      = 32 chars

IMPORTANT:
The 180-byte limit is an application safety limit in this code. The source
explicitly states that it is NOT the E220 radio's maximum packet size.

Encoding is compact UTF-8 JSON. CRC32 is calculated over canonical JSON without
the crc field. Incoming packets are decoded, validated, and CRC-checked.


5.7 communication_manager.py
----------------------------
Communication Manager provides a common server-side communication abstraction.
The module comments identify planned/compatible transports as:

    LoRa
    Wi-Fi
    Ethernet
    USB
    BLE

Its responsibilities are:

    * Create packets through packet_manager.
    * Select a route through routing_manager.
    * Add the chosen next hop.
    * Encode the packet.
    * Track required ACKs.
    * Queue or send data.
    * Decode received packets.
    * Reject duplicates.
    * Maintain packet statistics.

Internal resources include:

    outgoing queue: max 500
    incoming queue: max 500
    recent message IDs: max 1000

Statistics tracked include:

    packets_created
    packets_sent
    packets_received
    packets_failed
    ack_received
    nack_received
    duplicates_dropped
    crc_errors
    decode_errors
    route_failures
    retries

Physical transport integration:

    communication_manager.set_send_callback(callback)

The callback signature documented in source is effectively:

    callback(raw_bytes, next_hop)

CRITICAL CURRENT BEHAVIOR:
If no physical send callback is registered, Communication Manager queues the
encoded packet in its outgoing queue for simulator/API inspection/testing.
Therefore, the current repository does not automatically transmit that packet
through an E220 radio merely because the web "send" API was called.


5.8 mesh_manager.py
-------------------
Mesh Manager keeps server-side mesh state in memory.

It maintains:

    * master node ID
    * gateway connection information
    * mesh node roles
    * node last-seen/online state
    * neighbor/link information
    * route information
    * mesh settings

Gateway connection types allowed by source:

    Wi-Fi
    Ethernet
    USB
    BLE

Default mesh settings:

    uplink_threshold     = 30.0
    downlink_threshold   = 30.0
    measurement_window   = 20
    max_hops              = 5
    retry_count           = 3
    route_timeout_seconds= 60

A mesh node can have role NODE or MASTER. Setting one master updates the other
registered mesh nodes to role NODE.

Link information can include:

    RSSI
    SNR
    success_rate
    packet_loss
    latency_ms
    retries


5.9 routing_manager.py
----------------------
Routing Manager performs practical route selection using mesh information.

Core behavior:

    1. If source == destination, return a local route.
    2. Check for a direct source->destination link.
    3. Accept a direct route when its success rate is at or above the direction's
       threshold.
    4. If direct routing is not usable, evaluate two-hop relay candidates.
    5. Keep the best relay and a backup relay when available.

Uplink and downlink thresholds are handled separately.

The link score weights are:

    success rate = 70%
    RSSI         = 15%
    SNR          = 10%
    retry penalty= up to 5 points

RSSI and SNR are normalized into supporting score components. The implementation
currently focuses on direct links and two-hop relay selection rather than a full
arbitrary-hop graph search.


5.10 firmware_manager.py
------------------------
Firmware Manager handles server-side firmware release metadata and binaries.

Storage structure:

    data/firmware/releases/<release_id>/firmware.bin

Staging:

    data/firmware/staging/

Release states:

    DRAFT
    TESTING
    APPROVED
    ACTIVE
    RETIRED
    REVOKED

Channels:

    stable
    beta
    dev

Firmware file rules:

    minimum file size = 1 byte
    maximum file size = 16 MiB
    extension          = .bin

Version format follows semantic version syntax such as:

    1.2.3

Build numbers must be zero or greater.

The manager:

    * validates firmware metadata
    * validates the .bin file
    * calculates SHA-256
    * creates release metadata in SQLite
    * stores firmware.bin under a safe release directory
    * writes manifest.json
    * rejects duplicate hardware/version/build/channel combinations
    * validates release path safety

The manifest contains release information including version, build, hardware,
SHA-256, signature field, channel, release notes, security version and status.


5.11 ota_manager.py
--------------------
OTA Manager controls firmware update policy and server-side OTA job/state data.

OTA states:

    IDLE
    CHECKING
    UPDATE_AVAILABLE
    APPROVED
    DOWNLOADING
    VERIFYING
    READY_TO_BOOT
    REBOOTING
    VALIDATING
    SUCCESS
    FAILED
    ROLLBACK
    CANCELLED

Default OTA policy:

    ota_enabled          = true
    update_channel       = stable
    automatic_updates    = false
    check_interval_hours = 6
    manual_approval      = true
    rollback_enabled     = true
    allow_downgrade      = false
    require_https        = true

The OTA configuration is stored in:

    data/firmware/ota_config.json

The OTA manager stores device firmware state and update jobs in SQLite.
Only ACTIVE releases are allowed for OTA jobs. The source also prevents multiple
simultaneous non-terminal OTA jobs for the same node.

The OTA layer checks hardware compatibility and firmware version/build before
creating update jobs.


5.12 chat_manager.py
---------------------
Private Chat is a gateway application/database feature.

The source explicitly separates private chat from LoRa/M2M communication:

    * no communication_manager call
    * no LoRa packet creation
    * no mesh routing
    * no ESP32<->ESP32 M2M path

Current conceptual participants:

    GATEWAY / Gateway Control Center
    registered nodes from Node Management

Node names are used as display names, while node_id is the permanent identity.

Private conversations are stored in SQLite. Message statuses include:

    SENT
    DELIVERED
    SEEN
    FAILED

Messages have sender, receiver, text, timestamps and status fields.
The current server-side send API only allows "GATEWAY" as the sender.

Therefore the current Private Chat page is an operator-to-node application
chat/history feature, not a second LoRa protocol.


5.13 database.py
-----------------
SQLite is the persistence layer.

Database file:

    data/gateway.db

The database module creates data/ automatically and uses sqlite3 with:

    check_same_thread=False
    row_factory = sqlite3.Row

Major tables created by initialize_database():

    chat_conversations
    chat_messages
    nodes
    sensors                 (legacy compatibility)
    sensor_parameters
    sensor_graphs
    telemetry_values
    commands
    command_events
    logs
    telemetry               (legacy compatibility)
    firmware_releases
    device_firmware
    firmware_update_jobs
    firmware_update_events

The source contains indexes for telemetry, parameters, commands, logs, chat,
and firmware state/event lookups.

The database initialization function is called when database.py is run directly.
server.py itself uses get_connection() throughout its manager operations.


6. TELEMETRY DATA FLOW
======================

Current simulator flow
----------------------

    simulator/node_001.py or node_002.py
                |
                | Socket.IO "telemetry"
                v
    server.py receive_telemetry(data)
                |
                +--> validate data is dict and has node_id
                |
                +--> nodes[node_id] = data
                |
                +--> look up registered node
                |       |
                |       +--> enabled -> status = online
                |
                +--> read sensor/battery/lora sections
                |
                +--> map incoming fields to registered sensor_parameters
                |
                +--> save matched values through telemetry_manager
                |
                +--> console telemetry summary
                |
                +--> Socket.IO "node_update" broadcast

The mapping logic recognizes common parameter names/IDs for:

    temperature
    humidity
    battery voltage
    battery percentage/level
    current
    power
    RSSI
    SNR
    packets TX
    packets RX

This allows the simple telemetry message produced by protocol/messages.py to
feed the generic parameter database, provided the corresponding parameters
are registered for the node.


7. LEGACY/SIMPLE TELEMETRY MESSAGE FORMAT
==========================================

protocol/messages.py defines create_telemetry(). It produces a message such as:

    {
      "type": "telemetry",
      "timestamp": "...",
      "node_id": "NODE-001",
      "sensor": {
        "temperature": 29.4,
        "humidity": 60.2
      },
      "battery": {
        "voltage": 4.15,
        "percent": 94.4,
        "current_ma": 81.2,
        "power_mw": 337.0
      },
      "lora": {
        "rssi": -69.5,
        "snr": 9.8,
        "packets_tx": 12,
        "packets_rx": 11
      },
      "device": {
        "firmware": "v1.0.0",
        "uptime": 24,
        "status": "online"
      }
    }

Actual key details and rounding are defined by protocol/messages.py.

The richer packet_manager.py packet format is separate from this simple
telemetry message helper. The current simulator uses create_telemetry() over
Socket.IO rather than sending the packet_manager application packet through an
E220 transport.


8. SIMULATOR
============

The repository contains two Socket.IO development nodes:

    simulator/node_001.py
    simulator/node_002.py

Both connect to:

    http://127.0.0.1:5000

Both emit Socket.IO event:

    telemetry

Every 2 seconds.

Node 001
--------

    NODE_ID = NODE-001
    FIRMWARE = v1.0.0
    initial battery voltage = 4.15 V
    temperature center       = 29.0 C
    humidity center          = 60.0 %
    current center           = 80 mA
    RSSI center              = -70 dBm
    SNR center               = 9 dB
    RX loss probability     ~= 2%

Node 002
--------

    NODE_ID = NODE-002
    FIRMWARE = v1.0.0
    initial battery voltage = 4.05 V
    temperature center       = 30.0 C
    humidity center          = 57.0 %
    current center           = 95 mA
    RSSI center              = -78 dBm
    SNR center               = 7 dB
    RX loss probability     ~= 3%

The simulator also prints JSON telemetry to the terminal.

These scripts are for development/testing. They are not an implementation of
actual LoRa/E220 radio communication.


9. WEB DASHBOARD
================

The dashboard uses Jinja2 templates with a shared base.html shell.

The current UI uses a compact horizontal top navigation instead of the old
large left sidebar. The navigation provides:

    Dashboard
    Nodes
    Sensors
    Commands
    Network
    Firmware
    Logs
    Health
    System
    Chat

The shared header also contains:

    * global page search
    * logs/alert access
    * live clock
    * gateway online indicator
    * light/dark theme switch
    * accent palette
    * advanced appearance editor
    * mobile navigation


10. DASHBOARD PAGE
==================

URL:
    /

Template:
    dashboard/templates/index.html

Main purpose:
    operational overview and live telemetry.

Current dashboard areas include:

    * system metrics summary
    * live telemetry analytics chart
    * connected node status table
    * selected node sensor summary
    * custom sensor widgets
    * gateway activity stream

The dashboard exposes customization for visibility/layout preferences and
custom sensor widgets.

Built-in dashboard widget groups include:

    System Metrics Summary
    Live Telemetry Sensor Graph
    Connected Node Status
    Selected Node Sensor Cards
    Custom Sensor Widgets
    Recent Gateway Activity Stream

The client stores dashboard widget preferences in localStorage.

Custom sensor widgets can currently select:

    node
    sensor/parameter
    visualization type
    color
    whether node/last-update metadata is shown

Supported visualizations in the current dashboard template include:

    Numeric Value
    Gauge
    Horizontal Bar
    Status

The dashboard controller polls live data every 2 seconds.


11. NODE MANAGEMENT PAGE
========================

URL:
    /nodes

Template:
    dashboard/templates/nodes.html

Features:

    * search nodes
    * refresh
    * add node
    * edit/configure node
    * enable/disable
    * delete
    * view status/last-seen information

Node table columns shown in the current template:

    Node
    Node ID
    MCU
    Communication
    Firmware
    Status
    Last Seen
    Actions

The configuration drawer contains identity, hardware, communication and status
fields.


12. SENSOR MANAGEMENT PAGE
==========================

URL:
    /sensors

Template:
    dashboard/templates/sensors.html

Features:

    * node selection
    * parameter search
    * All/Enabled/Alarm/Graph filters
    * sensor parameter table
    * parameter detail drawer

Table fields include:

    Parameter
    Value
    Unit
    Quality
    Status
    Last Update
    Action

The backend supports CRUD, parameter enable/disable, graph configuration,
latest data, history, comparison and statistics through dedicated APIs.


13. COMMAND CENTER
===================

URL:
    /command-center

Template:
    dashboard/templates/command_center.html

Command Center contains:

    * node selector/list
    * device status and hardware information
    * selected node summary
    * active command state
    * command lifecycle stepper
    * command metadata
    * ACK status
    * response status
    * returned JSON payload viewer
    * command error area
    * command history
    * event timeline
    * cancel/retry actions
    * command configuration form

Command types visible in the current UI include:

    STATUS
    PING
    WIFI_SCAN
    WIFI_CONNECT
    RESTART
    GET_CONFIG
    SET_INTERVAL
    CUSTOM

Important distinction:
The UI can create and track commands through the backend command core. The
current communication manager still requires a physical transport callback for
real radio transmission. Without one, communication packets are queued for
testing.


14. COMMUNICATION CENTER
========================

URL:
    /communication

Template:
    dashboard/templates/communication.html

The page exposes:

    * master node
    * gateway connection
    * uplink threshold
    * downlink threshold
    * packet statistics
    * mesh node list
    * mesh link details
    * route test
    * mesh settings

Packet statistics shown by the interface map to the communication manager's
counters such as packets created/sent/received/failed, ACKs, retries, route
failures and duplicates dropped.

The communication layer is intentionally transport-independent, while the
current repository does not include a direct E220 UART adapter in
communication_manager.py.


15. FIRMWARE / OTA PAGE
=======================

URL:
    /firmware

Template:
    dashboard/templates/firmware.html

Current sections:

    * Firmware Upload
    * Firmware Releases
    * Device Firmware
    * Update Jobs
    * Update History
    * OTA Configuration

Firmware upload accepts .bin files and gathers:

    version
    build
    hardware family
    hardware model
    hardware revision
    channel
    minimum bootloader
    security version
    mandatory flag
    release notes

The release lifecycle visible in the page is:

    DRAFT -> TESTING -> APPROVED -> ACTIVE

The backend also defines RETIRED and REVOKED.

The device table shows current and target versions plus OTA state/channel.

The job table shows job ID, node, source version, target version, state,
progress, start/completion time and result.


16. SYSTEM OVERVIEW / HEALTH
============================

URL:
    /system-overview

Template:
    dashboard/templates/system-overview.html

The page provides one-glance health areas:

    Gateway Status
    Node Status
    Communication
    Sensor Status
    System Health

It also includes recent events and a link to Logs.


17. LOGS PAGE
=============

URL:
    /logs

The backend log storage table contains:

    id
    timestamp
    severity
    source
    message
    node_id

The API supports filtering by:

    severity
    search text
    date

Search checks message, source and node_id. Results are limited to 500 rows.

Logs are created by several backend operations including node changes, command
state changes, firmware actions, OTA configuration updates and system actions.


18. SYSTEM PAGE
===============

URL:
    /system

This page is the system configuration/maintenance area in the dashboard. The
backend exposes safe development-mode system actions including:

    POST /api/system/reboot
    POST /api/system/factory-reset

The reboot endpoint currently records the request and returns an acceptance
message; it does not terminate or physically reboot the Flask process. The
source explicitly describes this behavior as development/web-dashboard safe.

Factory reset requires JSON confirmation:

    {"confirm": true}

It resets node configuration for registered nodes through the configuration
manager layer and records a log.


19. PRIVATE CHAT PAGE
=====================

URL:
    /chat

Private Chat is intentionally separate from LoRa/M2M communication.

Current concept:

    Browser/Gateway operator
            |
            v
    Flask chat API
            |
            v
    SQLite chat tables
            |
            v
    registered node identities

The current server chat send endpoint requires:

    sender_id == "GATEWAY"

Chat users are derived from enabled Node Management records, and display names
come from the node name field.

Conversation and message data are persisted in:

    chat_conversations
    chat_messages

Message state progression used by chat code:

    SENT -> DELIVERED -> SEEN

FAILED is also defined.

No LoRa packet or mesh route is created by chat_manager.py.


20. BASE UI / THEME SYSTEM
==========================

base.html is the shared Jinja2 shell for most pages.

The current frontend includes:

    Light / Dark theme
    Theme presets including light, dark, midnight, clean, contrast
    Accent choices including orange, emerald, cyan, indigo, amber
    Advanced appearance editor
    Global theme CSS tokens
    Mobile navigation

The common application JavaScript in app.js provides:

    * HTML escaping helper
    * status normalization
    * India/Asia-Kolkata time formatting
    * HTTP API helpers
    * toast notifications
    * theme/accent/appearance state handling

The common API helper uses the browser fetch() API directly and leaves the API
base prefix empty by default, so paths such as /api/nodes are called on the same
origin as the dashboard.

Theme and dashboard customization data are client-side browser preferences and
are persisted through localStorage rather than the SQLite backend.


21. REST API REFERENCE
======================

The following is a practical map of the server endpoints visible in the current
server.py source.

PAGE ROUTES
-----------

GET  /
GET  /system-overview
GET  /nodes
GET  /sensors
GET  /communication
GET  /chat
GET  /system
GET  /logs
GET  /firmware
GET  /command-center

SYSTEM STATUS / LOGS
--------------------

GET  /api/status
GET  /api/logs
    Query parameters:
        severity
        search
        date

NODE MANAGEMENT
---------------

GET    /api/nodes
GET    /api/nodes/<node_id>
POST   /api/nodes
PUT    /api/nodes/<node_id>
DELETE /api/nodes/<node_id>
POST   /api/nodes/<node_id>/enable

NODE CONFIGURATION
------------------

GET  /api/nodes/<node_id>/config
PUT  /api/nodes/<node_id>/config
POST /api/nodes/<node_id>/config/reset

SENSOR PARAMETERS
-----------------

GET    /api/nodes/<node_id>/parameters
POST   /api/nodes/<node_id>/parameters
GET    /api/nodes/<node_id>/parameters/<parameter_id>
PUT    /api/nodes/<node_id>/parameters/<parameter_id>
DELETE /api/nodes/<node_id>/parameters/<parameter_id>
POST   /api/nodes/<node_id>/parameters/<parameter_id>/enable
GET    /api/parameters/defaults

GRAPH CONFIGURATION
-------------------

GET /api/nodes/<node_id>/parameters/<parameter_id>/graph
PUT /api/nodes/<node_id>/parameters/<parameter_id>/graph

TELEMETRY
---------

POST /api/telemetry
GET  /api/nodes/<node_id>/parameters/latest
GET  /api/nodes/<node_id>/parameters/statistics
GET  /api/nodes/<node_id>/parameters/<parameter_id>/statistics
GET  /api/nodes/<node_id>/telemetry/<parameter_id>
GET  /api/nodes/<node_id>/telemetry/compare

Compare query string:
    parameters=temperature,humidity
    limit=300

FIRMWARE RELEASES
-----------------

GET  /api/firmware/releases
POST /api/firmware/releases
GET  /api/firmware/releases/<release_id>
POST /api/firmware/releases/<release_id>/status

FIRMWARE DEVICES / OTA JOBS
---------------------------

GET  /api/firmware/devices
GET  /api/firmware/devices/<node_id>
POST /api/firmware/check
POST /api/firmware/update
GET  /api/firmware/jobs
GET  /api/firmware/jobs/<job_id>
POST /api/firmware/jobs/<job_id>/state
POST /api/firmware/device/<node_id>/check
GET  /api/firmware/download/<release_id>

OTA CONFIGURATION
-----------------

GET /api/firmware/config
PUT /api/firmware/config

COMMANDS
--------

POST /api/commands
GET  /api/commands
GET  /api/commands/<command_id>
GET  /api/commands/node/<node_id>
POST /api/commands/<command_id>/state
POST /api/commands/<command_id>/cancel
POST /api/commands/<command_id>/timeout
POST /api/commands/<command_id>/ack
POST /api/commands/<command_id>/execute
POST /api/commands/<command_id>/response
GET  /api/commands/<command_id>/events
POST /api/commands/<command_id>/retry

COMMUNICATION / MESH
--------------------

GET  /api/communication/status
GET  /api/communication/mesh
GET  /api/communication/settings
PUT  /api/communication/settings
GET  /api/communication/master
PUT  /api/communication/master
GET  /api/communication/gateway
PUT  /api/communication/gateway
POST /api/communication/mesh/nodes
DELETE /api/communication/mesh/nodes/<node_id>
POST /api/communication/mesh/link
GET  /api/communication/mesh/<node_id>/neighbors
GET  /api/communication/route
POST /api/communication/send
POST /api/communication/receive
GET  /api/communication/statistics
GET  /api/communication/queue/outgoing
GET  /api/communication/queue/incoming
POST /api/communication/queue/clear

CHAT
----

GET  /api/chat/users
GET  /api/chat/conversations
GET  /api/chat/messages
POST /api/chat/messages
GET  /api/chat/messages/<message_id>
POST /api/chat/messages/<message_id>/delivered
POST /api/chat/messages/<message_id>/seen

SYSTEM MAINTENANCE
------------------

POST /api/system/reboot
POST /api/system/factory-reset


22. REST API BEHAVIOR DETAILS
=============================

22.1 Node list
--------------
GET /api/nodes performs an offline-node check before returning registered node
records. The configured default timeout is 60 seconds without fresh telemetry.

22.2 Telemetry history
----------------------
GET /api/nodes/<node_id>/telemetry/<parameter_id> returns historical rows for the
selected parameter. The default manager limit is 300.

22.3 Statistics
---------------
Statistics are computed from recent numeric samples and include current, min,
max, average, sample count and last update time.

22.4 Command creation
---------------------
POST /api/commands accepts JSON/form data containing at least node_id and
command_type. Optional values include payload, priority, max_retries,
timeout_seconds and command_id.

22.5 Command ACK/response
-------------------------
ACK and response endpoints validate the node and command identity through the
command manager and then broadcast command_update Socket.IO events.

22.6 Firmware upload
--------------------
POST /api/firmware/releases expects a multipart firmware file plus firmware
metadata. The server stages the file, creates a release, calculates SHA-256,
creates a manifest and logs the upload.

22.7 OTA update job
------------------
POST /api/firmware/update requires node_id and release_id. The OTA manager only
allows ACTIVE releases and checks the known device firmware/hardware state.

22.8 Communication send
-----------------------
POST /api/communication/send constructs a packet with communication_manager,
sets the ack_required flag, then asks communication_manager.send() to route and
send it. Without a physical send callback, the packet is queued in memory for
inspection/testing.

22.9 Communication receive
--------------------------
POST /api/communication/receive takes a JSON packet and passes it to
communication_manager.receive(), which validates/decode-checks the application
packet and its CRC.

22.10 Chat send
---------------
POST /api/chat/messages accepts sender_id, recipient_id and content, but the
current server rejects any sender other than GATEWAY.


23. SOCKET.IO EVENTS
====================

Telemetry event received from simulator/client:

    telemetry

The server emits live update events such as:

    node_update
    registered_node
    command_update
    chat_message

get_nodes is a Socket.IO request event. When received, the server emits each
registered node as registered_node and each cached live node payload as
node_update.

The command APIs emit command_update after command state/ACK/execution/response/
timeout/retry operations.

The chat send API emits chat_message after successfully storing a message.


24. DATABASE MODEL SUMMARY
==========================

Nodes
-----
nodes stores device identity, hardware, communication, enabled state and
presence timestamps.

Sensor parameters
-----------------
sensor_parameters describes logical measurements and alarm/display options.

Sensor graphs
-------------
sensor_graphs stores graph visualization configuration per node/parameter.

Telemetry values
----------------
telemetry_values stores timestamped generic values, quality and status.

Legacy telemetry
----------------
telemetry is retained for compatibility and stores older fixed fields such as
temperature/humidity/battery/RSSI/SNR and packet counters.

Commands
--------
commands stores command lifecycle state and timestamps.
command_events stores immutable command lifecycle audit events.

Logs
----
logs stores application/server operational events.

Firmware
--------
firmware_releases stores release metadata.
device_firmware stores server-known current/target firmware state.
firmware_update_jobs stores update jobs.
firmware_update_events stores OTA event history.

Chat
----
chat_conversations stores private conversation identity and timestamps.
chat_messages stores message content, sender/receiver and delivery/read state.


25. DEVELOPMENT SETUP
=====================

Requirements inferred from imports
----------------------------------
The repository does not expose a requirements.txt in the current root tree.
The minimum Python packages directly implied by the source are:

    Flask
    Flask-SocketIO
    python-socketio

SQLite is provided by Python's standard library.

Recommended local setup on Windows
-----------------------------------

1. Open PowerShell.

2. Change to the project directory:

    cd "D:\esp32 selva\TEST\ESP32_LoRa_Project"

3. Optionally create a virtual environment:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1

4. Install the packages inferred from source:

    py -m pip install Flask Flask-SocketIO python-socketio

5. Start the gateway server:

    py backend\server.py

   or:

    python backend\server.py

6. Open the dashboard:

    http://127.0.0.1:5000


26. RUNNING THE SIMULATORS
==========================

Start the server first.

Then open another PowerShell window in the same project directory and run:

    py simulator\node_001.py

Open another PowerShell window if you also want NODE-002:

    py simulator\node_002.py

Both simulators attempt to connect to the local Socket.IO server and transmit a
telemetry event every 2 seconds.

Expected behavior:

    * node status becomes online once the node is registered and telemetry is
      received.
    * dashboard live information changes as simulator values change.
    * telemetry values are stored in SQLite when corresponding parameters are
      configured.
    * the terminal prints the generated telemetry JSON.


27. FIRST-TIME FUNCTIONAL TEST FLOW
===================================

A practical manual test sequence is:

    STEP 1
    Start backend/server.py.

    STEP 2
    Open http://127.0.0.1:5000.

    STEP 3
    Open Nodes and create NODE-001 and/or NODE-002 with communication values
    accepted by node_manager.py.

    STEP 4
    Open Sensors for a node and create parameters that match the simulator
    fields, such as:

        temperature
        humidity
        battery_voltage
        battery_percent
        current
        power
        rssi
        snr
        packets_tx
        packets_rx

    STEP 5
    Run simulator/node_001.py or node_002.py.

    STEP 6
    Return to Dashboard and verify live node status and telemetry.

    STEP 7
    Open Sensors and verify latest values/history/statistics.

    STEP 8
    Open Communication and inspect mesh/packet state. Remember that the current
    transport manager may queue packets rather than physically transmit them.

    STEP 9
    Open Command Center to create and inspect command records/lifecycle. Use
    ACK/execute/response APIs to simulate or integrate command acknowledgements.

    STEP 10
    Open Firmware to upload a .bin release and inspect release metadata and
    OTA job state.

    STEP 11
    Open Logs to verify operational entries generated by the server.

    STEP 12
    Open Chat to test Gateway-to-node private message persistence/status.


28. SAMPLE API TESTS
====================

Get server status
-----------------

    GET http://127.0.0.1:5000/api/status

Add a node
----------

    POST /api/nodes

Example JSON:

    {
      "node_id": "NODE-001",
      "name": "Test Node 1",
      "mcu_family": "ESP32",
      "mcu_model": "ESP32-WROOM-32",
      "hardware_revision": "REV-A",
      "firmware_version": "v1.0.0",
      "communication_type": "LoRa",
      "communication_config": {},
      "node_address": "NODE-001",
      "enabled": true
    }

Create a generic telemetry value
--------------------------------

    POST /api/telemetry

Example JSON:

    {
      "node_id": "NODE-001",
      "parameters": {
        "temperature": 29.5,
        "humidity": 61.0
      }
    }

Get latest parameter values
---------------------------

    GET /api/nodes/NODE-001/parameters/latest

Get parameter history
---------------------

    GET /api/nodes/NODE-001/telemetry/temperature?limit=100

Get statistics
--------------

    GET /api/nodes/NODE-001/parameters/temperature/statistics?limit=300

Create a command
----------------

    POST /api/commands

Example JSON:

    {
      "node_id": "NODE-001",
      "command_type": "PING",
      "payload": {
        "message": "Hello"
      },
      "priority": 1,
      "max_retries": 3,
      "timeout_seconds": 30
    }

Update command state
--------------------

    POST /api/commands/<command_id>/state

Example JSON:

    {
      "state": "SENT"
    }

Check communication route
-------------------------

    GET /api/communication/route?source=NODE-001&destination=NODE-002&direction=downlink

Get communication statistics
---------------------------

    GET /api/communication/statistics

Get logs
--------

    GET /api/logs?severity=warning


29. DATA AND FILE PERSISTENCE
=============================

The repository intentionally ignores runtime data using .gitignore rules that
include:

    data/
    data/*.db
    data/*.sqlite
    data/*.sqlite3

It also ignores:

    .venv/
    __pycache__/
    *.pyc
    .env
    *.env
    .vscode/

This means runtime database and firmware data are expected to remain local and
are not intended to be committed to Git by default.


30. IMPORTANT DIFFERENCE: GENERIC TELEMETRY vs APPLICATION PACKETS
==================================================================

There are two related but distinct concepts in the current code.

A. Simple telemetry message
---------------------------
protocol/messages.py creates a human-readable nested telemetry dictionary and
the simulator sends it through Socket.IO using the "telemetry" event.

B. Transport-independent application packet
-------------------------------------------
packet_manager.py creates versioned packets with packet type, source,
destination, TTL, priority, flags, payload and CRC. communication_manager.py
uses these packets for routing/queue/ACK processing.

The source therefore contains a more general communication protocol layer in
parallel with the current simulator telemetry transport.

This distinction is important when extending the project to a real E220/LoRa
physical transport.


31. REAL E220 / PHYSICAL TRANSPORT INTEGRATION POINT
====================================================

The clean extension point is the Communication Manager send callback.

Conceptually:

    communication_manager.set_send_callback(lora_send)

The callback is expected to accept:

    raw_bytes
    next_hop

The callback would be responsible for the actual hardware transport integration
(for example a serial/UART/E220 driver) while the communication manager keeps
packet creation, routing, ACK tracking and queue logic separated.

The current repository does not provide that direct E220 implementation inside
communication_manager.py, so the README does not claim that the existing web
send API is already a working physical LoRa transmission path.


32. SECURITY / DEPLOYMENT NOTES
===============================

Current source characteristics to be aware of before any production deployment:

    * Flask debug mode is enabled in server.py.
    * allow_unsafe_werkzeug=True is passed to socketio.run().
    * Socket.IO is configured with cors_allowed_origins="*".
    * No authentication/authorization layer is visible in the described server
      APIs.
    * Private Chat is application/database-only and is not end-to-end encrypted
      by this source.
    * Firmware download and OTA controls are server APIs and should be placed
      behind an appropriate security boundary in a real deployment.
    * System maintenance endpoints require application-level confirmation for
      factory reset, but they are not a substitute for a full security model.

These are source-level observations, not a claim that the project cannot be
made production-ready. They are simply items that should be addressed before
public exposure or industrial deployment.


33. KNOWN ISSUES AND VERIFICATION NOTES
========================================

33.1 config_manager.py mismatch
-------------------------------
During direct inspection of the current GitHub source, backend/config_manager.py
was fetched under that path, but its content begins with a chat_manager.py module
description and defines private-chat functionality instead of configuration
manager functions.

At the same time, server.py calls these configuration functions:

    config_manager.get_node_config_with_defaults(node_id)
    config_manager.save_node_config(node_id, config)
    config_manager.reset_node_config(node_id)
    config_manager.load_node_config(node_id)

The fetched config_manager.py content does not show those functions. Therefore,
the node configuration/factory-reset routes should be considered unverified and
are expected to fail with an AttributeError when those missing functions are
actually called, unless the local working copy differs from the inspected GitHub
content.

This issue appears to pre-date the UI redesign because the same mismatch was
visible when the older commit was inspected.

Recommended action:
    Restore/implement backend/config_manager.py so that it actually provides the
    functions expected by server.py. Verify node configuration and factory reset
    behavior afterward.


33.2 Custom dashboard sensor widget endpoint verification
-----------------------------------------------------------
The dashboard.js source contains custom-widget parameter loading code using a
path shaped like:

    /api/parameters/<node_id>

The server.py source exposes the registered parameter API as:

    /api/nodes/<node_id>/parameters

The common gateway.get() helper calls paths directly against the current origin.
Therefore this custom-widget parameter lookup should be tested in the browser.
If the exact /api/parameters/<node_id> request is reached, it will not match the
server route shown in server.py unless another route exists elsewhere.

Recommended action:
    Verify browser Network requests while opening the custom sensor widget
    editor. If the request uses /api/parameters/<node_id>, update dashboard.js
to call the actual parameter endpoint or add the intended backend route, while
keeping API compatibility intentional.


33.3 Reboot behavior
---------------------
The /api/system/reboot endpoint is explicitly development-safe. It logs the
request and returns success; it does not reboot the server machine or hardware.


33.4 Communication physical transport
--------------------------------------
communication_manager.py explicitly states that the module does not directly
talk to the E220 yet. With no send callback, outgoing packets are kept in an
in-memory queue for simulator/API inspection.

Therefore "send" in the web Communication Center currently means application
packet creation/routing/queueing, not necessarily real over-the-air transmission.


33.5 Runtime memory vs SQLite persistence
------------------------------------------
Some communication/mesh state is held in memory rather than SQLite, including
parts of mesh state, route state, packet queues, pending ACK tracking and recent
message IDs. A process restart can therefore reset this runtime state.

Node, telemetry, command, firmware, log and chat records are designed to have
SQLite persistence where the corresponding managers write them.


34. TROUBLESHOOTING
===================

Server does not start
---------------------

Check that the current directory is the project root:

    cd "D:\esp32 selva\TEST\ESP32_LoRa_Project"

Then run:

    py backend\server.py

If Python is not available as py, try:

    python backend\server.py

If imports fail, install the inferred packages:

    py -m pip install Flask Flask-SocketIO python-socketio


Browser shows a blank page or route error
-----------------------------------------

Check the server terminal first.
Then confirm the page URL is exactly:

    http://127.0.0.1:5000

Use the browser developer console to inspect JavaScript errors.

Because the frontend uses Jinja templates and same-origin APIs, a missing API
route usually appears as a failed request in the Network panel.


Node remains offline
--------------------

Verify:

    * node_id in telemetry matches a registered node_id.
    * the node is enabled.
    * simulator connected to 127.0.0.1:5000.
    * the Socket.IO "telemetry" event is reaching server.py.
    * the node has not exceeded the 60-second offline timeout.


Telemetry appears but sensor table is empty
-------------------------------------------

The server maps incoming telemetry fields to registered sensor parameters. A
parameter must exist and its name/ID must match the mapping logic for the
incoming field.

For simulator testing, create parameters such as:

    temperature
    humidity
    battery_voltage
    battery_percent
    current
    power
    rssi
    snr
    packets_tx
    packets_rx


Commands are created but not physically transmitted
---------------------------------------------------

This is expected if no physical transport send callback is registered.
Inspect:

    GET /api/communication/queue/outgoing

and the communication statistics.


Factory reset/configuration API fails
--------------------------------------

Inspect backend/config_manager.py first. The current GitHub source shows a
module-content/path mismatch as documented in Known Issues.


Firmware update job cannot be created
-------------------------------------

Check that:

    * the release exists.
    * release status is ACTIVE.
    * device firmware state exists.
    * hardware family/model/revision match.
    * another active OTA job is not already running for the same node.


35. RECOMMENDED DEVELOPMENT PRACTICES
======================================

When extending this project:

    1. Keep hardware transport code separate from packet/routing logic.
    2. Keep the generic telemetry database model separate from legacy telemetry
       compatibility fields.
    3. Preserve command state-machine transitions instead of bypassing them.
    4. Keep private chat isolated from the LoRa/M2M communication pipeline.
    5. Keep release metadata and firmware binaries separated, as current code does.
    6. Test API paths from the browser Network panel after frontend changes.
    7. Add a requirements.txt or pyproject.toml with pinned versions before
       deployment or reproducible installation.
    8. Add automated tests for node CRUD, telemetry mapping, command lifecycle,
       packet CRC, route selection, firmware release validation and chat rules.
    9. Add authentication/authorization before allowing remote access.
   10. Add the physical E220/UART transport adapter through the documented
       Communication Manager callback boundary.


36. PROJECT CAPABILITIES AT A GLANCE
====================================

Implemented server-side capability groups visible in the current code:

    NODE MANAGEMENT
        registration, metadata, status, enable/disable, delete

    SENSOR MANAGEMENT
        parameter CRUD, alarms, graph configuration

    TELEMETRY
        live event reception, persistence, latest values, history, statistics

    DASHBOARD
        live overview, charts, node/sensor widgets, activity stream

    COMMAND CENTER
        command creation, lifecycle state machine, ACK/response, retries,
        timeout, cancellation, event audit

    COMMUNICATION
        packet creation, validation, queueing, statistics, receive processing

    MESH
        master node, node roles, link metrics, topology, route selection

    ROUTING
        direct route, two-hop relay, score, backup relay

    FIRMWARE
        .bin upload, release lifecycle, SHA-256, manifest, channels

    OTA
        update checking, policy, device state, update jobs, progress/events,
        rollback state definitions

    LOGGING
        timestamped severity/source/message/node records

    PRIVATE CHAT
        gateway-to-registered-node application chat, persistent history,
        delivered/seen state

    UI CUSTOMIZATION
        light/dark, theme presets, accent colors, appearance editor, dashboard
        widget visibility and custom sensor widgets


37. WHAT THIS REPOSITORY IS NOT CLAIMING YET
============================================

Based strictly on the inspected source, the repository should NOT be described
as already providing all of the following without additional implementation or
verification:

    * direct E220 hardware transmission inside communication_manager.py
    * physical ESP32 radio integration merely from the browser send API
    * production-grade authentication/authorization
    * a hardware reboot implementation through /api/system/reboot
    * end-to-end encrypted private chat
    * a fully verified node configuration manager, due to the current
      config_manager.py mismatch
    * a fully verified custom dashboard sensor-widget API path until the browser
      request is checked

The architecture is prepared for these extensions, but the current source and
the verified runtime behavior should be documented separately from future
integration work.


38. QUICK START
===============

Windows / PowerShell
--------------------

    cd "D:\esp32 selva\TEST\ESP32_LoRa_Project"
    py -m pip install Flask Flask-SocketIO python-socketio
    py backend\server.py

Open:

    http://127.0.0.1:5000

Optional simulator:

    py simulator\node_001.py

Second node:

    py simulator\node_002.py

Stop any foreground process with:

    Ctrl+C


39. GIT / PROJECT STATUS NOTE
=============================

The documented UI redesign was committed to the GitHub main branch as:

    49166ec3b71e5da9ecc5be0763ce34fd8d807b73

with message:

    Redesign IoT gateway web UI

The redesign changed the dashboard frontend across the base shell and multiple
page-specific templates/styles/scripts while preserving the existing backend
module structure.

The repository .gitignore excludes runtime data, database files, environments,
compiled Python cache and environment files.


40. SOURCE-BASIS SUMMARY
========================

This README was prepared by inspecting the current GitHub repository source,
including:

    backend/server.py
    backend/database.py
    backend/node_manager.py
    backend/sensor_manager.py
    backend/telemetry_manager.py
    backend/command_manager.py
    backend/packet_manager.py
    backend/communication_manager.py
    backend/mesh_manager.py
    backend/routing_manager.py
    backend/firmware_manager.py
    backend/ota_manager.py
    backend/chat_manager.py
    dashboard/templates/base.html
    dashboard/templates/index.html
    dashboard/templates/nodes.html
    dashboard/templates/sensors.html
    dashboard/templates/command_center.html
    dashboard/templates/communication.html
    dashboard/templates/firmware.html
    dashboard/templates/system-overview.html
    protocol/messages.py
    simulator/node_001.py
    simulator/node_002.py
    dashboard/static/js/app.js
    dashboard/static/js/dashboard.js
    .gitignore

Where source behavior and planned architecture differ, this document follows the
current source and flags the difference rather than silently treating planned
features as already implemented.



41. TARGET ESP32 + E220 FIRMWARE ARCHITECTURE
==============================================

41.1 Scope and target hardware
------------------------------
The target embedded platform is:

    ESP32-WROOM-32
        +
    E220-900T22D LoRa module

The supplied firmware plan defines one standard firmware image for every ESP32.
The device role is selected by persistent configuration, not by maintaining a
separate Master firmware and Node firmware.

The same firmware therefore supports:

    MASTER
    NODE

with the local ESP32 webpage deciding which role is active.

The target firmware is responsible for identity, E220 control, packet handling,
reliable communication, mesh routing, application data, sensors, commands,
heartbeat/status, Gateway communication, local configuration, BLE, Wi-Fi,
Ethernet support, OTA, diagnostics, logging and security.

Reference source plan: the supplied workflow states that every ESP32 runs the
same standard firmware and that the local webpage configures role, identity,
Master relationship, neighbors, radio, sensors, network and OTA. The same plan
also separates the E220 as the LoRa transport underneath the firmware.

41.2 Target network topology
----------------------------
The planned system supports several Masters and many Nodes. Master ownership is
a management relationship, not a hard communication boundary.

Example:

    GATEWAY / SERVER
          |
          +----------------------+----------------------+
          |                      |                      |
      MASTER-01              MASTER-02              MASTER-03
          |                      |                      |
      NODE-01               NODE-04               NODE-07
      NODE-02               NODE-05               NODE-08
      NODE-03               NODE-06               NODE-09

Across those groups, configurable mesh relationships can still exist, for
example:

    NODE-02 <-> NODE-04

Therefore the target communication model supports:

    GATEWAY <-> MASTER
    GATEWAY <-> NODE
    MASTER  <-> NODE
    MASTER  <-> MASTER
    NODE    <-> NODE

A Node can remain managed by its own Master while using an allowed neighbor in
another Master group when the mesh configuration permits it.

41.3 Standard firmware modules
------------------------------
The target embedded firmware is logically organized around:

    Device / Identity
    Role Manager
    Master / Node Manager
    E220 Driver
    Packet Engine
    Reliability Engine
    Neighbor Manager
    Routing Engine
    Forwarding Engine
    Sensor Manager
    Telemetry Engine
    Command Engine
    ACK / Response Engine
    Heartbeat / Status Engine
    Gateway / MQTT Engine
    Wi-Fi Engine
    Ethernet Adapter
    BLE Commissioning Service
    Local Web Configuration
    OTA / Recovery Engine
    Diagnostics / Logging
    Security Layer

The exact source filenames for the future ESP32 firmware are not fixed by the
Gateway repository documented here; the above is the functional decomposition
from the supplied firmware plan.

41.4 Three-plane model
----------------------
The supplied workflow defines a clean three-plane architecture.

MANAGEMENT PLANE
    Master / Node configuration
    Identity
    Master assignment
    Node management
    Neighbor configuration
    Mesh settings
    E220 settings
    Sensor configuration
    Network configuration
    OTA
    Diagnostics

DATA PLANE
    Telemetry
    Commands
    ACK
    Responses
    Status
    Heartbeat
    Events
    Alarms
    Chat

NETWORK PLANE
    E220 LoRa
    Wi-Fi
    Ethernet
    BLE
    MQTT / LAN / Internet

The purpose of this separation is to prevent application logic from becoming
coupled directly to one physical transport.

41.5 ESP32 startup sequence
----------------------------
Target startup sequence from the supplied workflow:

    POWER ON
       |
       v
    Boot
       |
       v
    Load persistent configuration
       |
       v
    Load Device ID / Role
       |
       v
    Initialize system
       |
       v
    Initialize watchdog
       |
       v
    Initialize sensors
       |
       v
    Initialize Wi-Fi / Ethernet / BLE
       |
       v
    Initialize E220
       |
       v
    E220 configuration mode
       |
       v
    Read / apply E220 configuration
       |
       v
    Check AUX
       |
       v
    E220 normal mode
       |
       v
    Start network services
       |
       v
    Start heartbeat
       |
       v
    Start packet reception
       |
       v
    SYSTEM READY

The plan uses E220 Mode 3 as the configuration phase and Mode 0 as normal
communication, with AUX used to determine readiness/busy state before sensitive
radio operations.

41.6 Device identity model
---------------------------
Each ESP32 is expected to maintain at least:

    Device ID
    Device Name
    Role
    E220 radio address
    Firmware version
    Hardware information
    Master ID where applicable

Example:

    Device ID       = NODE-002
    Name            = Furnace-02
    Role            = NODE
    E220 Address    = 0x0102
    Firmware        = v1.0.0
    Master ID       = MASTER-01

The logical device identity and the E220 radio address are separate concepts.
The supplied plan uses a 16-bit radio address scheme, with examples such as:

    MASTER-01 = 0x0001
    MASTER-02 = 0x0002
    NODE-01   = 0x0101
    NODE-02   = 0x0102

41.7 Master responsibilities
-----------------------------
A Master is the coordinator for its configured group of Nodes.
Target responsibilities include:

    Node management
    Telemetry collection
    Command handling
    Status monitoring
    Heartbeat monitoring
    Mesh coordination
    Route information
    Gateway communication
    Master-to-Master communication
    Chat transport
    Configuration
    Diagnostics

The plan explicitly describes the Master as a coordinator, not merely a radio
repeater.

41.8 Node responsibilities
---------------------------
A target Node normally performs:

    Sensor acquisition
    Command reception
    Command execution
    ACK generation
    Response generation
    Telemetry reporting
    Heartbeat reporting
    Alarm / event reporting
    Neighbor/link maintenance
    Mesh forwarding
    Diagnostics reporting

Example Node application data can include temperature, humidity, digital I/O,
machine state, commands and mesh forwarding information.

41.9 Configurable neighbor model
---------------------------------
Each Node has a configured list of allowed neighbor devices.

Example:

    NODE-02
        Master:
            MASTER-01

        Allowed neighbors:
            NODE-01
            NODE-03
            NODE-04
            NODE-07

The neighbor list means allowed communication / forwarding candidates. It does
not mean every neighbor is used at all times.

This distinction is important:

    CONFIGURED NEIGHBORS
        = permitted direct peers / forwarding candidates

    CURRENT ROUTE
        = path dynamically selected using current link information

41.10 Adaptive mesh routing target
----------------------------------
The target ESP32 mesh engine evaluates at least:

    RSSI
    ACK success rate
    Packet loss
    Retry count
    Recent failures
    Last successful communication
    Hop count
    TTL
    Route timeout
    Destination reachability

Example target behavior:

    NODE-02 -> MASTER-01
          |
          X direct path unavailable
          |
          v
    evaluate configured neighbors
          |
          +-- NODE-03 = 95% success
          +-- NODE-04 = 72% success
          +-- NODE-05 = 48% success
          |
          v
    select NODE-03
          |
          v
    NODE-02 -> NODE-03 -> MASTER-01

If NODE-03 later becomes unreliable, the route may move to another configured
candidate such as NODE-04.

41.11 Multi-hop routing
------------------------
The target routing model permits more than one forwarding hop.

Example:

    NODE-02
       |
       v
    NODE-03
       |
       v
    NODE-05
       |
       v
    MASTER-01

Forwarded packets must preserve enough routing information for each hop to
continue delivery while avoiding routing loops.

Expected routing information includes:

    SOURCE
    DESTINATION
    NEXT HOP
    MESSAGE ID
    TTL
    HOP COUNT
    PACKET TYPE
    PAYLOAD

Example:

    SOURCE      = NODE-02
    DESTINATION = MASTER-01
    NEXT_HOP    = NODE-03
    TTL         = 5
    HOP_COUNT   = 1

TTL is the loop-protection mechanism specified in the plan.

41.12 Target communication directions
--------------------------------------
The target firmware supports both uplink and downlink communication.

    MASTER -> NODE
    NODE   -> MASTER

    NODE   -> NODE

    MASTER -> MASTER

    GATEWAY -> MASTER
    MASTER  -> GATEWAY

    GATEWAY -> NODE
    NODE    -> GATEWAY

The Gateway does not need to know the complete physical route to a remote Node;
the mesh routing layer is intended to select and forward the packet.

41.13 Packet and application message classes
---------------------------------------------
The supplied target plan separates application semantics from transport.
Expected application classes include:

    TELEMETRY
    COMMAND
    ACK
    RESPONSE
    STATUS
    HEARTBEAT
    EVENT
    ALARM
    CHAT
    ROUTING
    CONFIGURATION / CONFIG
    DIAGNOSTICS
    DISCOVERY
    ERROR / NACK where required

Every important message is expected to have a unique message/packet ID.

41.14 Command / ACK / RESPONSE separation
------------------------------------------
These three concepts must remain separate.

    COMMAND
        "START PUMP"

    ACK
        "The command packet was received."

    RESPONSE
        "The command was processed and the result is ..."

Example:

    START MOTOR
         |
         v
       ACK
         |
         v
    RESPONSE = MOTOR RUNNING

Failure example:

    START PUMP
         |
         v
       ACK = RECEIVED
         |
         v
    RESPONSE = FAILED
    Reason = Safety interlock active

This separation matches the current Gateway command model, which already tracks
queued/sent/waiting/ACK/executing/response/completed/failed-style lifecycle data,
but the physical ESP32 execution side remains part of the target firmware
workstream.

41.15 Reliable communication target
------------------------------------
The target reliability mechanism uses:

    ACK timeout
    Retry count
    Message ID
    Duplicate protection

Target retry example:

    SEND
      |
      v
    wait for ACK
      |
      +-- no ACK -> retry #1
      |
      +-- no ACK -> retry #2
      |
      +-- no ACK -> retry #3
      |
      v
    FAILED

Route quality should also be affected by communication failures so that a poor
path can be reevaluated and an alternate configured neighbor can be selected.

41.16 Duplicate protection target
---------------------------------
Duplicate protection is critical for machine-control commands.

Example:

    MESSAGE ID = 1050

Node executes:

    START MOTOR

If the ACK is lost, the sender may retry the same message ID. The Node must
recognize that message 1050 was already processed, avoid executing the command
a second time, and handle/resend the appropriate ACK as defined by the protocol.

This target behavior prevents a retransmission from causing a duplicate
physical action.

41.17 Sensor and telemetry target
---------------------------------
A Node can expose multiple sensor parameters, for example:

    Temperature
    Humidity
    Pressure
    Voltage
    Current
    Battery
    Digital input
    Analog input
    Other supported sensors

Each sensor can have:

    Sensor ID
    Name
    Type
    Unit
    Read interval
    Enable/disable state
    Alarm settings

Target data path:

    SENSOR
       |
       v
    NODE DATA PROCESSING
       |
       v
    TELEMETRY PACKET
       |
       +-- direct Master
       |
       +-- mesh route
       |
       v
    MASTER
       |
       v
    GATEWAY
       |
       v
    DATABASE / DASHBOARD

41.18 Heartbeat and status target
---------------------------------
Every ESP32 is expected to report health information.

Possible status information includes:

    ONLINE / OFFLINE
    Last seen
    Uptime
    Firmware version
    Reset reason
    Free heap
    E220 state
    RSSI
    Link quality
    Mesh state
    Wi-Fi state
    Ethernet state
    BLE state
    MQTT / Gateway state
    Sensor state
    Error / fault information

Heartbeat concept:

    NODE -> MASTER: I AM ALIVE

If heartbeat/status updates disappear beyond the configured timeout, the device
can transition from ONLINE to OFFLINE.

The current Gateway node manager already uses a 60-second default offline
timeout when evaluating registered-node status.

41.19 Gateway communication target
-----------------------------------
The planned Gateway is a true two-way application endpoint.

It can eventually:

    Send commands
    Receive command responses
    Receive telemetry
    Receive alarms
    Receive status
    Configure Masters
    Configure Nodes
    Configure mesh
    Handle private chat
    Manage firmware updates

The preferred separation is:

    E220 = LoRa transport for ESP32-to-ESP32 communication
    MQTT = IP/application transport between network-connected devices and the Gateway

The supplied plan describes the Gateway side as capable of using LAN, Wi-Fi,
Ethernet and Internet connectivity while keeping the higher-level application
protocol independent of the underlying IP interface.

41.20 Wi-Fi target behavior
---------------------------
The target ESP32 supports:

    Wi-Fi Station mode for normal operation
    Wi-Fi Access Point mode for commissioning/setup

Example setup flow:

    Phone / PC
       |
       v
    ESP32 temporary AP
       |
       v
    Local Webpage
       |
       v
    Configure Wi-Fi
       |
       v
    Save
       |
       v
    ESP32 reconnects as STA

The target local page is expected to configure items such as:

    SSID
    Password
    DHCP / static IP
    IP address
    Gateway
    DNS
    Gateway/server address
    Server port

41.21 Ethernet target behavior
------------------------------
Ethernet is planned as an optional network interface. On ESP32-WROOM-32 this
requires compatible external Ethernet interface/PHY hardware.

The application layer should not change merely because the network path is:

    Wi-Fi
or:
    Ethernet

41.22 BLE target behavior
-------------------------
BLE is planned primarily for local commissioning and diagnostics:

    Initial setup
    Device identification
    Local diagnostics
    Short-range commissioning

The local Web UI remains the main configuration interface in the supplied plan.

41.23 Local ESP32 webpage target
--------------------------------
The local ESP32 webpage is a commissioning and configuration control center,
not only a status page.

Main planned sections:

    DEVICE
    ROLE
    MASTER
    NODE
    E220
    MESH
    SENSORS
    NETWORK
    GATEWAY / MQTT
    BLE
    ETHERNET
    STATUS
    DIAGNOSTICS
    OTA
    SYSTEM

The configuration flow is:

    Connect
      |
      v
    Change configuration
      |
      v
    Validate
      |
      v
    Save to persistent storage
      |
      +-- Apply immediately where safe
      |
      +-- Restart where required
      |
      v
    Device starts with new configuration

41.24 Target E220 configuration model
-------------------------------------
The supplied ESP32 plan identifies these E220 control signals:

    M0
    M1
    AUX
    RXD
    TXD

Initial settings specified by the plan are:

    UART            = 115200 8N1
    Air rate        = 2.4 kbps initially
    Transmission    = Fixed
    TX power        = 22 dBm initially
    LBT             = ON
    RSSI            = ON
    Sub-packet      = 128 bytes initially

These are initial design values from the supplied plan. Final RF channel and
power must be selected for the actual deployment and legal operating
configuration.

41.25 Target packet journey examples
-------------------------------------
Example A - telemetry:

    SENSOR
      |
      v
    NODE-02
      |
      +-- direct Master works
      |
      +-- otherwise select best configured route
      |
      v
    MASTER-01
      |
      v
    MQTT / LAN / IP
      |
      v
    GATEWAY
      |
      +--> DATABASE
      +--> DASHBOARD

Example B - command:

    DASHBOARD
      |
      v
    GATEWAY SERVER
      |
      v
    MQTT / LAN / IP
      |
      v
    MASTER-01
      |
      v
    MESH ROUTING
      |
      v
    NODE-02
      |
      +--> ACK
      |
      +--> RESPONSE
      |
      v
    MASTER-01
      |
      v
    GATEWAY
      |
      v
    DASHBOARD

Example C - node-to-node:

    NODE-01 -> NODE-03 -> NODE-04

Example D - cross-Master:

    MASTER-01 -> NODE-02 -> NODE-04 -> MASTER-02

Example E - private Chat target architecture:

    OPERATOR
      |
      v
    DASHBOARD
      |
      v
    GATEWAY
      |
      v
    MASTER
      |
      v
    MESH
      |
      v
    NODE

The supplied firmware plan treats Chat as logically separate from machine
commands even when it traverses the ESP32 network.

41.26 Private Chat target semantics
-----------------------------------
Target Chat states are:

    SENT
      |
      v
    DELIVERED
      |
      v
    SEEN

Chat must not be interpreted as a machine-control command merely because both
features use the same network.

Examples:

    "Hello NODE-04"
        = CHAT

    "STOP MOTOR"
        = COMMAND

The current Gateway source is more restrictive: its current chat implementation
stores chat messages in the Gateway/server database and keeps Chat separate from
its LoRa communication manager. The target ESP32 plan describes the broader
future networked Chat transport shown above. These are therefore documented as
CURRENT and TARGET behaviors rather than silently treated as the same feature.

41.27 Target OTA architecture
-----------------------------
OTA is explicitly outside the LoRa data path.

Planned firmware-update methods:

    USB
    Local Wi-Fi
    Wi-Fi hotspot / commissioning network
    Ethernet
    Internet

NOT:

    LoRa / E220 firmware-image transport

Target OTA flow:

    Firmware image
      |
      v
    Inactive OTA application slot
      |
      v
    Validate image
      |
      v
    Verify
      |
      v
    Reboot
      |
      v
    Boot new firmware
      |
      v
    Self-test
      |
      +-- PASS -> accept
      |
      +-- FAIL -> rollback

USB remains a recovery mechanism.

41.28 Target OTA partition plan
--------------------------------
The supplied plans specify the following target partition class:

    APP0    = approximately 1.9 MB
    APP1    = approximately 1.9 MB
    SPIFFS  = approximately 190 KB

The firmware plan specifically calls for a project-local partition definition
so that the actual partition layout is controlled by the project rather than by
a menu label or implicit board default.

The three-part build plan repeats the same partition target throughout the
build.

41.29 OTA safety and security target
------------------------------------
The target production OTA design includes:

    Dual OTA application partitions
    Firmware validation
    Power-loss protection
    Failed-update handling
    Automatic rollback
    Firmware authenticity checks
    Firmware integrity verification
    Signed firmware
    HTTPS for Internet delivery
    Compatibility checks

Target compatibility checks include:

    Hardware version
    Firmware version
    Configuration compatibility
    Gateway compatibility

41.30 OTA management target
----------------------------
The production Gateway is planned to manage:

    Firmware repository
    Release versions
    Device firmware status
    Update history
    Individual updates
    Group updates
    Rollback to previous version
    Update progress

Expected progress states include:

    Downloading
    Installing
    Rebooting
    Success
    Failed
    Rollback

The current Gateway repository already contains a server-side firmware release
and OTA job management layer, including release metadata, SHA-256 calculation,
manifest generation, device firmware state, update jobs and update events. The
physical ESP32 OTA client and full remote transport remain target firmware work.

41.31 Target diagnostics and logging
------------------------------------
Every ESP32 local diagnostics page is expected to expose, where available:

    Boot status
    E220 status
    E220 configuration
    Network status
    MQTT status
    Mesh status
    Neighbor links
    Current route
    Packet count
    ACK count
    Retry count
    Packet failures
    RSSI
    Uptime
    Free heap
    Reset reason
    Firmware version
    OTA status

The Gateway already provides a persistent `logs` table and `/api/logs` endpoint
for server-side activity. The target ESP32 firmware should provide the embedded
side of diagnostics and local logging as part of the later development phases.

41.32 Target security foundation
--------------------------------
Production protection areas specified in the supplied plan include:

    Local web configuration authentication/authorization
    Protection of Wi-Fi credentials
    Protection of MQTT credentials
    Protected command handling
    Protected mesh management
    Secure firmware update path
    Secure MQTT/TLS where used
    HTTPS for Internet OTA
    Device authentication
    Firmware integrity verification
    Firmware authenticity / signed-image verification

The current Gateway repository is a development-oriented local control server,
not a fully hardened public Internet deployment. Production security work must
therefore remain an explicit later phase.


42. PHASED ESP32 BUILD ROADMAP
==============================

42.1 Three-part build strategy plus OTA phase
---------------------------------------------
The supplied planning documents define three principal build stages, with OTA
specified as a later firmware-update phase after the first three stages.

PART 1 - CORE NETWORK

    ESP32 + E220 + standard firmware
    Role Master/Node
    Device ID
    E220 integration
    LoRa packets
    ACK/retry
    Heartbeat
    Device status
    Basic Node <-> Master
    Local Web Configuration
    Wi-Fi basics
    Ethernet basics

Expected result:

    Stable Master + multiple Nodes communicating reliably

PART 2 - MESH & APPLICATIONS

    Configurable neighbors
    Multi-hop routing
    Link-success selection
    Node <-> Node
    Sensor data
    Commands
    Command response
    Alarms
    Master <-> Master
    Private Chat
    Mesh diagnostics

Expected result:

    Complete working LoRa mesh network

PART 3 - GATEWAY & PRODUCTION

    Internet connectivity
    Gateway / MQTT
    Remote monitoring
    Remote control
    Gateway responses
    Node/Master management
    Wi-Fi / Ethernet
    BLE configuration
    Diagnostics / logs
    Security foundation

Expected result:

    Complete remotely manageable system foundation

PART 4 - OTA & FIRMWARE UPDATE

    Firmware release management
    Local update
    USB update / recovery
    Local Wi-Fi update
    Ethernet update
    Internet OTA
    Gateway/server OTA control
    Individual device update
    Group update
    Dual OTA slots
    Validation
    Rollback
    Signed firmware
    Progress/status
    Compatibility checks

Expected result:

    Production firmware lifecycle and recoverable remote updates

42.2 Required development order
--------------------------------
The intended order is deliberately sequential:

    PART 1
      |
      v
    Core ESP32 / network
      |
      v
    PART 2
      |
      v
    Mesh + applications
      |
      v
    PART 3
      |
      v
    Gateway + remote system
      |
      v
    PART 4
      |
      v
    OTA + firmware update

The supplied plan explicitly says OTA should be implemented only after Parts
1-3 are fully working.

42.3 Part 1 acceptance checklist
--------------------------------
Before moving to Part 2, the embedded system should demonstrate:

    Same firmware boots as Master and Node
    Device identity persists
    Role persists
    E220 UART works
    E220 configuration can be read/applied
    Master <-> Node packets work
    ACK works
    Retry works
    Duplicate protection works
    Heartbeat works
    Online/offline status works
    Local configuration page works
    Wi-Fi setup works
    Ethernet integration path is defined where hardware exists

42.4 Part 2 acceptance checklist
--------------------------------
Before moving to Part 3, the embedded network should demonstrate:

    Configurable neighbor lists
    Node <-> Node delivery
    Direct-route selection
    Relay selection
    Multi-hop forwarding
    TTL loop protection
    Link-quality tracking
    Route adaptation
    Telemetry over mesh
    Command over mesh
    ACK / response over mesh
    Alarm/event delivery
    Multiple Masters
    Master <-> Master communication
    Private Chat semantics separated from machine commands
    Mesh diagnostics

42.5 Part 3 acceptance checklist
--------------------------------
Before treating the system as remotely manageable:

    Gateway two-way data path works
    MQTT connectivity works
    Gateway <-> Master messages work
    Gateway <-> Node requests work through Master/mesh
    Telemetry reaches Gateway
    Command ACK/response reaches Gateway
    Node status reaches Gateway
    Remote configuration path works
    BLE commissioning works
    Logs/diagnostics are visible
    Authentication/authorization foundation is applied
    MQTT security is configured where used
    Internet boundary is clearly separated from the LoRa transport

42.6 Part 4 acceptance checklist
--------------------------------
Before production OTA is considered complete:

    Dual OTA slots are verified
    Local update works
    USB recovery works
    Wi-Fi update works
    Ethernet update works where hardware supports it
    Internet OTA uses HTTPS
    Firmware image validation works
    Integrity/authenticity checks work
    New image boots correctly
    Self-test is executed
    Rollback works after failed validation
    Firmware version/state is reported to Gateway
    Update progress is visible
    Update history is retained
    Hardware/configuration compatibility is enforced


43. CURRENT REPOSITORY VS TARGET EMBEDDED PLAN
===============================================

The following distinctions are important when extending the project.

43.1 Gateway pieces already present in the repository
-----------------------------------------------------
The current GitHub repository contains server-side implementations for:

    Node management
    Sensor parameter management
    Telemetry history and statistics
    Command lifecycle management
    Command ACK/response processing
    Packet creation / validation / CRC
    Transport-independent communication queues
    Mesh topology and link data
    Route selection
    Firmware releases
    OTA device state and jobs
    Logs
    Private chat persistence
    Browser dashboard
    Socket.IO live events
    Node simulator programs

43.2 Physical ESP32 work still represented as target architecture
-----------------------------------------------------------------
The supplied embedded plan requires the future ESP32 firmware to implement the
physical side of the design, including:

    Real E220 UART driver
    E220 M0/M1/AUX control
    Persistent embedded configuration
    Master/Node runtime roles
    Embedded neighbor management
    Real multi-hop forwarding
    Physical route measurement
    Embedded duplicate-protection state
    Real sensor acquisition
    Embedded command execution
    Real Gateway/MQTT client
    BLE commissioning
    Embedded OTA / boot validation / rollback
    Embedded security mechanisms

These should not be marked as complete merely because corresponding server-side
management code already exists.

43.3 Important current-to-target gaps observed from source
-----------------------------------------------------------
The repository source and supplied plans imply several clear integration steps:

    1. E220 physical transport
       Current communication_manager.py is transport-independent and provides a
       send callback / queue abstraction. The physical E220 UART layer is not
       directly implemented by that Python server module.

    2. Embedded multi-hop implementation
       The current server routing_manager.py selects a direct route or a relay
       candidate using a second link. The supplied embedded plan goes further
       and calls for configurable multi-hop routing with TTL/hop-count handling.

    3. Gateway <-> ESP32 MQTT transport
       The target architecture requires MQTT/IP connectivity from the Master or
       another network-connected ESP32 to the Gateway. The current repository's
       communication manager is transport-independent; a real MQTT transport
       adapter is an integration task for the embedded side.

    4. Physical sensor acquisition
       The current Gateway can define/store sensor parameters and telemetry, but
       the actual ESP32 sensor drivers and physical I/O acquisition belong in
       the future standard firmware.

    5. Physical OTA client
       The current Gateway manages releases and OTA jobs server-side. The ESP32
       client still needs the local/network update implementation, boot
       validation and rollback behavior described by the plan.

    6. Production security
       The current local development Gateway is not equivalent to a hardened
       Internet deployment. Authentication, authorization, device identity,
       secure MQTT and signed-image enforcement remain explicit production tasks.

43.4 Do not mix the two communication layers
---------------------------------------------
The target design has two fundamentally different transport levels:

    E220 / LoRa
        Device-to-device radio transport among ESP32 nodes/Masters.

    MQTT / LAN / Wi-Fi / Ethernet / Internet
        IP-side Gateway/application transport.

The application packet model should stay transport-independent so that the same
logical command, telemetry or status message can travel through different
network adapters without changing its meaning.

Firmware images are intentionally excluded from the E220 path.


44. IMPLEMENTATION PRINCIPLES FOR FUTURE DEVELOPMENT
=====================================================

When extending the repository, preserve these architectural rules from the
supplied plans:

    RULE 1
    One standard ESP32 firmware image supports both MASTER and NODE roles.

    RULE 2
    Role is persistent configuration, not a separate firmware binary.

    RULE 3
    Master ownership defines management responsibility, not a hard radio
    communication boundary.

    RULE 4
    Neighbor configuration defines allowed communication / forwarding peers.

    RULE 5
    Current routes are selected dynamically using measured link information.

    RULE 6
    Direct delivery should be preferred when healthy; otherwise the routing
    engine should use the configured mesh path.

    RULE 7
    Every forwarded packet must preserve the identity needed for routing and
    duplicate protection.

    RULE 8
    ACK means receipt of a command packet; RESPONSE means execution/result.

    RULE 9
    A duplicate command ID must not cause a duplicate physical action.

    RULE 10
    Heartbeat/status must be independent enough to detect an unavailable Node.

    RULE 11
    Telemetry, commands, events and alarms must work in both direct and mesh
    communication paths where supported.

    RULE 12
    Private Chat must remain logically separate from machine-control commands.

    RULE 13
    Gateway communication is two-way.

    RULE 14
    E220 remains the LoRa transport; MQTT/IP remains the Gateway network
    transport.

    RULE 15
    OTA firmware images must not be transported over LoRa.

    RULE 16
    USB remains an available recovery path.

    RULE 17
    OTA must use validation, safe boot handling and rollback before being called
    production-ready.

    RULE 18
    Production firmware update must verify compatibility, integrity and
    authenticity.


45. TARGET FINAL SYSTEM SUMMARY
================================

The intended final system can be summarized as:

    ┌─────────────────────────────────────────────────────────────┐
    │                     GATEWAY / SERVER                       │
    │                                                             │
    │  Web Dashboard  Node Mgmt  Sensors  Commands  Logs  OTA   │
    │  Telemetry      Mesh Mgmt  Chat      Status    MQTT       │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                            MQTT / LAN / IP
                                   │
                  ┌────────────────┴────────────────┐
                  │                                 │
             MASTER-01                          MASTER-02
                  │                                 │
        ┌─────────┼─────────┐             ┌────────┼─────────┐
        │         │         │             │        │         │
      NODE-01  NODE-02  NODE-03         NODE-04 NODE-05 NODE-06
        │         │         │             │        │         │
        └─────────┴──── configurable Node-to-Node mesh ────────┘

The embedded device itself follows:

    STANDARD ESP32 FIRMWARE
              |
       +------+------+------+
       |      |      |      |
      ROLE   E220 NETWORK  WEB/OTA
       |      |      |      |
    MASTER/   |   Wi-Fi    Config
      NODE    |   Ethernet  Status
              |   BLE       OTA
              |
          MESH ENGINE
              |
       PACKET / DATA ENGINE
              |
      +-------+-------+-------+
      |       |       |       |
   TELEMETRY COMMAND  CHAT  STATUS
              |
          ACK/RESPONSE

The target end state is a remotely manageable ESP32 + E220 LoRa mesh system with
one standard firmware, configurable Master/Node roles, dynamic mesh routing,
reliable ACK/retry delivery, sensor telemetry, command execution, alarms/events,
Gateway/MQTT connectivity, private Chat, local commissioning, diagnostics and
recoverable secure OTA updates.


46. SOURCE DOCUMENTS USED FOR THIS README UPDATE
=================================================

This README update incorporates the following project planning documents
supplied with the request:

    esp32 buiding plan 3s.txt
        Three-stage build strategy plus partition target.

    esp32 part1,2,3 vise plane.txt
        Part-by-part function list, final development order and OTA scope.

    workflow esp32.txt
        End-to-end architecture and detailed communication/workflow model.

    ESP32_Firmware_Complete_Functional_Plan(1).txt
        ESP32-WROOM-32 + E220-900T22D functional plan, firmware roles,
        network behavior, E220 settings, mesh, Gateway, local webpage and OTA.

The supplied documents describe the TARGET embedded architecture. The CURRENT
Gateway implementation described earlier in this README remains the authority
for what is actually present in the GitHub server repository.


47. DOCUMENTATION STATUS
========================

Current Gateway/server implementation:
    Documented from repository source code.

Target ESP32 firmware architecture:
    Documented from the supplied functional plans.

Physical ESP32/E220 production firmware completion:
    NOT inferred from the presence of server-side management code.

Recommended next engineering sequence:

    1. Implement and validate Part 1 on real ESP32-WROOM-32 + E220 hardware.
    2. Add Part 2 mesh/application behavior after Part 1 acceptance.
    3. Integrate Part 3 Gateway/MQTT/remote-management behavior.
    4. Implement Part 4 OTA only after Parts 1-3 are validated.


END OF UPDATED README


END OF README
============================================================
