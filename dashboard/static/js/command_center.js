/* ============================================================
   COMMAND CENTER JAVASCRIPT — PHASE 3
   Real-time command management, ACK & response analytics
   ============================================================ */

"use strict";

(() => {
    // Application State
    const state = {
        nodes: [],
        selectedNodeId: null,
        activeCommand: null,
        commandHistory: [],
        selectedCommandId: null,
        historyFilter: "ALL",
        socket: null,
        socketConnected: false,
        pollingTimer: null
    };

    // DOM Elements Cache
    const el = {};

    /* ============================================================
       INITIALIZATION
       ============================================================ */
    document.addEventListener("DOMContentLoaded", () => {
        cacheDOMElements();
        bindEvents();
        initSocketIO();
        loadNodes();
        startPolling();
    });

    function cacheDOMElements() {
        // Toolbar
        el.topTargetBadge = document.getElementById("top-target-badge");
        el.socketStatusPill = document.getElementById("socket-status-pill");
        el.socketStatusText = document.getElementById("socket-status-text");
        el.cmdRefreshBtn = document.getElementById("cmd-refresh-btn");

        // Section 1: Nodes
        el.nodeCountBadge = document.getElementById("node-count-badge");
        el.nodeSearchInput = document.getElementById("node-search-input");
        el.nodeListContainer = document.getElementById("node-list-container");

        // Section 2: Device Status
        el.deviceStatusIndicator = document.getElementById("device-status-indicator");
        el.devNodeId = document.getElementById("dev-node-id");
        el.devStatus = document.getElementById("dev-status");
        el.devLastSeen = document.getElementById("dev-last-seen");
        el.devMcu = document.getElementById("dev-mcu");
        el.devHwRev = document.getElementById("dev-hw-rev");
        el.devFw = document.getElementById("dev-fw");
        el.devComm = document.getElementById("dev-comm");
        el.devLastCmdState = document.getElementById("dev-last-cmd-state");

        // Section 3: Banner
        el.bannerAvatar = document.getElementById("banner-avatar");
        el.bannerNodeName = document.getElementById("banner-node-name");
        el.bannerNodeId = document.getElementById("banner-node-id");
        el.bannerConnectionBadge = document.getElementById("banner-connection-badge");
        el.bannerNodeDetails = document.getElementById("banner-node-details");
        el.bannerActiveCmd = document.getElementById("banner-active-cmd");
        el.bannerCmdState = document.getElementById("banner-cmd-state");
        el.bannerLastResp = document.getElementById("banner-last-resp");

        // Section 4: Server Command
        el.cmdHeaderId = document.getElementById("cmd-header-id");
        el.activeCmdStatePill = document.getElementById("active-cmd-state-pill");
        el.btnCancelCmd = document.getElementById("btn-cancel-cmd");
        el.btnRetryCmd = document.getElementById("btn-retry-cmd");
        el.metaCmdType = document.getElementById("meta-cmd-type");
        el.metaCmdTarget = document.getElementById("meta-cmd-target");
        el.metaCmdPriority = document.getElementById("meta-cmd-priority");
        el.metaCmdRetries = document.getElementById("meta-cmd-retries");
        el.metaCmdCreated = document.getElementById("meta-cmd-created");
        el.metaCmdTimeout = document.getElementById("meta-cmd-timeout");

        // Section 5: Response & ACK
        el.btnCopyResult = document.getElementById("btn-copy-result");
        el.ackBadgeStatus = document.getElementById("ack-badge-status");
        el.ackMessageText = document.getElementById("ack-message-text");
        el.ackTimestampText = document.getElementById("ack-timestamp-text");
        el.respBadgeStatus = document.getElementById("resp-badge-status");
        el.respSummaryText = document.getElementById("resp-summary-text");
        el.respTimestampText = document.getElementById("resp-timestamp-text");
        el.cmdErrorBanner = document.getElementById("cmd-error-banner");
        el.cmdErrorMessage = document.getElementById("cmd-error-message");
        el.responseDataJson = document.getElementById("response-data-json");

        // Section 6: History
        el.historyTargetLabel = document.getElementById("history-target-label");
        el.historyFilterSelect = document.getElementById("history-filter-select");
        el.btnViewTimeline = document.getElementById("btn-view-timeline");
        el.historyListContainer = document.getElementById("history-list-container");

        // Section 7: Configuration
        el.cmdTypeSelect = document.getElementById("cmd-type-select");
        el.cmdPrioritySelect = document.getElementById("cmd-priority-select");
        el.cmdTimeoutInput = document.getElementById("cmd-timeout-input");
        el.cmdRetriesInput = document.getElementById("cmd-retries-input");

        // Specific Params
        el.paramPingMsg = document.getElementById("param-ping-msg");
        el.paramScanBand = document.getElementById("param-scan-band");
        el.paramScanLimit = document.getElementById("param-scan-limit");
        el.paramWifiSsid = document.getElementById("param-wifi-ssid");
        el.paramWifiPass = document.getElementById("param-wifi-pass");
        el.paramWifiSave = document.getElementById("param-wifi-save");
        el.paramRebootDelay = document.getElementById("param-reboot-delay");
        el.paramRebootReason = document.getElementById("param-reboot-reason");
        el.paramConfigSection = document.getElementById("param-config-section");
        el.paramIntervalMs = document.getElementById("param-interval-ms");
        el.paramCustomName = document.getElementById("param-custom-name");
        el.paramCustomJson = document.getElementById("param-custom-json");

        // Section 8: Send Button
        el.btnSendCommand = document.getElementById("btn-send-command");
        el.sendBtnSubtext = document.getElementById("send-btn-subtext");

        // Timeline Modal
        el.timelineModalOverlay = document.getElementById("timeline-modal-overlay");
        el.modalCmdId = document.getElementById("modal-cmd-id");
        el.btnCloseTimelineModal = document.getElementById("btn-close-timeline-modal");
        el.timelineEventsList = document.getElementById("timeline-events-list");
    }

    /* ============================================================
       EVENT BINDINGS
       ============================================================ */
    function bindEvents() {
        // Refresh
        el.cmdRefreshBtn?.addEventListener("click", () => {
            loadNodes();
            if (state.selectedNodeId) {
                loadCommandHistory(state.selectedNodeId);
            }
            if (window.gateway?.toast) {
                gateway.toast("Command Center refreshed", "info");
            }
        });

        // Search Nodes
        el.nodeSearchInput?.addEventListener("input", renderNodes);

        // Command Type Change (switch dynamic form pane)
        el.cmdTypeSelect?.addEventListener("change", (e) => {
            switchParamPane(e.target.value);
        });

        // Send Command
        el.btnSendCommand?.addEventListener("click", handleSendCommand);

        // Cancel Command
        el.btnCancelCmd?.addEventListener("click", handleCancelCommand);

        // Retry Command
        el.btnRetryCmd?.addEventListener("click", handleRetryCommand);

        // Filter History
        el.historyFilterSelect?.addEventListener("change", (e) => {
            state.historyFilter = e.target.value;
            renderHistory();
        });

        // Copy Result
        el.btnCopyResult?.addEventListener("click", copyResultToClipboard);

        // View Timeline
        el.btnViewTimeline?.addEventListener("click", () => {
            if (state.activeCommand?.command_id) {
                openTimelineModal(state.activeCommand.command_id);
            } else {
                if (window.gateway?.toast) gateway.toast("Please select a command first", "warning");
            }
        });

        // Close Timeline Modal
        el.btnCloseTimelineModal?.addEventListener("click", closeTimelineModal);
        el.timelineModalOverlay?.addEventListener("click", (e) => {
            if (e.target === el.timelineModalOverlay) closeTimelineModal();
        });
    }

    function switchParamPane(cmdType) {
        document.querySelectorAll(".param-pane").forEach(pane => {
            pane.classList.remove("active");
        });
        const activePane = document.getElementById(`pane-${cmdType}`);
        if (activePane) {
            activePane.classList.add("active");
        } else {
            // Default to custom or empty if not matched
            document.getElementById("pane-CUSTOM")?.classList.add("active");
        }
    }

    /* ============================================================
       NODE MANAGEMENT & SELECTION (SECTION 1, 2, 3)
       ============================================================ */
    async function loadNodes() {
        try {
            const data = await gateway.get("/api/nodes");
            state.nodes = Array.isArray(data) ? data : (data?.nodes || []);
            renderNodes();

            // Auto-select first node or preserve selection
            if (state.nodes.length > 0) {
                const exists = state.nodes.some(n => n.node_id === state.selectedNodeId);
                if (!exists || !state.selectedNodeId) {
                    selectNode(state.nodes[0].node_id);
                } else {
                    updateSelectedNodeUI();
                }
            } else {
                state.selectedNodeId = null;
                updateSelectedNodeUI();
            }
        } catch (err) {
            console.error("Failed to load nodes:", err);
            el.nodeListContainer.innerHTML = `<div class="cmd-empty-state"><p>Error loading nodes: ${escapeHtml(err.message)}</p></div>`;
        }
    }

    function renderNodes() {
        const query = (el.nodeSearchInput?.value || "").toLowerCase().trim();
        const filtered = state.nodes.filter(node => {
            const id = String(node.node_id || "").toLowerCase();
            const name = String(node.name || "").toLowerCase();
            return id.includes(query) || name.includes(query);
        });

        el.nodeCountBadge.textContent = `${filtered.length} Node${filtered.length === 1 ? '' : 's'}`;

        if (filtered.length === 0) {
            el.nodeListContainer.innerHTML = '<div class="cmd-empty-state"><p>No nodes available</p></div>';
            return;
        }

        el.nodeListContainer.innerHTML = "";
        filtered.forEach(node => {
            const isSelected = node.node_id === state.selectedNodeId;
            const isOnline = String(node.status || "").toLowerCase() === "online";
            const lastSeen = node.last_seen ? formatTime(node.last_seen) : "Never";

            const card = document.createElement("div");
            card.className = `node-item-card ${isSelected ? 'selected' : ''}`;
            card.setAttribute("data-node-id", node.node_id);
            card.innerHTML = `
                <div class="node-item-top">
                    <span class="node-item-id">${escapeHtml(node.node_id)}</span>
                    <span class="status-pill-${isOnline ? 'online' : 'offline'}">${isOnline ? 'ONLINE' : 'OFFLINE'}</span>
                </div>
                <div class="node-item-name">${escapeHtml(node.name || 'Unnamed Node')}</div>
                <div class="node-item-meta">
                    <span>FW: ${escapeHtml(node.firmware_version || 'v1.0.0')}</span>
                    <span>${lastSeen}</span>
                </div>
            `;

            card.addEventListener("click", () => selectNode(node.node_id));
            el.nodeListContainer.appendChild(card);
        });
    }

    function selectNode(nodeId) {
        state.selectedNodeId = nodeId;

        // Highlight selected node in list
        document.querySelectorAll(".node-item-card").forEach(c => {
            c.classList.toggle("selected", c.getAttribute("data-node-id") === nodeId);
        });

        updateSelectedNodeUI();
        loadCommandHistory(nodeId);
    }

    function updateSelectedNodeUI() {
        const node = state.nodes.find(n => n.node_id === state.selectedNodeId);

        if (!node) {
            el.topTargetBadge.textContent = "Target: None";
            el.sendBtnSubtext.textContent = "Target: None";
            el.btnSendCommand.disabled = true;

            // Clear Device Status
            el.deviceStatusIndicator.textContent = "—";
            el.devNodeId.textContent = "—";
            el.devStatus.textContent = "—";
            el.devLastSeen.textContent = "—";
            el.devMcu.textContent = "—";
            el.devHwRev.textContent = "—";
            el.devFw.textContent = "—";
            el.devComm.textContent = "—";
            el.devLastCmdState.textContent = "—";
            el.devLastCmdState.className = "state-pill state-pill-sm state-idle";

            // Clear Banner
            el.bannerNodeName.textContent = "No Node Selected";
            el.bannerNodeId.textContent = "NONE";
            el.bannerConnectionBadge.textContent = "OFFLINE";
            el.bannerConnectionBadge.className = "connection-badge";
            el.bannerNodeDetails.textContent = "Select a node from the left panel to begin dispatching commands.";
            el.bannerActiveCmd.textContent = "None";
            el.bannerCmdState.textContent = "IDLE";
            el.bannerCmdState.className = "state-pill state-pill-sm state-idle";
            el.bannerLastResp.textContent = "N/A";
            return;
        }

        const isOnline = String(node.status || "").toLowerCase() === "online";
        const lastSeenStr = node.last_seen ? formatTime(node.last_seen) : "Never";

        // Toolbar & Send
        el.topTargetBadge.textContent = `Target: ${node.node_id}`;
        el.sendBtnSubtext.textContent = `Target: ${node.node_id}`;
        el.btnSendCommand.disabled = false;

        // Section 2: Device Status & Info
        el.deviceStatusIndicator.textContent = isOnline ? "ONLINE" : "OFFLINE";
        el.deviceStatusIndicator.className = isOnline ? "status-pill-online" : "status-pill-offline";
        el.devNodeId.textContent = node.node_id;
        el.devStatus.textContent = isOnline ? "Connected" : "Offline";
        el.devLastSeen.textContent = lastSeenStr;
        el.devMcu.textContent = `${node.mcu_family || 'ESP32'} ${node.mcu_model ? '(' + node.mcu_model + ')' : ''}`;
        el.devHwRev.textContent = node.hardware_revision || "REV-A";
        el.devFw.textContent = node.firmware_version || "1.0.0";
        el.devComm.textContent = node.communication_type || "LoRa";

        // Section 3: Banner
        el.bannerNodeName.textContent = node.name || node.node_id;
        el.bannerNodeId.textContent = node.node_id;
        el.bannerConnectionBadge.textContent = isOnline ? "ONLINE" : "OFFLINE";
        el.bannerConnectionBadge.className = `connection-badge ${isOnline ? 'online' : ''}`;
        el.bannerNodeDetails.textContent = `${node.mcu_family || 'ESP32'} • ${node.communication_type || 'LoRa'} • FW ${node.firmware_version || '1.0.0'} • Last Seen: ${lastSeenStr}`;

        el.historyTargetLabel.textContent = node.node_id;
    }

    /* ============================================================
       COMMAND HISTORY & DETAILS (SECTION 4, 5, 6)
       ============================================================ */
    async function loadCommandHistory(nodeId) {
        if (!nodeId) return;

        try {
            const data = await gateway.get(`/api/commands/node/${nodeId}?limit=100`);
            state.commandHistory = Array.isArray(data?.commands) ? data.commands : [];
            renderHistory();

            if (state.commandHistory.length > 0) {
                // If current selected command is in the list, keep it; else select most recent
                const found = state.commandHistory.find(c => c.command_id === state.selectedCommandId);
                selectCommand(found || state.commandHistory[0]);
            } else {
                state.activeCommand = null;
                state.selectedCommandId = null;
                resetCommandDetails();
            }
        } catch (err) {
            console.error("Failed to load command history:", err);
            el.historyListContainer.innerHTML = `<div class="cmd-empty-state"><p>Error loading history: ${escapeHtml(err.message)}</p></div>`;
        }
    }

    function renderHistory() {
        const filter = state.historyFilter;
        const filtered = state.commandHistory.filter(cmd => {
            if (filter === "ALL") return true;
            if (filter === "COMPLETED") return cmd.state === "COMPLETED";
            if (filter === "FAILED") return cmd.state === "FAILED";
            if (filter === "TIMEOUT") return cmd.state === "TIMEOUT";
            if (filter === "ACTIVE") return ["QUEUED", "SENT", "WAITING_ACK", "ACK_RECEIVED", "EXECUTING"].includes(cmd.state);
            return true;
        });

        if (filtered.length === 0) {
            el.historyListContainer.innerHTML = '<div class="cmd-empty-state"><p>No command history for this filter</p></div>';
            return;
        }

        el.historyListContainer.innerHTML = "";
        filtered.forEach(cmd => {
            const isSelected = cmd.command_id === state.selectedCommandId;
            const created = cmd.created_at ? formatTime(cmd.created_at) : "—";
            const stateClass = `state-${String(cmd.state || '').toLowerCase()}`;

            const card = document.createElement("div");
            card.className = `history-item-card ${isSelected ? 'active' : ''}`;
            card.setAttribute("data-cmd-id", cmd.command_id);
            card.innerHTML = `
                <div class="history-item-head">
                    <span class="history-cmd-id">${escapeHtml(cmd.command_id)}</span>
                    <span class="state-pill state-pill-sm ${stateClass}">${escapeHtml(cmd.state)}</span>
                </div>
                <div class="history-item-head">
                    <span class="history-item-type">${escapeHtml(cmd.command_type)}</span>
                    <span class="history-item-time">${created}</span>
                </div>
            `;

            card.addEventListener("click", () => selectCommand(cmd));
            el.historyListContainer.appendChild(card);
        });
    }

    function selectCommand(cmd) {
        if (!cmd) return;
        state.activeCommand = cmd;
        state.selectedCommandId = cmd.command_id;

        // Highlight in history list
        document.querySelectorAll(".history-item-card").forEach(c => {
            c.classList.toggle("active", c.getAttribute("data-cmd-id") === cmd.command_id);
        });

        renderCommandDetails(cmd);
        renderResponseDetails(cmd);
        updateBannerCommandState(cmd);
    }

    function renderCommandDetails(cmd) {
        const stateStr = cmd.state || "QUEUED";
        const stateClass = `state-${stateStr.toLowerCase()}`;

        el.cmdHeaderId.textContent = `ID: ${cmd.command_id}`;
        el.activeCmdStatePill.textContent = stateStr;
        el.activeCmdStatePill.className = `state-pill ${stateClass}`;

        // Action Buttons Enablement
        const isTerminal = ["COMPLETED", "FAILED", "TIMEOUT", "CANCELLED"].includes(stateStr);
        el.btnCancelCmd.disabled = isTerminal;
        el.btnRetryCmd.disabled = !["TIMEOUT", "FAILED"].includes(stateStr) || (cmd.retry_count >= cmd.max_retries);

        // Metadata
        el.metaCmdType.textContent = cmd.command_type || "—";
        el.metaCmdTarget.textContent = cmd.node_id || "—";
        el.metaCmdPriority.textContent = `Priority ${cmd.priority || 1}`;
        el.metaCmdRetries.textContent = `${cmd.retry_count || 0} / ${cmd.max_retries || 3}`;
        el.metaCmdCreated.textContent = cmd.created_at ? formatTime(cmd.created_at) : "—";
        el.metaCmdTimeout.textContent = cmd.timeout_at ? formatTime(cmd.timeout_at) : "—";

        // Update Stepper
        updateLifecycleStepper(stateStr);
    }

    function updateLifecycleStepper(currentState) {
        const steps = ["QUEUED", "SENT", "WAITING_ACK", "ACK_RECEIVED", "EXECUTING", "COMPLETED"];
        const stateIndexMap = {
            "QUEUED": 0,
            "SENT": 1,
            "WAITING_ACK": 2,
            "ACK_RECEIVED": 3,
            "EXECUTING": 4,
            "COMPLETED": 5,
            "TIMEOUT": 2,
            "FAILED": 4,
            "CANCELLED": 0
        };

        const targetIdx = stateIndexMap[currentState] ?? 0;

        steps.forEach((stepName, idx) => {
            const stepEl = document.getElementById(`step-${stepName.toLowerCase().replace('_', '-')}`);
            if (!stepEl) return;

            stepEl.classList.remove("active", "completed");

            if (currentState === "COMPLETED" || idx < targetIdx) {
                stepEl.classList.add("completed");
            } else if (idx === targetIdx) {
                stepEl.classList.add("active");
            }
        });

        // Update connecting lines
        for (let i = 1; i <= 5; i++) {
            const line = document.getElementById(`line-${i}`);
            if (line) {
                line.classList.toggle("active", i <= targetIdx);
            }
        }
    }

    function renderResponseDetails(cmd) {
        // ACK Status
        const ackAt = cmd.ack_at ? formatTime(cmd.ack_at) : "—";
        const hasAck = !!cmd.ack_at || ["ACK_RECEIVED", "EXECUTING", "COMPLETED"].includes(cmd.state);
        const ackStatus = cmd.ack_status || (hasAck ? "RECEIVED" : "WAITING");

        el.ackBadgeStatus.textContent = ackStatus;
        el.ackBadgeStatus.className = `ack-badge ${hasAck ? 'ok' : ''}`;
        el.ackMessageText.textContent = cmd.ack_message || (hasAck ? "Command acknowledged by device" : "Waiting for device ACK...");
        el.ackTimestampText.textContent = hasAck ? `ACK Time: ${ackAt}` : "—";

        // Response Status
        const respAt = cmd.response_at || cmd.completed_at;
        const isSuccess = cmd.state === "COMPLETED";
        const isFailed = cmd.state === "FAILED";
        const isTimeout = cmd.state === "TIMEOUT";

        if (isSuccess) {
            el.respBadgeStatus.textContent = "SUCCESS";
            el.respBadgeStatus.className = "resp-badge ok";
            el.respSummaryText.textContent = "Command executed successfully";
            el.respTimestampText.textContent = `Completed: ${respAt ? formatTime(respAt) : '—'}`;
        } else if (isFailed) {
            el.respBadgeStatus.textContent = "FAILED";
            el.respBadgeStatus.className = "resp-badge fail";
            el.respSummaryText.textContent = cmd.error || "Execution failed";
            el.respTimestampText.textContent = `Failed: ${respAt ? formatTime(respAt) : '—'}`;
        } else if (isTimeout) {
            el.respBadgeStatus.textContent = "TIMEOUT";
            el.respBadgeStatus.className = "resp-badge fail";
            el.respSummaryText.textContent = "Command timed out while waiting for node response";
            el.respTimestampText.textContent = `Timeout: ${cmd.timeout_at ? formatTime(cmd.timeout_at) : '—'}`;
        } else {
            el.respBadgeStatus.textContent = "WAITING";
            el.respBadgeStatus.className = "resp-badge";
            el.respSummaryText.textContent = "Waiting for node response...";
            el.respTimestampText.textContent = "—";
        }

        // Error Banner
        if (cmd.error) {
            el.cmdErrorBanner.style.display = "block";
            el.cmdErrorMessage.textContent = cmd.error;
        } else {
            el.cmdErrorBanner.style.display = "none";
        }

        // Result Data Viewer
        if (cmd.result !== null && cmd.result !== undefined && Object.keys(cmd.result).length > 0) {
            try {
                el.responseDataJson.textContent = typeof cmd.result === "object" ?
                    JSON.stringify(cmd.result, null, 2) : String(cmd.result);
            } catch {
                el.responseDataJson.textContent = String(cmd.result);
            }
        } else if (isSuccess) {
            el.responseDataJson.textContent = JSON.stringify({ status: "SUCCESS", message: "Command executed without return payload" }, null, 2);
        } else {
            el.responseDataJson.textContent = "Waiting for node response...";
        }
    }

    function updateBannerCommandState(cmd) {
        if (!cmd) return;
        el.bannerActiveCmd.textContent = cmd.command_id;
        el.bannerCmdState.textContent = cmd.state;
        el.bannerCmdState.className = `state-pill state-pill-sm state-${String(cmd.state).toLowerCase()}`;
        el.bannerLastResp.textContent = cmd.state === "COMPLETED" ? "SUCCESS" : (cmd.error ? "FAILED" : "PENDING");

        // Also update Section 2 last command state
        el.devLastCmdState.textContent = `${cmd.command_type}: ${cmd.state}`;
        el.devLastCmdState.className = `state-pill state-pill-sm state-${String(cmd.state).toLowerCase()}`;
    }

    function resetCommandDetails() {
        el.cmdHeaderId.textContent = "No active command";
        el.activeCmdStatePill.textContent = "IDLE";
        el.activeCmdStatePill.className = "state-pill state-idle";
        el.btnCancelCmd.disabled = true;
        el.btnRetryCmd.disabled = true;

        el.metaCmdType.textContent = "—";
        el.metaCmdTarget.textContent = "—";
        el.metaCmdPriority.textContent = "—";
        el.metaCmdRetries.textContent = "—";
        el.metaCmdCreated.textContent = "—";
        el.metaCmdTimeout.textContent = "—";

        updateLifecycleStepper("QUEUED");
        document.querySelectorAll(".step-node").forEach(s => s.classList.remove("active", "completed"));

        el.ackBadgeStatus.textContent = "WAITING";
        el.ackBadgeStatus.className = "ack-badge";
        el.ackMessageText.textContent = "Waiting for device ACK...";
        el.ackTimestampText.textContent = "—";

        el.respBadgeStatus.textContent = "WAITING";
        el.respBadgeStatus.className = "resp-badge";
        el.respSummaryText.textContent = "Waiting for command completion...";
        el.respTimestampText.textContent = "—";

        el.cmdErrorBanner.style.display = "none";
        el.responseDataJson.textContent = "Waiting for node response...";

        el.bannerActiveCmd.textContent = "None";
        el.bannerCmdState.textContent = "IDLE";
        el.bannerCmdState.className = "state-pill state-pill-sm state-idle";
        el.bannerLastResp.textContent = "N/A";
    }

    /* ============================================================
       COMMAND DISPATCH (SECTION 7 & 8)
       ============================================================ */
    async function handleSendCommand() {
        if (!state.selectedNodeId) {
            if (window.gateway?.toast) gateway.toast("Please select a target node first", "warning");
            return;
        }

        const cmdType = el.cmdTypeSelect.value;
        const priority = parseInt(el.cmdPrioritySelect.value) || 1;
        const timeoutSeconds = parseInt(el.cmdTimeoutInput.value) || 30;
        const maxRetries = parseInt(el.cmdRetriesInput.value) || 3;

        let payload = {};
        let finalCommandType = cmdType;

        try {
            if (cmdType === "STATUS") {
                payload = {};
            } else if (cmdType === "PING") {
                payload = { echo: el.paramPingMsg.value.trim() || "PING" };
            } else if (cmdType === "WIFI_SCAN") {
                payload = {
                    band: el.paramScanBand.value,
                    limit: parseInt(el.paramScanLimit.value) || 20
                };
            } else if (cmdType === "WIFI_CONNECT") {
                const ssid = el.paramWifiSsid.value.trim();
                if (!ssid) {
                    if (window.gateway?.toast) gateway.toast("Wi-Fi SSID is required", "warning");
                    el.paramWifiSsid.focus();
                    return;
                }
                payload = {
                    ssid: ssid,
                    password: el.paramWifiPass.value,
                    save: el.paramWifiSave.value === "true"
                };
            } else if (cmdType === "RESTART") {
                payload = {
                    delay_seconds: parseInt(el.paramRebootDelay.value) || 1,
                    reason: el.paramRebootReason.value.trim() || "Operator reboot"
                };
            } else if (cmdType === "GET_CONFIG") {
                payload = { section: el.paramConfigSection.value.trim() || "all" };
            } else if (cmdType === "SET_INTERVAL") {
                const interval = parseInt(el.paramIntervalMs.value);
                if (!interval || interval < 500) {
                    if (window.gateway?.toast) gateway.toast("Interval must be at least 500 ms", "warning");
                    return;
                }
                payload = { interval_ms: interval };
            } else if (cmdType === "CUSTOM") {
                const customName = el.paramCustomName.value.trim();
                if (!customName) {
                    if (window.gateway?.toast) gateway.toast("Custom command name is required", "warning");
                    el.paramCustomName.focus();
                    return;
                }
                finalCommandType = customName;

                const customJsonText = el.paramCustomJson.value.trim();
                if (customJsonText) {
                    try {
                        payload = JSON.parse(customJsonText);
                    } catch (err) {
                        if (window.gateway?.toast) gateway.toast(`Invalid custom JSON payload: ${err.message}`, "error");
                        return;
                    }
                }
            }
        } catch (err) {
            console.error("Payload building error:", err);
            return;
        }

        // Prepare request body
        const reqBody = {
            node_id: state.selectedNodeId,
            command_type: finalCommandType,
            payload: payload,
            priority: priority,
            timeout_seconds: timeoutSeconds,
            max_retries: maxRetries
        };

        // UI Loading state
        el.btnSendCommand.disabled = true;
        const originalText = el.btnSendCommand.querySelector(".btn-text").textContent;
        el.btnSendCommand.querySelector(".btn-text").textContent = "DISPATCHING...";

        try {
            const res = await gateway.post("/api/commands", reqBody);
            const cmd = res?.command;

            if (cmd) {
                if (window.gateway?.toast) {
                    gateway.toast(`Command ${cmd.command_id} dispatched (QUEUED)`, "success");
                }

                // Add to history and select
                state.commandHistory.unshift(cmd);
                renderHistory();
                selectCommand(cmd);
            }
        } catch (err) {
            console.error("Send command failed:", err);
            if (window.gateway?.toast) {
                gateway.toast(err.message || "Failed to dispatch command", "error");
            }
        } finally {
            el.btnSendCommand.disabled = false;
            el.btnSendCommand.querySelector(".btn-text").textContent = originalText;
        }
    }

    /* ============================================================
       CANCEL & RETRY ACTIONS
       ============================================================ */
    async function handleCancelCommand() {
        if (!state.activeCommand) return;
        const cid = state.activeCommand.command_id;

        try {
            const res = await gateway.post(`/api/commands/${cid}/cancel`, { reason: "Cancelled via Command Center" });
            if (res?.command) {
                updateCommandInState(res.command);
                if (window.gateway?.toast) gateway.toast(`Command ${cid} cancelled`, "info");
            }
        } catch (err) {
            console.error("Cancel failed:", err);
            if (window.gateway?.toast) gateway.toast(err.message, "error");
        }
    }

    async function handleRetryCommand() {
        if (!state.activeCommand) return;
        const cid = state.activeCommand.command_id;

        try {
            const res = await gateway.post(`/api/commands/${cid}/retry`, {});
            if (res?.command) {
                updateCommandInState(res.command);
                if (window.gateway?.toast) gateway.toast(`Command ${cid} reset for retry (QUEUED)`, "success");
            }
        } catch (err) {
            console.error("Retry failed:", err);
            if (window.gateway?.toast) gateway.toast(err.message, "error");
        }
    }

    /* ============================================================
       TIMELINE MODAL (EVENT AUDITING)
       ============================================================ */
    async function openTimelineModal(commandId) {
        el.modalCmdId.textContent = commandId;
        el.timelineModalOverlay.style.display = "flex";
        el.timelineEventsList.innerHTML = '<div class="cmd-empty-state"><p>Loading timeline events...</p></div>';

        try {
            const data = await gateway.get(`/api/commands/${commandId}/events`);
            const events = Array.isArray(data?.events) ? data.events : [];

            if (events.length === 0) {
                el.timelineEventsList.innerHTML = '<div class="cmd-empty-state"><p>No events recorded for this command.</p></div>';
                return;
            }

            el.timelineEventsList.innerHTML = "";
            events.forEach(evt => {
                const time = evt.created_at ? formatTime(evt.created_at) : "—";
                const statePill = `<span class="state-pill state-pill-sm state-${String(evt.state).toLowerCase()}">${escapeHtml(evt.state)}</span>`;

                let detailsHtml = "";
                if (evt.details) {
                    const detailsStr = typeof evt.details === "object" ? JSON.stringify(evt.details) : String(evt.details);
                    detailsHtml = `<div class="timeline-event-details"><code>${escapeHtml(detailsStr)}</code></div>`;
                }
                if (evt.error) {
                    detailsHtml += `<div class="timeline-event-details" style="color: var(--red);"><strong>Error:</strong> ${escapeHtml(evt.error)}</div>`;
                }

                const item = document.createElement("div");
                item.className = "timeline-event-item";
                item.innerHTML = `
                    <div class="timeline-event-head">
                        <span class="timeline-event-type">${escapeHtml(evt.event_type)}</span>
                        ${statePill}
                        <span class="timeline-event-time">${time}</span>
                    </div>
                    ${detailsHtml}
                `;
                el.timelineEventsList.appendChild(item);
            });
        } catch (err) {
            console.error("Failed to load timeline events:", err);
            el.timelineEventsList.innerHTML = `<div class="cmd-empty-state"><p>Error: ${escapeHtml(err.message)}</p></div>`;
        }
    }

    function closeTimelineModal() {
        el.timelineModalOverlay.style.display = "none";
    }

    /* ============================================================
       SOCKET.IO REAL-TIME INTEGRATION
       ============================================================ */
    function initSocketIO() {
        try {
            if (typeof io !== "function") {
                console.warn("Socket.IO client library not found; falling back to polling.");
                updateSocketStatus(false);
                return;
            }

            state.socket = io({
                reconnection: true,
                reconnectionDelay: 2000,
                reconnectionAttempts: 10
            });

            state.socket.on("connect", () => {
                updateSocketStatus(true);
                // Sync latest data upon reconnect
                loadNodes();
                if (state.selectedNodeId) {
                    loadCommandHistory(state.selectedNodeId);
                }
            });

            state.socket.on("disconnect", () => {
                updateSocketStatus(false);
            });

            // Listen to command_update events from backend
            state.socket.on("command_update", (payload) => {
                handleSocketCommandUpdate(payload);
            });

            // Listen to node updates
            state.socket.on("node_update", (nodePayload) => {
                if (nodePayload?.node_id) {
                    const idx = state.nodes.findIndex(n => n.node_id === nodePayload.node_id);
                    if (idx !== -1) {
                        state.nodes[idx] = { ...state.nodes[idx], ...nodePayload };
                        renderNodes();
                        if (state.selectedNodeId === nodePayload.node_id) {
                            updateSelectedNodeUI();
                        }
                    }
                }
            });

        } catch (err) {
            console.error("Socket.IO setup error:", err);
            updateSocketStatus(false);
        }
    }

    function updateSocketStatus(connected) {
        state.socketConnected = connected;
        if (connected) {
            el.socketStatusPill.className = "socket-status-pill connected";
            el.socketStatusText.textContent = "Live Socket";
        } else {
            el.socketStatusPill.className = "socket-status-pill disconnected";
            el.socketStatusText.textContent = "Offline (Polling)";
        }
    }

    function handleSocketCommandUpdate(payload) {
        const cmd = payload?.command || payload;
        if (!cmd || !cmd.command_id) return;

        // If belongs to currently selected node, update state
        if (cmd.node_id === state.selectedNodeId) {
            updateCommandInState(cmd);
        }
    }

    function updateCommandInState(updatedCmd) {
        const idx = state.commandHistory.findIndex(c => c.command_id === updatedCmd.command_id);
        if (idx !== -1) {
            state.commandHistory[idx] = { ...state.commandHistory[idx], ...updatedCmd };
        } else {
            state.commandHistory.unshift(updatedCmd);
        }

        renderHistory();

        // If currently inspected command updated, refresh its view
        if (state.selectedCommandId === updatedCmd.command_id) {
            selectCommand(updatedCmd);
        }
    }

    function startPolling() {
        if (state.pollingTimer) clearInterval(state.pollingTimer);
        state.pollingTimer = setInterval(() => {
            if (state.selectedNodeId) {
                // Background poll history to ensure synchronization
                loadCommandHistory(state.selectedNodeId);
            }
        }, 8000);
    }

    /* ============================================================
       UTILITY HELPERS
       ============================================================ */
    function formatTime(isoStr) {
        if (!isoStr) return "—";
        try {
            const date = new Date(isoStr);
            if (Number.isNaN(date.getTime())) return "—";
            return new Intl.DateTimeFormat("en-IN", {
                timeZone: "Asia/Kolkata",
                month: "short",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false
            }).format(date);
        } catch {
            return String(isoStr);
        }
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function copyResultToClipboard() {
        const text = el.responseDataJson.textContent;
        if (!text || text.includes("Waiting for node response")) {
            if (window.gateway?.toast) gateway.toast("No result data to copy", "info");
            return;
        }
        navigator.clipboard.writeText(text).then(() => {
            if (window.gateway?.toast) gateway.toast("Result payload copied to clipboard", "success");
        }).catch(() => {
            if (window.gateway?.toast) gateway.toast("Failed to copy to clipboard", "error");
        });
    }

})();

