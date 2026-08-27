"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("system-form");
    if (!form) return;

    const nodeSelect = document.getElementById("system-node");
    let nodes = [];
    let currentNode = "";

    init();

    async function init() {
        bindEvents();
        await loadNodes();
    }

    function bindEvents() {
        nodeSelect?.addEventListener("change", async () => {
            currentNode = nodeSelect.value;
            await loadSystem();
        });

        document.getElementById("system-save")?.addEventListener("click", saveSystem);
        document.getElementById("system-reset")?.addEventListener("click", resetSystem);
        document.getElementById("system-reboot")?.addEventListener("click", () =>
            confirmAction("Reboot Gateway", "Are you sure you want to reboot the gateway?", rebootGateway)
        );
        document.getElementById("system-factory-reset")?.addEventListener("click", () =>
            confirmAction("Factory Reset", "This resets saved gateway/node configuration to defaults. This action cannot be undone.", factoryReset)
        );
    }

    async function loadNodes() {
        try {
            const response = await gateway.get("/api/nodes");
            nodes = Array.isArray(response) ? response : (response.nodes || []);

            if (!nodes.length) {
                nodeSelect.innerHTML = `<option value="">No Nodes Configured</option>`;
                setFormDisabled(true);
                return;
            }

            nodeSelect.innerHTML = `<option value="">Select Node</option>` + nodes.map(node =>
                `<option value="${gateway.escape(node.node_id)}">${gateway.escape(node.name || node.node_id)}</option>`
            ).join("");

            currentNode = nodes[0].node_id;
            nodeSelect.value = currentNode;
            setFormDisabled(false);
            await loadSystem();
        } catch (error) {
            console.error("System node loading error:", error);
            gateway.toast(error.message || "Unable to load nodes", "error");
        }
    }

    async function loadSystem() {
        if (!currentNode) return;
        const node = nodes.find(item => item.node_id === currentNode);
        if (!node) return;

        setValue("system-node-name", node.name);
        setValue("system-node-id", node.node_id);
        setValue("system-address", node.node_address);
        setValue("system-mcu", node.mcu_model || node.mcu_family);
        setValue("system-hardware", node.hardware_revision);
        setValue("system-firmware", node.firmware_version);

        try {
            const response = await gateway.get(`/api/nodes/${encodeURIComponent(currentNode)}/config`);
            const config = response.config || {};
            setValue("system-timezone", config.time?.timezone || "Asia/Kolkata");
            setChecked("system-time-sync", config.time?.sync_enabled ?? true);
            setValue("system-watchdog", config.watchdog?.timeout_s ?? 60);
        } catch (error) {
            console.error("System configuration load error:", error);
            setValue("system-timezone", "Asia/Kolkata");
            setChecked("system-time-sync", true);
            setValue("system-watchdog", 60);
        }
    }

    async function saveSystem() {
        if (!currentNode) {
            gateway.toast("Select a node first", "error");
            return;
        }

        const node = nodes.find(item => item.node_id === currentNode);
        if (!node) return;

        try {
            await gateway.put(`/api/nodes/${encodeURIComponent(currentNode)}`, {
                name: getValue("system-node-name"),
                mcu_family: node.mcu_family || "",
                mcu_model: node.mcu_model || "",
                hardware_revision: getValue("system-hardware"),
                firmware_version: getValue("system-firmware") || node.firmware_version || "v1.0.0",
                communication_type: node.communication_type,
                communication_config: node.communication_config || {},
                node_address: getValue("system-address")
            });

            const configResponse = await gateway.get(`/api/nodes/${encodeURIComponent(currentNode)}/config`);
            const config = configResponse.config || {};
            config.time = {
                ...(config.time || {}),
                timezone: getValue("system-timezone") || "Asia/Kolkata",
                sync_enabled: getChecked("system-time-sync", true)
            };
            config.watchdog = {
                ...(config.watchdog || {}),
                enabled: true,
                timeout_s: Number(getValue("system-watchdog")) || 60
            };

            await gateway.put(`/api/nodes/${encodeURIComponent(currentNode)}/config`, { config });
            gateway.toast("System configuration saved", "success");
            await loadNodes();
        } catch (error) {
            console.error("System save error:", error);
            gateway.toast(error.message || "Unable to save system configuration", "error");
        }
    }

    async function resetSystem() {
        if (!currentNode) {
            gateway.toast("Select a node first", "error");
            return;
        }

        try {
            const response = await gateway.post(`/api/nodes/${encodeURIComponent(currentNode)}/config/reset`);
            const config = response.config || {};
            setValue("system-timezone", config.time?.timezone || "Asia/Kolkata");
            setChecked("system-time-sync", config.time?.sync_enabled ?? true);
            setValue("system-watchdog", config.watchdog?.timeout_s ?? 60);
            gateway.toast("System defaults restored", "success");
        } catch (error) {
            gateway.toast(error.message || "Unable to reset defaults", "error");
        }
    }

    async function rebootGateway() {
        try {
            await gateway.post("/api/system/reboot", {});
            gateway.toast("Gateway reboot request accepted", "success");
        } catch (error) {
            gateway.toast(error.message || "Reboot request failed", "error");
        }
    }

    async function factoryReset() {
        try {
            await gateway.post("/api/system/factory-reset", { confirm: true });
            gateway.toast("Gateway configuration reset to defaults", "success");
            await loadNodes();
        } catch (error) {
            gateway.toast(error.message || "Factory reset failed", "error");
        }
    }

    function confirmAction(title, message, action) {
        const root = document.getElementById("system-modal-root");
        if (!root) return;
        root.innerHTML = `
            <div class="modal-overlay" id="system-confirm-modal">
                <div class="modal">
                    <div class="modal-icon">!</div>
                    <h2>${gateway.escape(title)}</h2>
                    <p>${gateway.escape(message)}</p>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" id="system-confirm-cancel">Cancel</button>
                        <button type="button" class="btn btn-danger" id="system-confirm-ok">Confirm</button>
                    </div>
                </div>
            </div>`;
        document.getElementById("system-confirm-cancel")?.addEventListener("click", closeModal);
        document.getElementById("system-confirm-ok")?.addEventListener("click", async () => {
            closeModal();
            await action();
        });
    }

    function closeModal() {
        const root = document.getElementById("system-modal-root");
        if (root) root.innerHTML = "";
    }

    function setFormDisabled(disabled) {
        form.querySelectorAll("input, select, button").forEach(el => {
            if (el.id === "system-node") return;
            el.disabled = disabled;
        });
    }

    function setValue(id, value) {
        const el = document.getElementById(id);
        if (el) el.value = value ?? "";
    }

    function getValue(id) {
        return (document.getElementById(id)?.value || "").trim();
    }

    function setChecked(id, value) {
        const el = document.getElementById(id);
        if (el) el.checked = Boolean(value);
    }

    function getChecked(id, fallback = false) {
        const el = document.getElementById(id);
        return el ? el.checked : fallback;
    }
});
