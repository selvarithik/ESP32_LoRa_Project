/* ============================================================
   SELVARITHIK'S LORA GATEWAY
   DASHBOARD CONTROLLER & TELEMETRY ENGINE
   ============================================================ */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const nodesTable = document.getElementById("dashboard-nodes");
    if (!nodesTable) return;

    let selectedNode = null;
    let selectedParam = null;
    let chartTimeRange = "1h";
    let refreshTimer = null;
    let currentNodesList = [];
    let currentSensorsList = [];
    let telemetryHistoryData = [];
    let customSensorWidgets = [];
    let editingSensorWidgetId = null;

    // Chart Canvas
    const canvas = document.getElementById("dashboard-telemetry-chart");
    const ctx = canvas ? canvas.getContext("2d") : null;

    /* ============================================================
       INITIALIZATION
       ============================================================ */
    initDashboard();

    async function initDashboard() {
        bindEvents();
        initWidgetPreferences();
        initCustomSensorWidgets();
        await loadDashboard();

        // Real-time polling (every 2 seconds)
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(loadDashboard, 2000);

        // Resize listener for chart canvas
        window.addEventListener("resize", () => {
            if (canvas) renderTelemetryChart();
        });

        window.addEventListener("gateway:themechange", () => {
            if (canvas) renderTelemetryChart();
        });
    }

    /* ============================================================
       EVENT BINDINGS
       ============================================================ */
    function bindEvents() {
        // Refresh Button
        const refreshBtn = document.getElementById("dashboard-refresh");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", async () => {
                await loadDashboard();
                if (window.gateway?.toast) gateway.toast("Dashboard refreshed", "info");
            });
        }

        // Widget Customization Drawer
        const customizeBtn = document.getElementById("dashboard-customize-btn");
        const drawer = document.getElementById("widget-drawer");
        const overlay = document.getElementById("widget-drawer-overlay");
        const closeBtn = document.getElementById("close-widget-drawer");
        const saveWidgetsBtn = document.getElementById("save-widgets-btn");
        const resetWidgetsBtn = document.getElementById("reset-widgets-btn");

        if (customizeBtn && drawer && overlay) {
            customizeBtn.addEventListener("click", () => {
                drawer.classList.add("open");
                overlay.classList.add("open");
            });

            const closeDrawer = () => {
                drawer.classList.remove("open");
                overlay.classList.remove("open");
            };

            closeBtn?.addEventListener("click", closeDrawer);
            overlay.addEventListener("click", closeDrawer);

            saveWidgetsBtn?.addEventListener("click", () => {
                saveWidgetPreferences();
                closeDrawer();
                if (window.gateway?.toast) gateway.toast("Dashboard layout saved", "success");
            });

            resetWidgetsBtn?.addEventListener("click", () => {
                localStorage.removeItem("gateway_dashboard_widgets");
                initWidgetPreferences();
                closeDrawer();
                if (window.gateway?.toast) gateway.toast("Widgets reset to default", "info");
            });
        }

        // Custom sensor widgets
        const addSensorBtn = document.getElementById("add-sensor-widget-btn");
        const addSensorInline = document.getElementById("add-sensor-widget-inline");
        const widgetEditor = document.getElementById("sensor-widget-editor");
        const widgetOverlay = document.getElementById("sensor-widget-overlay");
        const closeWidgetEditor = document.getElementById("close-sensor-widget-editor");
        const cancelWidgetEditor = document.getElementById("cancel-sensor-widget");
        const saveWidgetEditor = document.getElementById("save-sensor-widget");
        const widgetNodeSelect = document.getElementById("sensor-widget-node");
        const widgetParameterSelect = document.getElementById("sensor-widget-parameter");

        const openSensorEditor = async (widget = null) => {
            if (!widgetEditor || !widgetOverlay) return;
            editingSensorWidgetId = widget?.id || null;

            document.getElementById("sensor-widget-name").value = widget?.name || "";
            document.getElementById("sensor-widget-type").value = widget?.type || "value";
            document.getElementById("sensor-widget-color").value = widget?.color || getComputedStyle(document.documentElement).getPropertyValue("--brand-primary").trim() || "#E87522";
            document.getElementById("sensor-widget-meta").checked = widget?.showMeta !== false;

            populateWidgetNodeSelect();
            if (widgetNodeSelect) {
                widgetNodeSelect.value = widget?.nodeId || selectedNode || "";
            }
            await populateWidgetParameters(widgetNodeSelect?.value || "");
            if (widgetParameterSelect) {
                widgetParameterSelect.value = widget?.parameter || "";
            }

            const title = widgetEditor.querySelector("h3");
            const saveLabel = saveWidgetEditor?.textContent;
            if (title) title.textContent = widget ? "Edit Sensor Widget" : "Create Sensor Widget";
            if (saveWidgetEditor) saveWidgetEditor.textContent = widget ? "Save Changes" : (saveLabel || "Create Widget");

            widgetEditor.classList.add("open");
            widgetOverlay.classList.add("open");
            widgetEditor.setAttribute("aria-hidden", "false");
        };

        const closeSensorEditor = () => {
            widgetEditor?.classList.remove("open");
            widgetOverlay?.classList.remove("open");
            widgetEditor?.setAttribute("aria-hidden", "true");
            editingSensorWidgetId = null;
        };

        addSensorBtn?.addEventListener("click", () => openSensorEditor());
        addSensorInline?.addEventListener("click", () => openSensorEditor());
        closeWidgetEditor?.addEventListener("click", closeSensorEditor);
        cancelWidgetEditor?.addEventListener("click", closeSensorEditor);
        widgetOverlay?.addEventListener("click", closeSensorEditor);

        widgetNodeSelect?.addEventListener("change", () => {
            populateWidgetParameters(widgetNodeSelect.value);
        });

        saveWidgetEditor?.addEventListener("click", async () => {
            const name = document.getElementById("sensor-widget-name")?.value.trim();
            const nodeId = widgetNodeSelect?.value;
            const parameter = widgetParameterSelect?.value;
            const type = document.getElementById("sensor-widget-type")?.value || "value";
            const color = document.getElementById("sensor-widget-color")?.value || "#E87522";
            const showMeta = document.getElementById("sensor-widget-meta")?.checked !== false;

            if (!nodeId || !parameter) {
                gateway.toast?.("Select a node and sensor parameter", "error");
                return;
            }

            const existing = customSensorWidgets.find(w => w.id === editingSensorWidgetId);
            const widget = {
                id: editingSensorWidgetId || `sensor-widget-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
                name: name || parameter,
                nodeId,
                parameter,
                type,
                color,
                showMeta
            };

            if (existing) {
                Object.assign(existing, widget);
            } else {
                customSensorWidgets.push(widget);
            }

            saveCustomSensorWidgets();
            renderCustomSensorWidgets();
            closeSensorEditor();
            gateway.toast?.(existing ? "Sensor widget updated" : "Sensor widget created", "success");
        });

        document.addEventListener("click", (event) => {
            const editBtn = event.target.closest?.("[data-edit-sensor-widget]");
            const deleteBtn = event.target.closest?.("[data-delete-sensor-widget]");

            if (editBtn) {
                const widget = customSensorWidgets.find(w => w.id === editBtn.getAttribute("data-edit-sensor-widget"));
                if (widget) openSensorEditor(widget);
            }

            if (deleteBtn) {
                const id = deleteBtn.getAttribute("data-delete-sensor-widget");
                customSensorWidgets = customSensorWidgets.filter(w => w.id !== id);
                saveCustomSensorWidgets();
                renderCustomSensorWidgets();
            }
        });

        // Chart Parameter Select
        const paramSelect = document.getElementById("chart-parameter-select");
        if (paramSelect) {
            paramSelect.addEventListener("change", (e) => {
                selectedParam = e.target.value;
                loadTelemetryHistory();
            });
        }

        // Chart Time Range Buttons
        const rangeButtons = document.querySelectorAll("#chartTimeRangeGroup .time-range-btn");
        rangeButtons.forEach(btn => {
            btn.addEventListener("click", (e) => {
                rangeButtons.forEach(b => b.classList.remove("active"));
                e.target.classList.add("active");
                chartTimeRange = e.target.getAttribute("data-range") || "1h";
                loadTelemetryHistory();
            });
        });
    }

    /* ============================================================
       WIDGET CUSTOMIZATION ENGINE
       ============================================================ */
    function initWidgetPreferences() {
        try {
            const raw = localStorage.getItem("gateway_dashboard_widgets");
            const prefs = raw ? JSON.parse(raw) : null;

            document.querySelectorAll(".widget-toggle-item input").forEach(input => {
                const widgetId = input.getAttribute("data-target-widget");
                if (prefs && typeof prefs[widgetId] === "boolean") {
                    input.checked = prefs[widgetId];
                } else {
                    input.checked = true;
                }
            });

            applyWidgetVisibility();
        } catch (err) {
            console.error("Widget preferences load error:", err);
        }
    }

    function saveWidgetPreferences() {
        const prefs = {};
        document.querySelectorAll(".widget-toggle-item input").forEach(input => {
            const widgetId = input.getAttribute("data-target-widget");
            prefs[widgetId] = input.checked;
        });

        localStorage.setItem("gateway_dashboard_widgets", JSON.stringify(prefs));
        applyWidgetVisibility();
    }

    function applyWidgetVisibility() {
        document.querySelectorAll(".widget-toggle-item input").forEach(input => {
            const widgetId = input.getAttribute("data-target-widget");
            const widgetEl = document.querySelector(`.dashboard-widget[data-widget-id="${widgetId}"]`);
            if (widgetEl) {
                widgetEl.style.display = input.checked ? "" : "none";
            }
        });
    }

    /* ============================================================
       CUSTOM SENSOR WIDGETS
       ============================================================ */
    function initCustomSensorWidgets() {
        try {
            const raw = localStorage.getItem("gateway_custom_sensor_widgets");
            customSensorWidgets = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(customSensorWidgets)) customSensorWidgets = [];
        } catch (error) {
            console.error("Custom sensor widget load error:", error);
            customSensorWidgets = [];
        }
        renderCustomSensorWidgets();
    }

    function saveCustomSensorWidgets() {
        localStorage.setItem("gateway_custom_sensor_widgets", JSON.stringify(customSensorWidgets));
    }

    function populateWidgetNodeSelect() {
        const select = document.getElementById("sensor-widget-node");
        if (!select) return;

        select.innerHTML = '<option value="">Select Node</option>' +
            currentNodesList.map(node => {
                const id = gateway.escape(node.node_id);
                const name = gateway.escape(node.name || node.node_id);
                return `<option value="${id}">${name} (${id})</option>`;
            }).join("");
    }

    async function populateWidgetParameters(nodeId) {
        const select = document.getElementById("sensor-widget-parameter");
        if (!select) return;

        if (!nodeId) {
            select.innerHTML = '<option value="">Select Parameter</option>';
            return;
        }

        try {
            let sensors = [];
            if (nodeId === selectedNode && currentSensorsList.length) {
                sensors = currentSensorsList;
            } else {
                const data = await gateway.get(`/api/nodes/${encodeURIComponent(nodeId)}/parameters`);
                sensors = Array.isArray(data) ? data : (data.parameters || []);
            }

            select.innerHTML = '<option value="">Select Parameter</option>' +
                sensors.map(s => {
                    const name = s.parameter_name || s.name;
                    return name
                        ? `<option value="${gateway.escape(name)}">${gateway.escape(name)}${s.unit ? ` (${gateway.escape(s.unit)})` : ""}</option>`
                        : "";
                }).join("");
        } catch (error) {
            console.error("Widget parameter load error:", error);
            select.innerHTML = '<option value="">Unable to load parameters</option>';
        }
    }

    async function refreshCustomSensorWidgets() {
        if (!customSensorWidgets.length) {
            renderCustomSensorWidgets();
            return;
        }

        const dataByNode = {};
        if (selectedNode) dataByNode[selectedNode] = currentSensorsList;

        for (const widget of customSensorWidgets) {
            if (!widget.nodeId || !widget.parameter) continue;
            if (!dataByNode[widget.nodeId]) {
                try {
                    const data = await gateway.get(`/api/parameters/${widget.nodeId}`);
                    dataByNode[widget.nodeId] = Array.isArray(data) ? data : (data.parameters || []);
                } catch (error) {
                    console.error("Widget node data error:", widget.nodeId, error);
                    dataByNode[widget.nodeId] = [];
                }
            }

            const sensor = dataByNode[widget.nodeId].find(s =>
                (s.parameter_name || s.name) === widget.parameter
            );
            widget.runtime = sensor ? {
                value: sensor.value,
                unit: sensor.unit || "",
                status: gateway.status(sensor.status || sensor.quality),
                quality: sensor.quality || "Good",
                min: Number.isFinite(Number(sensor.min_value)) ? Number(sensor.min_value) : 0,
                max: Number.isFinite(Number(sensor.max_value)) ? Number(sensor.max_value) : 100,
                updated: sensor.updated_at || sensor.last_update || null
            } : null;
        }

        renderCustomSensorWidgets();
    }

    function renderCustomSensorWidgets() {
        const container = document.getElementById("custom-sensor-widgets");
        if (!container) return;

        if (!customSensorWidgets.length) {
            container.innerHTML = `
                <div class="empty-state custom-widget-empty">
                    No custom sensor widgets yet. Use “+ Add” to create one.
                </div>`;
            return;
        }

        container.innerHTML = customSensorWidgets.map(widget => {
            const runtime = widget.runtime;
            const value = runtime?.value ?? "—";
            const unit = runtime?.unit || "";
            const status = runtime?.status || "offline";
            const safeColor = isSafeHex(widget.color) ? widget.color : "#E87522";
            const min = Number.isFinite(runtime?.min) ? runtime.min : 0;
            const max = Number.isFinite(runtime?.max) && runtime.max > min ? runtime.max : 100;
            const numeric = Number(value);
            const percent = Number.isFinite(numeric)
                ? Math.max(0, Math.min(100, ((numeric - min) / (max - min)) * 100))
                : 0;

            let visualization = `
                <div class="custom-widget-value" style="--widget-accent:${safeColor}">
                    <strong>${gateway.escape(String(value))}</strong>
                    <span>${gateway.escape(unit)}</span>
                </div>`;

            if (widget.type === "gauge") {
                visualization = `
                    <div class="custom-widget-gauge" style="--widget-accent:${safeColor}; --widget-pct:${percent}%">
                        <div class="custom-widget-gauge-ring"><span>${gateway.escape(String(value))}</span></div>
                        <small>${gateway.escape(unit)}</small>
                    </div>`;
            } else if (widget.type === "bar") {
                visualization = `
                    <div class="custom-widget-bar-wrap" style="--widget-accent:${safeColor}">
                        <div class="custom-widget-bar-track"><span style="width:${percent}%"></span></div>
                        <strong>${gateway.escape(String(value))} ${gateway.escape(unit)}</strong>
                    </div>`;
            } else if (widget.type === "status") {
                visualization = `
                    <div class="custom-widget-status" style="--widget-accent:${safeColor}">
                        <span class="custom-widget-status-dot"></span>
                        <strong>${gateway.escape((runtime?.status || "offline").toUpperCase())}</strong>
                    </div>`;
            }

            return `
                <article class="custom-sensor-widget" data-custom-sensor-widget-id="${gateway.escape(widget.id)}">
                    <div class="custom-widget-head">
                        <div>
                            <strong>${gateway.escape(widget.name || widget.parameter)}</strong>
                            <small>${gateway.escape(widget.parameter)}</small>
                        </div>
                        <div class="custom-widget-actions">
                            <button type="button" class="icon-btn" data-edit-sensor-widget="${gateway.escape(widget.id)}" aria-label="Edit ${gateway.escape(widget.name)}">✎</button>
                            <button type="button" class="icon-btn" data-delete-sensor-widget="${gateway.escape(widget.id)}" aria-label="Delete ${gateway.escape(widget.name)}">×</button>
                        </div>
                    </div>
                    ${visualization}
                    ${widget.showMeta !== false ? `
                        <div class="custom-widget-meta">
                            <span>${gateway.escape(widget.nodeId)}</span>
                            <span class="status ${status}"><i></i>${status.toUpperCase()}</span>
                        </div>` : ""}
                </article>`;
        }).join("");
    }

    function isSafeHex(value) {
        return /^#[0-9A-Fa-f]{6}$/.test(String(value || ""));
    }

    /* ============================================================
       LOAD DASHBOARD DATA
       ============================================================ */
    async function loadDashboard() {
        try {
            const response = await gateway.get("/api/nodes");
            const nodes = Array.isArray(response) ? response : (response.nodes || []);
            currentNodesList = nodes;

            updateStatistics(nodes);
            renderNodes(nodes);

            // Auto-select first node if none selected
            if (!selectedNode && nodes.length > 0) {
                selectedNode = nodes[0].node_id;
            }

            if (selectedNode) {
                await loadSensors(selectedNode);
            } else {
                showNoNode();
            }

            await loadActivity();
            await refreshCustomSensorWidgets();

        } catch (error) {
            console.error("Dashboard error:", error);
            showDashboardError();
        }
    }

    /* ============================================================
       STATISTICS COUNTERS
       ============================================================ */
    function updateStatistics(nodes) {
        const total = document.getElementById("total-nodes");
        const online = document.getElementById("online-nodes");
        const sensorCount = document.getElementById("sensor-count");
        const alarmCount = document.getElementById("alarm-count");

        const onlineNodes = nodes.filter(n => gateway.status(n.status) === "online");

        if (total) total.textContent = nodes.length;
        if (online) online.textContent = onlineNodes.length;
        if (sensorCount && sensorCount.textContent === "—") sensorCount.textContent = "0";
        if (alarmCount && alarmCount.textContent === "—") alarmCount.textContent = "0";
    }

    /* ============================================================
       RENDER NODES TABLE
       ============================================================ */
    function renderNodes(nodes) {
        if (!nodes.length) {
            nodesTable.innerHTML = `
                <tr>
                    <td colspan="4" class="loading">
                        <strong>No Nodes Configured</strong>
                        <div style="margin-top:4px; font-size:10px; color:var(--text-muted);">Add a node from Node Management.</div>
                    </td>
                </tr>
            `;
            return;
        }

        nodesTable.innerHTML = nodes.map(node => {
            const status = gateway.status(node.status);
            const isOnline = status === "online";
            const isSelected = selectedNode === node.node_id;
            const lastSeen = node.last_seen ? gateway.time(node.last_seen) : "Never";

            return `
                <tr class="${isSelected ? 'dashboard-node-selected' : ''}"
                    data-node-id="${gateway.escape(node.node_id)}"
                    style="${isSelected ? 'background: var(--brand-primary-light); border-left: 3px solid var(--brand-primary);' : ''}">
                    <td>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="width:26px; height:26px; display:flex; align-items:center; justify-content:center; border-radius:4px; background:var(--bg-surface-subtle); color:var(--text-main); font-weight:700;">
                                ⬡
                            </div>
                            <div>
                                <strong style="display:block; font-size:11px;">${gateway.escape(node.name || node.node_id)}</strong>
                                <small style="font-size:9px; color:var(--text-muted);">${gateway.escape(node.node_id)}</small>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span style="font-size:11px;">${gateway.escape(node.communication_type || 'LoRa')}</span>
                    </td>
                    <td>
                        <span class="status-pill-${isOnline ? 'online' : 'offline'}" style="font-size:9px; font-weight:700; padding:2px 6px; border-radius:4px;">
                            ${isOnline ? 'ONLINE' : 'OFFLINE'}
                        </span>
                    </td>
                    <td>
                        <span style="font-size:10px; color:var(--text-muted);">${lastSeen}</span>
                    </td>
                </tr>
            `;
        }).join("");

        populateWidgetNodeSelect();

        // Attach click listeners to rows
        nodesTable.querySelectorAll("tr[data-node-id]").forEach(row => {
            row.addEventListener("click", () => {
                const nid = row.getAttribute("data-node-id");
                if (nid && nid !== selectedNode) {
                    selectedNode = nid;
                    renderNodes(currentNodesList);
                    loadSensors(selectedNode);
                }
            });
        });
    }

    /* ============================================================
       LOAD SENSORS FOR SELECTED NODE
       ============================================================ */
    async function loadSensors(nodeId) {
        const container = document.getElementById("dashboard-sensors");
        const nodeLabel = document.getElementById("selected-node");

        const matchedNode = currentNodesList.find(n => n.node_id === nodeId);
        if (nodeLabel) {
            nodeLabel.textContent = matchedNode ? `Node: ${matchedNode.name || nodeId} (${nodeId})` : `Node: ${nodeId}`;
        }

        try {
            const data = await gateway.get(`/api/nodes/${encodeURIComponent(nodeId)}/parameters`);
            const sensors = Array.isArray(data) ? data : (data.parameters || []);
            currentSensorsList = sensors;

            // Update sensor counter on dashboard
            const sensorCountEl = document.getElementById("sensor-count");
            if (sensorCountEl) sensorCountEl.textContent = sensors.length;

            // Count alarms
            const alarmCountEl = document.getElementById("alarm-count");
            const alarms = sensors.filter(s => s.status === "alarm" || s.quality === "alarm");
            if (alarmCountEl) alarmCountEl.textContent = alarms.length;

            renderSensors(sensors);
            updateChartParameterDropdown(sensors);
            loadTelemetryHistory();

        } catch (error) {
            console.error("Failed to load sensors:", error);
            if (container) {
                container.innerHTML = '<div class="empty-state">Unable to load sensor data.</div>';
            }
        }
    }

    function renderSensors(sensors) {
        const container = document.getElementById("dashboard-sensors");
        if (!container) return;

        if (!sensors.length) {
            container.innerHTML = '<div class="empty-state">No active sensor parameters for this node.</div>';
            return;
        }

        container.innerHTML = sensors.map(s => {
            const val = s.value !== null && s.value !== undefined ? s.value : "—";
            const unit = s.unit || "";
            const isAlarm = s.status === "alarm" || s.quality === "alarm";
            const isSelected = selectedParam === s.parameter_name || selectedParam === s.name;

            return `
                <div class="sensor-card ${isSelected ? 'sensor-card-selected' : ''}"
                     data-param-name="${gateway.escape(s.parameter_name || s.name)}"
                     style="${isSelected ? 'border-color:var(--brand-primary); background:var(--brand-primary-light);' : ''}; cursor:pointer;">
                    <div class="sensor-card-name">${gateway.escape(s.parameter_name || s.name)}</div>
                    <div class="sensor-card-value" style="${isAlarm ? 'color:var(--status-alarm);' : ''}">${val} <small style="font-size:11px; font-weight:normal; color:var(--text-muted);">${unit}</small></div>
                    <div class="sensor-card-meta">Quality: <strong>${gateway.escape(s.quality || 'Good')}</strong></div>
                </div>
            `;
        }).join("");

        // Attach click listener to switch charted parameter
        container.querySelectorAll(".sensor-card").forEach(card => {
            card.addEventListener("click", () => {
                const pname = card.getAttribute("data-param-name");
                if (pname) {
                    selectedParam = pname;
                    const paramSelect = document.getElementById("chart-parameter-select");
                    if (paramSelect) paramSelect.value = pname;
                    renderSensors(currentSensorsList);
                    loadTelemetryHistory();
                }
            });
        });
    }

    /* ============================================================
       CHART PARAMETER SELECTOR & TELEMETRY ENGINE
       ============================================================ */
    function updateChartParameterDropdown(sensors) {
        const select = document.getElementById("chart-parameter-select");
        if (!select) return;

        const currentVal = select.value;
        select.innerHTML = '<option value="">Auto (First Parameter)</option>' +
            sensors.map(s => {
                const name = s.parameter_name || s.name;
                return `<option value="${gateway.escape(name)}">${gateway.escape(name)} (${gateway.escape(s.unit || '')})</option>`;
            }).join("");

        if (currentVal && sensors.some(s => (s.parameter_name || s.name) === currentVal)) {
            select.value = currentVal;
            selectedParam = currentVal;
        } else if (sensors.length > 0 && !selectedParam) {
            selectedParam = sensors[0].parameter_name || sensors[0].name;
            select.value = selectedParam;
        }
    }

    async function loadTelemetryHistory() {
        if (!selectedNode) return;

        const subtitle = document.getElementById("chart-subtitle");
        if (subtitle) {
            subtitle.textContent = `Node ${selectedNode} • Parameter: ${selectedParam || 'Auto'} • Window: ${chartTimeRange.toUpperCase()}`;
        }

        try {
            // Fetch live telemetry records from server
            const res = await gateway.get(`/api/nodes/${encodeURIComponent(selectedNode)}/telemetry/${encodeURIComponent((currentSensorsList.find(x => (x.parameter_name || x.name) === selectedParam) || currentSensorsList[0] || {}).parameter_id || "")}?limit=50`);
            const records = Array.isArray(res) ? res : (res.data || res.telemetry || []);

            // Extract points for selected parameter
            const points = [];
            records.forEach(r => {
                const timestamp = r.created_at || r.timestamp;
                let val = null;

                if (selectedParam && r.data && typeof r.data === "object") {
                    val = r.data[selectedParam];
                } else if (r.data && typeof r.data === "object") {
                    // Pick first numeric value
                    const firstKey = Object.keys(r.data)[0];
                    if (firstKey) val = r.data[firstKey];
                } else if (typeof r.value === "number") {
                    val = r.value;
                }

                if (typeof val === "number" && !isNaN(val)) {
                    points.unshift({ time: timestamp, value: val });
                }
            });

            telemetryHistoryData = points.filter(point => {
                if (!point.time) return true;
                const t = new Date(point.time).getTime();
                if (!Number.isFinite(t)) return true;
                const rangeHours = chartTimeRange === "1h" ? 1 : (chartTimeRange === "6h" ? 6 : 24);
                return (Date.now() - t) <= rangeHours * 60 * 60 * 1000;
            });

            renderTelemetryChart();

        } catch (err) {
            console.error("Telemetry history error:", err);
            renderTelemetryChart();
        }
    }

    /* ============================================================
       CANVAS TELEMETRY CHART RENDERER
       ============================================================ */
    function renderTelemetryChart() {
        if (!ctx || !canvas) return;

        // Auto-scale canvas for Retina/HiDPI screens
        const rect = canvas.parentElement.getBoundingClientRect();
        const width = Math.floor(rect.width) || 600;
        const height = 220;
        const dpr = window.devicePixelRatio || 1;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        ctx.resetTransform?.();
        ctx.scale(dpr, dpr);

        ctx.clearRect(0, 0, width, height);

        const emptyState = document.getElementById("chart-empty-state");
        if (!telemetryHistoryData.length) {
            if (emptyState) emptyState.style.display = "flex";
            return;
        } else {
            if (emptyState) emptyState.style.display = "none";
        }

        const rootStyle = getComputedStyle(document.documentElement);
        const primaryColor = rootStyle.getPropertyValue("--brand-primary").trim() || "#E87522";
        const gridColor = rootStyle.getPropertyValue("--chart-grid").trim() || "rgba(100,116,139,.18)";
        const textColor = rootStyle.getPropertyValue("--chart-text").trim() || rootStyle.getPropertyValue("--text-muted").trim() || "#64748B";

        const padding = { top: 20, right: 24, bottom: 30, left: 45 };
        const chartW = width - padding.left - padding.right;
        const chartH = height - padding.top - padding.bottom;

        // Values range
        const values = telemetryHistoryData.map(d => d.value);
        let minVal = Math.min(...values);
        let maxVal = Math.max(...values);
        if (minVal === maxVal) { minVal -= 5; maxVal += 5; }
        const range = maxVal - minVal;

        // Draw horizontal grid lines & Y-axis labels
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        ctx.fillStyle = textColor;
        ctx.font = "10px Inter, sans-serif";
        ctx.textAlign = "right";

        const gridSteps = 4;
        for (let i = 0; i <= gridSteps; i++) {
            const y = padding.top + (chartH / gridSteps) * i;
            const val = maxVal - (range / gridSteps) * i;

            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(padding.left + chartW, y);
            ctx.stroke();

            ctx.fillText(val.toFixed(1), padding.left - 8, y + 3);
        }

        // Compute points coordinates
        const coords = telemetryHistoryData.map((d, i) => {
            const x = padding.left + (chartW / (telemetryHistoryData.length - 1 || 1)) * i;
            const y = padding.top + chartH - ((d.value - minVal) / range) * chartH;
            return { x, y, val: d.value, time: d.time };
        });

        // Draw filled gradient area under curve
        const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
        gradient.addColorStop(0, hexToRgba(primaryColor, 0.35));
        gradient.addColorStop(1, hexToRgba(primaryColor, 0.0));

        ctx.beginPath();
        ctx.moveTo(coords[0].x, padding.top + chartH);
        ctx.lineTo(coords[0].x, coords[0].y);

        for (let i = 0; i < coords.length - 1; i++) {
            const cx = (coords[i].x + coords[i + 1].x) / 2;
            const cy = (coords[i].y + coords[i + 1].y) / 2;
            ctx.quadraticCurveTo(coords[i].x, coords[i].y, cx, cy);
        }
        ctx.lineTo(coords[coords.length - 1].x, coords[coords.length - 1].y);
        ctx.lineTo(coords[coords.length - 1].x, padding.top + chartH);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Draw smooth line
        ctx.beginPath();
        ctx.moveTo(coords[0].x, coords[0].y);
        for (let i = 0; i < coords.length - 1; i++) {
            const cx = (coords[i].x + coords[i + 1].x) / 2;
            const cy = (coords[i].y + coords[i + 1].y) / 2;
            ctx.quadraticCurveTo(coords[i].x, coords[i].y, cx, cy);
        }
        ctx.lineTo(coords[coords.length - 1].x, coords[coords.length - 1].y);
        ctx.strokeStyle = primaryColor;
        ctx.lineWidth = 2.5;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        ctx.stroke();

        // Draw last value highlight circle & readout
        const lastPt = coords[coords.length - 1];
        ctx.beginPath();
        ctx.arc(lastPt.x, lastPt.y, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = primaryColor;
        ctx.fill();
        ctx.strokeStyle = rootStyle.getPropertyValue("--bg-surface").trim() || "#FFFFFF";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Time labels on X axis
        ctx.fillStyle = textColor;
        ctx.textAlign = "center";
        const timeIndices = [0, Math.floor(coords.length / 2), coords.length - 1];
        timeIndices.forEach(idx => {
            const pt = coords[idx];
            if (pt) {
                const timeLabel = pt.time ? formatShortTime(pt.time) : "—";
                ctx.fillText(timeLabel, pt.x, height - 10);
            }
        });
    }

    /* ============================================================
       LOAD ACTIVITY STREAM
       ============================================================ */
    async function loadActivity() {
        const list = document.getElementById("activity-list");
        if (!list) return;

        try {
            const data = await gateway.get("/api/logs?limit=8");
            const logs = Array.isArray(data) ? data : (data.logs || []);

            if (!logs.length) {
                list.innerHTML = '<div class="loading">No recent activity.</div>';
                return;
            }

            list.innerHTML = logs.map(log => {
                const sev = (log.severity || "info").toLowerCase();
                const sevColor = sev === "error" ? "red" : (sev === "warning" ? "orange" : "green");
                const time = log.timestamp ? gateway.time(log.timestamp) : "—";

                return `
                    <div class="activity-item" style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border-subtle); font-size:11px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span class="stat-icon ${sevColor}" style="width:20px; height:20px; font-size:10px; border-radius:50%;">●</span>
                            <span style="font-weight:600;">${gateway.escape(log.source || 'GATEWAY')}</span>
                            <span style="color:var(--text-muted);">${gateway.escape(log.message)}</span>
                        </div>
                        <small style="color:var(--text-subtle); font-size:10px;">${time}</small>
                    </div>
                `;
            }).join("");

        } catch (error) {
            console.error("Activity load error:", error);
        }
    }

    /* ============================================================
       HELPERS
       ============================================================ */
    function showNoNode() {
        const container = document.getElementById("dashboard-sensors");
        if (container) container.innerHTML = '<div class="empty-state">No nodes configured.</div>';
    }

    function showDashboardError() {
        if (nodesTable) {
            nodesTable.innerHTML = '<tr><td colspan="4" class="loading">Error connecting to gateway.</td></tr>';
        }
    }

    function hexToRgba(hex, alpha) {
        let c = hex.replace("#", "");
        if (c.length === 3) c = c.split("").map(ch => ch + ch).join("");
        const num = parseInt(c, 16);
        return `rgba(${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}, ${alpha})`;
    }

    function formatShortTime(isoStr) {
        try {
            const date = new Date(isoStr);
            return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
        } catch {
            return "—";
        }
    }
});
