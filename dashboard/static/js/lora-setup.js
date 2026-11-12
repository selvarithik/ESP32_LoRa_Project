"use strict";
const radioMessages = {
    SETTINGS_READ_TIMEOUT: "The E220 did not answer the settings request. Check module power, common ground, UART wiring and AUX.",
    SETTINGS_PARTIAL_RESPONSE: "The E220 reply was incomplete. Check the UART connections and module power.",
    INVALID_PUBLIC_SETTINGS: "The E220 replied with invalid settings data. Check the wiring and inspect again.",
    SETTINGS_MISMATCH_NO_RF: "Saved firmware settings differ from the E220 registers. Compare the channel, air rate, power and RSSI setting before activation.",
    UNVERIFIED_RADIO_PINS: "The configured UART and control pins do not match this board’s supported wiring.",
    MESH_CREDENTIAL_REQUIRED: "Provision the shared mesh credential over USB before enabling radio traffic.",
    MODE_RESTORE_TIMEOUT: "AUX did not become ready after the mode change. Check AUX, M0, M1 and power.",
    AUX_BUSY_TIMEOUT: "The radio stayed busy too long to send. Check AUX and the module power supply.",
    REGISTER_WRITE_REJECTED: "The E220 did not confirm the register write. Inspect the module before trying again.",
    MESSAGE_TX_EXPIRED: "The radio did not send the message before its deadline.",
    SLEEP_MODE_TIMEOUT: "The radio did not confirm the sleep-mode change.",
    RADIO_BUSY_OR_UNAVAILABLE: "The radio is busy or unavailable. Refresh its status before trying again.",
    RADIO_UPDATE_REQUIRES_DISABLED_LOCAL_COMMISSIONING: "Disable the radio and register writes on the ESP32 before saving setup from Gateway.",
    REVISION_CONFLICT: "The saved settings changed. Read the current setup before saving again."
};

function radioFault(code) {
    if (!code || ["NONE", "DISABLED", "INSPECTING", "PROBE_COMPLETE_NO_RF"].includes(code)) return "";
    if (String(code).includes("ACK_TIMEOUT")) return "The device did not acknowledge the command before the deadline. Check the Gateway connection and retry.";
    return radioMessages[code] || `The device reported ${code}. Refresh status and check its connection.`;
}

function renderRadioReport(target, radio, routes) {
    target.replaceChildren();
    if (radio) {
        const status = radio.rf_receive_state === "RECEIVING" ? "Receiving authenticated LoRa packets"
            : radio.rf_receive_state === "STALE" ? "Last radio reception is stale"
            : radio.state === "INSPECTING" ? "Reading E220 registers"
            : radio.state === "SLEEPING" ? "Radio sleeping"
            : radio.state === "READY_LINK_UNVERIFIED" ? "Radio ready, waiting for a peer packet"
            : radio.error === "PROBE_COMPLETE_NO_RF" ? "E220 detected over UART, RF disabled"
            : radio.state === "DISABLED" ? "Radio disabled"
            : radio.state === "ERROR" ? "Radio fault" : "Radio status unavailable";
        const o = radio.observed;
        const rssi = Number.isFinite(radio.rssi_dbm) ? `${radio.rssi_dbm} dBm${radio.rf_receive_state === "RECEIVING" ? "" : " (last sample)"}`
            : o?.rssi_enabled === false ? "RSSI is disabled in the module" : "Waiting for a valid packet with RSSI";
        const details = [
            ["Connection", status], ["Module readback", radio.public_settings_read ? "Registers read successfully" : "No valid register readback"],
            ["Received signal (RSSI)", rssi], ["Last radio peer", radio.last_rf_peer],
            ["Last received", Number.isFinite(radio.last_rf_age_ms) ? `${Math.floor(radio.last_rf_age_ms / 1000)} s before this report` : null],
            ["AUX pin", radio.pin_levels?.aux_high == null ? null : radio.pin_levels.aux_high ? "High" : "Low"],
            ["Channel", o && Number.isInteger(o.channel) ? `${o.channel} · ${(850.125 + o.channel).toFixed(3)} MHz` : null],
            ["Air rate code", o?.air_rate_code], ["Transmit power", o ? `${o.power_dbm} dBm` : null],
            ["UART", o ? `${o.baud} baud` : null], ["Subpacket size", o ? `${o.subpacket_bytes} bytes` : null],
            ["Addressing", o ? o.fixed_mode ? "Fixed" : "Transparent" : null], ["Work mode", radio.work_mode],
            ["Received messages", radio.rx_messages], ["Timeouts", radio.timeouts], ["Authentication failures", radio.auth_failures],
            ["Fault", radioFault(radio.error) || null]
        ];
        const list = document.createElement("dl");
        for (const [label, value] of details) {
            if (value == null) continue;
            const name = document.createElement("dt"); name.textContent = label;
            const item = document.createElement("dd"); item.textContent = value;
            list.append(name, item);
        }
        target.append(list);
    }
    if (Array.isArray(routes)) {
        const heading = document.createElement("h3"); heading.textContent = "Reported routes";
        const list = document.createElement("ul");
        for (const route of routes) {
            const item = document.createElement("li");
            const hops = route.hop_count ?? route.hops;
            item.textContent = `${route.destination || "Unknown destination"} via ${route.next_hop || "unknown next hop"}${Number.isFinite(hops) ? ` (${hops} hop${hops === 1 ? "" : "s"})` : ""}`;
            list.append(item);
        }
        if (!routes.length) { const item = document.createElement("li"); item.textContent = "No route has been learned."; list.append(item); }
        target.append(heading, list);
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    const device = document.getElementById("lora-device");
    if (!device) return;
    const form = document.getElementById("lora-setup");
    const feedback = document.getElementById("lora-feedback");
    const output = document.getElementById("lora-result");
    const buttons = [...document.querySelectorAll("[data-lora-command]"), form.querySelector("button")];
    const fields = [
        ["lora_address_high", "Address high byte", 0, 255],
        ["lora_address_low", "Address low byte", 0, 255],
        ["lora_channel", "Channel", 0, 80],
        ["lora_air_rate", "Air rate code", 0, 7],
        ["lora_baud", "UART baud", [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]],
        ["lora_tx_power", "Transmit power (dBm)", [10, 13, 17, 22]],
        ["lora_packet_bytes", "Subpacket size (bytes)", [64, 128, 200]],
        ["lora_wor_cycle_ms", "Wake-on-radio cycle (ms)", [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]],
        ["lora_work_mode", "Work mode", ["NORMAL", "WOR_TX", "WOR_RX"]],
        ["lora_fixed_mode", "Fixed addressing"],
        ["lora_rssi", "Report received signal strength (RSSI)"],
        ["lora_lbt", "Listen before talk"]
    ];
    let saved = null;
    let busy = false;

    function showSetup(config) {
        saved = null;
        form.hidden = true;
        if (!Number.isInteger(config?.configuration_revision) || fields.some(([key]) => config[key] == null)) {
            feedback.textContent = "This firmware did not report all saved radio fields. Use the ESP32 LoRa page.";
            return;
        }
        if (config.lora_enabled !== false || config.lora_apply_settings !== false) {
            feedback.textContent = "Disable the radio and register writes on the ESP32 before staging setup from Gateway.";
            return;
        }
        const container = document.getElementById("lora-fields");
        container.replaceChildren();
        for (const [key, title, options, max] of fields) {
            const label = document.createElement("label");
            label.textContent = title;
            const input = document.createElement(Array.isArray(options) ? "select" : "input");
            input.name = key;
            input.className = "input";
            if (Array.isArray(options)) {
                for (const value of options) input.add(new Option(String(value), String(value)));
            } else if (options === undefined) {
                input.type = "checkbox";
                input.checked = config[key];
            } else {
                input.type = "number";
                input.min = options;
                input.max = max;
                input.required = true;
            }
            if (input.type !== "checkbox") input.value = String(config[key]);
            label.append(input);
            container.append(label);
        }
        saved = config;
        form.hidden = false;
    }

    async function command(kind, payload = {}) {
        if (!device.value || busy) return;
        busy = true;
        device.disabled = true;
        buttons.forEach(button => { button.disabled = true; });
        feedback.textContent = "Submitting " + kind;
        output.textContent = "";
        try {
            const {command: queued} = await gateway.post("/api/v1/commands", {node_id: device.value, command_type: kind, payload});
            const deadline = Date.now() + 125000;
            while (Date.now() < deadline) {
                const {command: current} = await gateway.get("/api/commands/" + encodeURIComponent(queued.command_id));
                feedback.textContent = `${kind} · ${current.state} · ${queued.command_id}`;
                if (["COMPLETED", "FAILED", "TIMEOUT", "CANCELLED"].includes(current.state)) {
                    const result = current.result || {};
                    if (kind === "RADIO_INSPECT" || kind === "GET_RADIO_STATUS") {
                        renderRadioReport(output, result);
                        if (!result.state) output.textContent = radioFault(current.error || result.error) || "No radio report was returned.";
                    } else if (kind === "GET_ROUTE_INFO" && current.state === "COMPLETED") {
                        renderRadioReport(output, null, result.routes || []);
                    } else if (current.state !== "COMPLETED") {
                        output.textContent = radioFault(current.error || result.error) || "The device did not complete this request.";
                    } else {
                        output.textContent = kind === "CONFIG_UPDATE" ? "Settings saved on the device for local activation." : "Saved setup read from the device.";
                    }
                    if (result.gateway_verified_transport) {
                        const path = document.createElement("p");
                        path.textContent = `Gateway connection used for this response: ${result.gateway_verified_transport === "IP" ? "local HTTP" : result.gateway_verified_transport}`;
                        output.append(path);
                    }
                    document.getElementById("lora-result-panel").open = true;
                    if (current.state === "COMPLETED" && kind === "GET_CONFIG") showSetup(current.result);
                    if (current.state === "COMPLETED" && kind === "CONFIG_UPDATE") feedback.textContent += " · Saved for local commissioning";
                    return;
                }
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            feedback.textContent = `No final response in this view. Check Command Center for ${queued.command_id}.`;
        } catch (error) {
            feedback.textContent = error.message;
        } finally {
            busy = false;
            device.disabled = false;
            buttons.forEach(button => { button.disabled = false; });
        }
    }

    device.onchange = () => { saved = null; form.hidden = true; output.textContent = ""; feedback.textContent = ""; };
    for (const button of document.querySelectorAll("[data-lora-command]")) {
        button.onclick = () => command(button.dataset.loraCommand);
    }
    form.onsubmit = event => {
        event.preventDefault();
        if (!saved || busy) return;
        const changes = {};
        for (const [key] of fields) {
            const input = form.elements[key];
            const value = input.type === "checkbox" ? input.checked : typeof saved[key] === "number" ? Number(input.value) : input.value;
            if (value !== saved[key]) changes[key] = value;
        }
        if (!Object.keys(changes).length) { feedback.textContent = "Radio settings already match."; return; }
        const revision = saved.configuration_revision;
        saved = null;
        form.hidden = true;
        command("CONFIG_UPDATE", {...changes, expected_revision: revision});
    };
    try {
        const {nodes} = await gateway.get("/api/device-controls");
        for (const node of nodes) device.add(new Option(`${node.name || node.node_id} · ${node.device_role}`, node.node_id));
        if (!device.options.length) feedback.textContent = "No enrolled devices available.";
    } catch (error) {
        feedback.textContent = error.message;
    }
});
