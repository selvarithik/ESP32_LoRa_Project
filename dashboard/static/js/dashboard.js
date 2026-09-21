"use strict";

document.addEventListener("DOMContentLoaded", function () {
    var root = document.getElementById("dashboard-console");
    if (!root) return;

    var state = {
        nodes: [],
        telemetry: {},
        graphs: {},
        customWidgets: [],
        search: "",
        nodeFilter: "",
        statusFilter: "",
        showConfig: true,
        showHidden: true,
        busy: false,
        graphBusy: false,
        refreshTimer: null,
        graphTimer: null
    };

    function esc(value) {
        if (window.gateway && typeof window.gateway.escape === "function") {
            return window.gateway.escape(String(value === null || value === undefined ? "" : value));
        }
        return String(value === null || value === undefined ? "" : value)
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    function text(id, value) {
        var el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function toast(message, type) {
        if (window.gateway && typeof window.gateway.toast === "function") {
            window.gateway.toast(message, type || "info");
        }
    }

    function formatTime(value) {
        if (!value) return "—";
        if (window.gateway && typeof window.gateway.time === "function") {
            return window.gateway.time(value);
        }
        var d = new Date(value);
        return isNaN(d.getTime()) ? String(value) : d.toLocaleString();
    }

    function formatClock(value) {
        if (!value) return "—";
        var d = new Date(value);
        return isNaN(d.getTime()) ? String(value) : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }

    function formatValue(value, decimals) {
        if (value === null || value === undefined || value === "") return "—";
        var n = Number(value);
        if (!isFinite(n)) return String(value);
        var dp = Math.max(0, Math.min(8, Number(decimals === undefined ? 2 : decimals)));
        return n.toFixed(dp);
    }

    function online(node) {
        var s = String((node && node.status) || "").toLowerCase();
        return s === "online" || s === "connected";
    }

    function parameterStatus(p) {
        var alarm = String((p && p.alarm_status) || "").toUpperCase();
        if (alarm === "HIGH" || alarm === "LOW") return "alarm";
        if (alarm === "SENSOR_ERROR") return "error";
        if (alarm === "NO_DATA") return "offline";
        var q = String((p && p.quality) || "").toUpperCase();
        if (q && q !== "GOOD") return "warning";
        var st = String((p && p.status) || "").toUpperCase();
        if (st && /WARN/.test(st)) return "warning";
        if (st && /ERROR|FAULT|FAIL/.test(st)) return "error";
        return "good";
    }

    function parameterStatusLabel(p) {
        var alarm = String((p && p.alarm_status) || "").toUpperCase();
        if (alarm === "HIGH") return "HIGH ALARM";
        if (alarm === "LOW") return "LOW ALARM";
        if (alarm === "SENSOR_ERROR") return "SENSOR ERROR";
        if (alarm === "NO_DATA") return "NO DATA";
        var q = String((p && p.quality) || "").toUpperCase();
        if (q && q !== "GOOD") return q;
        var st = String((p && p.status) || "").toUpperCase();
        return st || "NORMAL";
    }

    function normalizeNodes(data) {
        return Array.isArray(data) ? data : ((data && data.nodes) || []);
    }

    function normalizeParameters(data) {
        return Array.isArray(data) ? data : ((data && data.parameters) || []);
    }

    async function getJson(url, options) {
        var response = await fetch(url, Object.assign({
            credentials: "same-origin",
            cache: "no-store"
        }, options || {}));

        var type = response.headers.get("content-type") || "";
        var body = type.indexOf("application/json") >= 0
            ? await response.json()
            : { success: response.ok, error: await response.text() };

        if (!response.ok || (body && body.success === false)) {
            throw new Error((body && body.error) || ("Request failed: " + response.status));
        }
        return body;
    }

    function populateNodeFilter() {
        var select = document.getElementById("dashboard-node-filter");
        if (!select) return;

        var current = state.nodeFilter;
        select.innerHTML = '<option value="">All nodes</option>';

        state.nodes.forEach(function (node) {
            var opt = document.createElement("option");
            opt.value = node.node_id;
            opt.textContent = (node.name || node.node_id) + " · " + node.node_id;
            select.appendChild(opt);
        });

        select.value = current;
    }

    async function loadNodes() {
        var data = await getJson("/api/nodes");
        state.nodes = normalizeNodes(data);
        populateNodeFilter();
    }

    async function loadNodeTelemetry(node, includeGraphs) {
        try {
            var data = await getJson("/api/nodes/" + encodeURIComponent(node.node_id) + "/parameters/latest");
            var parameters = normalizeParameters(data);
            state.telemetry[node.node_id] = parameters;

            if (includeGraphs) {
                var graphParams = parameters.filter(function (p) {
                    return p.enabled !== false && Boolean(p.graph_enabled);
                });
                await Promise.allSettled(graphParams.map(function (p) {
                    return loadGraph(node.node_id, p);
                }));
            }
        } catch (error) {
            console.error("Dashboard telemetry error for " + node.node_id, error);
            state.telemetry[node.node_id] = [];
        }
    }

    async function loadGraph(nodeId, parameter) {
        var key = nodeId + "::" + parameter.parameter_id;

        try {
            var cfgResponse = await getJson(
                "/api/nodes/" + encodeURIComponent(nodeId) +
                "/parameters/" + encodeURIComponent(parameter.parameter_id) + "/graph"
            );

            var config = (cfgResponse && cfgResponse.graph) || {};
            var maxPoints = Number(config.max_points || 180);
            if (!isFinite(maxPoints)) maxPoints = 180;
            maxPoints = Math.max(30, Math.min(300, maxPoints));

            var historyResponse = await getJson(
                "/api/nodes/" + encodeURIComponent(nodeId) +
                "/telemetry/" + encodeURIComponent(parameter.parameter_id) +
                "?limit=" + maxPoints
            );

            state.graphs[key] = {
                config: config,
                data: Array.isArray(historyResponse && historyResponse.data)
                    ? historyResponse.data : []
            };
        } catch (error) {
            console.error("Dashboard graph error for " + nodeId + "/" + parameter.parameter_id, error);
            state.graphs[key] = { config: {}, data: [], error: error.message };
        }
    }

    async function loadTelemetry(includeGraphs) {
        await Promise.allSettled(state.nodes.map(function (node) {
            return loadNodeTelemetry(node, includeGraphs);
        }));
    }

    async function loadActivity() {
        try {
            var response = await getJson("/api/logs?limit=8");
            var logs = Array.isArray(response) ? response : ((response && response.logs) || []);
            renderActivity(logs);
            if (logs[0] && logs[0].timestamp) {
                text("dashboard-server-time", formatClock(logs[0].timestamp));
            }
        } catch (error) {
            console.error("Dashboard activity error", error);
            var box = document.getElementById("activity-list");
            if (box) box.innerHTML = '<div class="dashboard-empty">Unable to load activity.</div>';
        }
    }

    async function loadServerStatus() {
        try {
            var response = await getJson("/api/status");
            var stateName = String(response.status || "unknown").toUpperCase();
            text("dashboard-gateway-state", stateName);
            text("dashboard-gateway-sub",
                String(response.server || "Gateway server") +
                " · " + String(response.nodes === undefined ? state.nodes.length : response.nodes) +
                " configured nodes"
            );

            var dot = document.getElementById("dashboard-gateway-dot");
            if (dot) {
                if (String(response.status || "").toLowerCase() === "online") {
                    dot.style.background = "var(--d-lime)";
                    dot.style.boxShadow = "0 0 0 4px var(--d-lime-soft)";
                } else {
                    dot.style.background = "var(--d-red)";
                    dot.style.boxShadow = "0 0 0 4px var(--d-red-soft)";
                }
            }
        } catch (error) {
            text("dashboard-gateway-state", "UNAVAILABLE");
            text("dashboard-gateway-sub", "Server status endpoint unavailable.");
        }
    }

    function allParameters() {
        var result = [];
        state.nodes.forEach(function (node) {
            (state.telemetry[node.node_id] || []).forEach(function (p) {
                result.push({ node: node, parameter: p });
            });
        });
        return result;
    }

    function nodeHasProblem(node) {
        if (!online(node) && node.enabled !== false) return true;
        return (state.telemetry[node.node_id] || []).some(function (p) {
            var k = parameterStatus(p);
            return k === "alarm" || k === "error";
        });
    }

    function matches(node) {
        if (state.nodeFilter && node.node_id !== state.nodeFilter) return false;

        if (state.statusFilter === "online" && !online(node)) return false;
        if (state.statusFilter === "offline" && (online(node) || node.enabled === false)) return false;
        if (state.statusFilter === "alarm" && !nodeHasProblem(node)) return false;

        var q = state.search.toLowerCase().trim();
        if (!q) return true;

        var nodeText = [
            node.node_id, node.name, node.node_address, node.mcu_family,
            node.mcu_model, node.hardware_revision, node.firmware_version,
            node.communication_type, JSON.stringify(node.communication_config || {})
        ].join(" ").toLowerCase();

        if (nodeText.indexOf(q) >= 0) return true;

        return (state.telemetry[node.node_id] || []).some(function (p) {
            return [
                p.parameter_id, p.parameter_name, p.parameter_type,
                p.data_type, p.unit, p.sensor_id, p.description
            ].join(" ").toLowerCase().indexOf(q) >= 0;
        });
    }

    function nodeConfigFields(node) {
        var fields = [
            ["Node ID", node.node_id],
            ["Name", node.name],
            ["Address", node.node_address],
            ["MCU Family", node.mcu_family],
            ["MCU Model", node.mcu_model],
            ["Hardware", node.hardware_revision],
            ["Firmware", node.firmware_version],
            ["Communication", node.communication_type],
            ["Enabled", node.enabled === false ? "NO" : "YES"],
            ["Status", String(node.status || "—").toUpperCase()],
            ["Last Seen", formatTime(node.last_seen)],
            ["Created", formatTime(node.created_at)],
            ["Updated", formatTime(node.updated_at)]
        ];

        var html = fields.map(function (field) {
            return '<div class="dashboard-inspector-field">' +
                '<span>' + esc(field[0]) + '</span>' +
                '<strong title="' + esc(field[1] || "—") + '">' + esc(field[1] || "—") + '</strong>' +
                '</div>';
        }).join("");

        if (node.communication_config) {
            var prettyConfig = "";
            try {
                prettyConfig = JSON.stringify(node.communication_config, null, 2);
            } catch (_) {
                prettyConfig = String(node.communication_config);
            }
            html += '<details class="dashboard-config-details">' +
                '<summary>Communication Config</summary>' +
                '<pre>' + esc(prettyConfig) + '</pre>' +
                '</details>';
        }

        return html;
    }

    function sensorCard(p) {
        var kind = parameterStatus(p);
        var displayOff = p.display_enabled === false;
        var value = p.value !== null && p.value !== undefined && p.value !== "" ? p.value : p.text_value;
        var valueText = value === null || value === undefined || value === ""
            ? "—"
            : (isFinite(Number(value)) ? formatValue(value, p.decimal_places) : String(value));

        var range = (p.min_value !== null && p.min_value !== undefined) ||
                    (p.max_value !== null && p.max_value !== undefined)
            ? String(p.min_value === null || p.min_value === undefined ? "—" : p.min_value) +
              " … " +
              String(p.max_value === null || p.max_value === undefined ? "—" : p.max_value)
            : "—";

        var alarms = p.alarm_enabled
            ? String(p.low_alarm === null || p.low_alarm === undefined ? "—" : p.low_alarm) +
              " … " +
              String(p.high_alarm === null || p.high_alarm === undefined ? "—" : p.high_alarm)
            : "Disabled";

        return '<article class="dashboard-sensor-card ' + kind + (displayOff ? " hidden-param" : "") + '">' +
            '<div class="dashboard-sensor-top">' +
                '<div class="dashboard-sensor-name" title="' + esc(p.parameter_name || p.parameter_id) + '">' + esc(p.parameter_name || p.parameter_id) + '</div>' +
                '<div class="dashboard-sensor-badge">' + esc(displayOff ? "DISPLAY OFF" : (p.parameter_id || "PARAM")) + '</div>' +
            '</div>' +
            '<div class="dashboard-sensor-value">' + esc(valueText) + '<span>' + esc(p.unit || "") + '</span></div>' +
            '<div class="dashboard-sensor-status ' + kind + '"><i></i>' + esc(parameterStatusLabel(p)) + '</div>' +
            '<div class="dashboard-sensor-meta">' +
                '<div><span>Sensor ID</span><strong>' + esc(p.sensor_id || "—") + '</strong></div>' +
                '<div><span>Type</span><strong>' + esc(p.parameter_type || "—") + '</strong></div>' +
                '<div><span>Data</span><strong>' + esc(p.data_type || "—") + '</strong></div>' +
                '<div><span>Updated</span><strong>' + esc(formatTime(p.timestamp)) + '</strong></div>' +
                '<div><span>Range</span><strong>' + esc(range) + '</strong></div>' +
                '<div><span>Alarm</span><strong>' + esc(alarms) + '</strong></div>' +
                '<div><span>Quality</span><strong>' + esc(p.quality || "—") + '</strong></div>' +
                '<div><span>Alarm State</span><strong>' + esc(p.alarm_status || "—") + '</strong></div>' +
                '<div><span>Precision</span><strong>' + esc(p.decimal_places === null || p.decimal_places === undefined ? "—" : p.decimal_places + " dp") + '</strong></div>' +
                '<div><span>Graph</span><strong>' + esc(p.graph_enabled ? "ENABLED" : "OFF") + '</strong></div>' +
                '<div><span>Display</span><strong>' + esc(p.display_enabled === false ? "OFF" : "ON") + '</strong></div>' +
                '<div><span>Description</span><strong title="' + esc(p.description || "—") + '">' + esc(p.description || "—") + '</strong></div>' +
            '</div>' +
        '</article>';
    }

    function graphSvg(nodeId, p) {
        var graph = state.graphs[nodeId + "::" + p.parameter_id];
        var data = graph && Array.isArray(graph.data) ? graph.data.filter(function (x) {
            return x && isFinite(Number(x.value)) && x.timestamp;
        }) : [];

        if (!data.length) {
            return '<article class="dashboard-graph-card">' +
                '<div class="dashboard-graph-head"><div class="dashboard-graph-title">' +
                '<strong>' + esc(p.parameter_name || p.parameter_id) + '</strong>' +
                '<span>Graph enabled · waiting for numeric telemetry</span></div>' +
                '<div class="dashboard-graph-stat">LIVE</div></div>' +
                '<div class="dashboard-graph-empty">No historical numeric samples available.</div>' +
                '</article>';
        }

        var points = data.slice(-160).map(function (x) {
            return { time: new Date(x.timestamp).getTime(), value: Number(x.value) };
        }).filter(function (x) { return isFinite(x.time) && isFinite(x.value); });

        if (!points.length) {
            return '<article class="dashboard-graph-card"><div class="dashboard-graph-empty">No plottable telemetry samples.</div></article>';
        }

        var values = points.map(function (x) { return x.value; });
        var min = Math.min.apply(null, values);
        var max = Math.max.apply(null, values);
        var avg = values.reduce(function (a,b) { return a + b; }, 0) / values.length;

        var cfg = (graph && graph.config) || {};
        var minY = cfg.auto_scale === false && cfg.y_min !== null && cfg.y_min !== undefined ? Number(cfg.y_min) : min;
        var maxY = cfg.auto_scale === false && cfg.y_max !== null && cfg.y_max !== undefined ? Number(cfg.y_max) : max;

        if (!isFinite(minY)) minY = min;
        if (!isFinite(maxY)) maxY = max;
        if (minY === maxY) {
            var padSame = Math.abs(minY || 1) * 0.08 || 1;
            minY -= padSame; maxY += padSame;
        } else {
            var pad = (maxY - minY) * 0.08;
            minY -= pad; maxY += pad;
        }

        var w = 760, h = 148, left = 36, right = 10, top = 10, bottom = 22;
        var iw = w - left - right, ih = h - top - bottom;
        var firstT = points[0].time, lastT = points[points.length - 1].time;
        var span = Math.max(1, lastT - firstT);

        var path = points.map(function (pt, idx) {
            var x = left + ((pt.time - firstT) / span) * iw;
            var y = top + (1 - ((pt.value - minY) / Math.max(0.000001, maxY - minY))) * ih;
            return (idx === 0 ? "M " : "L ") + x.toFixed(1) + " " + y.toFixed(1);
        }).join(" ");

        var grid = [0, 0.5, 1].map(function (frac) {
            var y = top + frac * ih;
            return '<line x1="' + left + '" y1="' + y.toFixed(1) + '" x2="' + (w-right) + '" y2="' + y.toFixed(1) + '" stroke="currentColor" stroke-width="1"/>';
        }).join("");

        var labels =
            '<text x="' + (left-7) + '" y="' + (top+4) + '" text-anchor="end" fill="currentColor" font-size="8">' + esc(formatValue(max, p.decimal_places)) + '</text>' +
            '<text x="' + (left-7) + '" y="' + (top+ih/2+3) + '" text-anchor="end" fill="currentColor" font-size="8">' + esc(formatValue(avg, p.decimal_places)) + '</text>' +
            '<text x="' + (left-7) + '" y="' + (top+ih+3) + '" text-anchor="end" fill="currentColor" font-size="8">' + esc(formatValue(min, p.decimal_places)) + '</text>';

        return '<article class="dashboard-graph-card">' +
            '<div class="dashboard-graph-head"><div class="dashboard-graph-title">' +
                '<strong>' + esc(p.parameter_name || p.parameter_id) + '</strong>' +
                '<span>' + esc((cfg.time_range || "configured range")) + ' · ' + points.length + ' samples</span>' +
            '</div><div class="dashboard-graph-stat">' + esc(formatValue(points[points.length-1].value, p.decimal_places)) + ' ' + esc(p.unit || "") + '</div></div>' +
            '<svg class="dashboard-graph-svg" viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' + esc(p.parameter_name || p.parameter_id) + ' telemetry graph">' +
                grid + labels +
                '<path d="' + path + '" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>' +
            '</svg>' +
            '<div class="dashboard-graph-foot"><span>MIN ' + esc(formatValue(min, p.decimal_places)) + '</span>' +
                '<span>AVG ' + esc(formatValue(avg, p.decimal_places)) + '</span>' +
                '<span>MAX ' + esc(formatValue(max, p.decimal_places)) + '</span></div>' +
            '</article>';
    }

    function renderNodes() {
        var container = document.getElementById("dashboard-node-list");
        if (!container) return;

        var filtered = state.nodes.filter(matches);

        if (!filtered.length) {
            container.innerHTML = '<div class="dashboard-node-empty">No configured nodes match the current filters.</div>';
            return;
        }

        container.innerHTML = filtered.map(function (node) {
            var params = (state.telemetry[node.node_id] || []).filter(function (p) {
                return p && p.enabled !== false;
            });

            var shown = state.showHidden
                ? params
                : params.filter(function (p) { return p.display_enabled !== false; });

            var cards = shown.map(sensorCard).join("");
            if (!cards) cards = '<div class="dashboard-node-empty">No enabled sensor parameters configured for this node.</div>';

            var graphParams = params.filter(function (p) { return Boolean(p.graph_enabled); });
            var graphs = graphParams.map(function (p) { return graphSvg(node.node_id, p); }).join("");

            var nodeOnline = online(node);

            return '<article class="dashboard-node" data-node-id="' + esc(node.node_id) + '">' +
                '<header class="dashboard-node-head">' +
                    '<div>' +
                        '<div class="dashboard-node-title-row">' +
                            '<span class="dashboard-node-status ' + (nodeOnline ? "online" : "") + '"></span>' +
                            '<div class="dashboard-node-name" title="' + esc(node.name || node.node_id) + '">' + esc(node.name || node.node_id) + '</div>' +
                        '</div>' +
                        '<div class="dashboard-node-id">' + esc(node.node_id) + '</div>' +
                    '</div>' +
                    '<div class="dashboard-node-config">' +
                        '<div class="dashboard-node-config-item"><span>Address</span><strong>' + esc(node.node_address || "—") + '</strong></div>' +
                        '<div class="dashboard-node-config-item"><span>MCU</span><strong>' + esc([node.mcu_family,node.mcu_model].filter(Boolean).join(" / ") || "—") + '</strong></div>' +
                        '<div class="dashboard-node-config-item"><span>Firmware</span><strong>' + esc(node.firmware_version || "—") + '</strong></div>' +
                        '<div class="dashboard-node-config-item"><span>Hardware</span><strong>' + esc(node.hardware_revision || "—") + '</strong></div>' +
                        '<div class="dashboard-node-config-item"><span>Communication</span><strong>' + esc(node.communication_type || "—") + '</strong></div>' +
                        '<div class="dashboard-node-config-item"><span>Last Seen</span><strong>' + esc(formatTime(node.last_seen)) + '</strong></div>' +
                    '</div>' +
                    '<button class="dashboard-node-toggle" type="button" data-toggle-node="' + esc(node.node_id) + '">Collapse</button>' +
                '</header>' +
                '<div class="dashboard-node-body">' +
                    (state.showConfig
                        ? '<div class="dashboard-node-inspector"><div class="dashboard-node-inspector-head">Node Configuration</div><div class="dashboard-node-inspector-grid">' + nodeConfigFields(node) + '</div></div>'
                        : "") +
                    '<div class="dashboard-node-sensors">' + cards + '</div>' +
                    (graphs ? '<div class="dashboard-node-graph-list">' + graphs + '</div>' : "") +
                '</div>' +
            '</article>';
        }).join("");
    }

    function renderFleet() {
        var box = document.getElementById("dashboard-fleet-list");
        if (!box) return;

        var sorted = state.nodes.slice().sort(function (a,b) {
            return Number(online(b)) - Number(online(a));
        });

        if (!sorted.length) {
            box.innerHTML = '<div class="dashboard-empty">No nodes configured.</div>';
            return;
        }

        box.innerHTML = sorted.slice(0, 12).map(function (node) {
            return '<div class="dashboard-health-row">' +
                '<span class="dashboard-health-dot ' + (online(node) ? "" : "offline") + '"></span>' +
                '<div class="dashboard-row-main"><strong>' + esc(node.name || node.node_id) + '</strong>' +
                '<span>' + esc(node.node_id) + ' · ' + esc(node.communication_type || "—") + '</span></div>' +
                '<div class="dashboard-row-value">' + (online(node) ? "ONLINE" : "OFFLINE") + '</div>' +
                '</div>';
        }).join("");
    }

    function renderProblems() {
        var box = document.getElementById("dashboard-alert-list");
        if (!box) return;

        var problems = [];

        state.nodes.forEach(function (node) {
            if (!online(node) && node.enabled !== false) {
                problems.push({
                    kind: "error",
                    title: node.name || node.node_id,
                    detail: "Node offline · last seen " + formatTime(node.last_seen),
                    value: "OFFLINE"
                });
            }

            (state.telemetry[node.node_id] || []).forEach(function (p) {
                var k = parameterStatus(p);
                if (k === "alarm" || k === "error") {
                    problems.push({
                        kind: k,
                        title: (node.name || node.node_id) + " · " + (p.parameter_name || p.parameter_id),
                        detail: parameterStatusLabel(p),
                        value: p.value === null || p.value === undefined ? (p.text_value || "—") : p.value
                    });
                }
            });
        });

        if (!problems.length) {
            box.innerHTML = '<div class="dashboard-empty">No active problems detected from live node/sensor state.</div>';
            return;
        }

        box.innerHTML = problems.slice(0, 15).map(function (p) {
            return '<div class="dashboard-alert-row">' +
                '<span class="dashboard-alert-icon ' + (p.kind === "error" ? "error" : "") + '">!</span>' +
                '<div class="dashboard-row-main"><strong>' + esc(p.title) + '</strong><span>' + esc(p.detail) + '</span></div>' +
                '<div class="dashboard-row-value">' + esc(p.value) + '</div>' +
                '</div>';
        }).join("");
    }

    function renderActivity(logs) {
        var box = document.getElementById("activity-list");
        if (!box) return;

        if (!logs.length) {
            box.innerHTML = '<div class="dashboard-empty">No log records available.</div>';
            return;
        }

        box.innerHTML = logs.slice(0, 8).map(function (log) {
            var severity = String(log.severity || log.level || "INFO").toUpperCase();
            var source = String(log.source || log.node_id || "SYSTEM");
            var message = String(log.message || log.text || "—");
            return '<div class="dashboard-event-row">' +
                '<span class="dashboard-event-dot"></span>' +
                '<div class="dashboard-row-main"><strong>' + esc(source) + ' · ' + esc(severity) + '</strong><span>' + esc(message) + '</span></div>' +
                '<div class="dashboard-row-value">' + esc(formatClock(log.timestamp || log.created_at)) + '</div>' +
                '</div>';
        }).join("");
    }

    function updateCounters() {
        var onlineCount = state.nodes.filter(online).length;
        var paramCount = 0;
        var problemCount = 0;

        state.nodes.forEach(function (node) {
            (state.telemetry[node.node_id] || []).forEach(function (p) {
                if (p.enabled === false) return;
                paramCount += 1;
                var k = parameterStatus(p);
                if (k === "alarm" || k === "error") problemCount += 1;
            });
        });

        text("total-nodes", state.nodes.length);
        text("online-nodes", onlineCount);
        text("sensor-count", paramCount);
        text("alarm-count", problemCount);

        text("fleet-online", onlineCount);
        text("fleet-offline", state.nodes.filter(function (n) { return n.enabled !== false && !online(n); }).length);
        text("fleet-disabled", state.nodes.filter(function (n) { return n.enabled === false; }).length);
    }

    function loadLayout() {
        try {
            var data = JSON.parse(localStorage.getItem("gateway_dashboard_v4_layout") || "{}");
            document.querySelectorAll("#widgetToggleList input[data-target-widget]").forEach(function (input) {
                var target = document.getElementById(input.getAttribute("data-target-widget"));
                if (typeof data[input.getAttribute("data-target-widget")] === "boolean") {
                    input.checked = data[input.getAttribute("data-target-widget")];
                    if (target) target.style.display = input.checked ? "" : "none";
                }
            });
        } catch (error) {}
    }

    function openDrawer() {
        var drawer = document.getElementById("widget-drawer");
        var overlay = document.getElementById("widget-drawer-overlay");
        if (!drawer || !overlay) return;
        drawer.classList.add("open");
        overlay.classList.add("open");
        drawer.setAttribute("aria-hidden", "false");
    }

    function closeDrawer() {
        var drawer = document.getElementById("widget-drawer");
        if (drawer) drawer.classList.remove("open");
        var overlay = document.getElementById("widget-drawer-overlay");
        if (overlay) overlay.classList.remove("open");
        if (drawer) drawer.setAttribute("aria-hidden", "true");
    }

    function saveLayout() {
        var result = {};
        document.querySelectorAll("#widgetToggleList input[data-target-widget]").forEach(function (input) {
            var targetId = input.getAttribute("data-target-widget");
            result[targetId] = Boolean(input.checked);
            var target = document.getElementById(targetId);
            if (target) target.style.display = input.checked ? "" : "none";
        });
        localStorage.setItem("gateway_dashboard_v4_layout", JSON.stringify(result));
        toast("Dashboard layout saved.", "success");
    }

    function resetLayout() {
        localStorage.removeItem("gateway_dashboard_v4_layout");
        document.querySelectorAll("#widgetToggleList input[data-target-widget]").forEach(function (input) {
            input.checked = true;
            var target = document.getElementById(input.getAttribute("data-target-widget"));
            if (target) target.style.display = "";
        });
        toast("Dashboard layout reset.", "info");
    }

    function renderCustomWidgets() {
        var box = document.getElementById("custom-sensor-widgets");
        if (!box) return;

        if (!state.customWidgets.length) {
            box.innerHTML = '<div class="dashboard-empty">No custom widgets configured.</div>';
            return;
        }

        box.innerHTML = state.customWidgets.map(function (widget) {
            var found = allParameters().find(function (item) {
                return item.node.node_id === widget.nodeId &&
                    (String(item.parameter.parameter_id) === String(widget.parameter) ||
                     String(item.parameter.parameter_name) === String(widget.parameter));
            });
            var p = found && found.parameter;
            return '<article class="dashboard-custom-card">' +
                '<header><div><strong>' + esc(widget.name || widget.parameter) + '</strong>' +
                '<div style="margin-top:3px;color:var(--d-dim);font-size:8px">' + esc(widget.nodeId) + '</div></div>' +
                '<button type="button" data-delete-custom-widget="' + esc(widget.id) + '" aria-label="Delete widget">×</button></header>' +
                '<div class="custom-value">' + esc(p && p.value !== null && p.value !== undefined ? formatValue(p.value,p.decimal_places) : "—") +
                ' <span style="font-size:9px;color:var(--d-muted)">' + esc((p && p.unit) || "") + '</span></div>' +
                '</article>';
        }).join("");
    }

    function loadCustomWidgets() {
        try {
            var data = JSON.parse(localStorage.getItem("gateway_custom_sensor_widgets") || "[]");
            state.customWidgets = Array.isArray(data) ? data : [];
        } catch (error) {
            state.customWidgets = [];
        }
        renderCustomWidgets();
    }

    function saveCustomWidgets() {
        localStorage.setItem("gateway_custom_sensor_widgets", JSON.stringify(state.customWidgets));
    }

    function addCustomWidget() {
        if (!state.nodes.length) {
            toast("No nodes are configured.", "warning");
            return;
        }

        var nodeId = window.prompt(
            "Node ID:\n\n" + state.nodes.map(function (n) { return n.node_id + " — " + (n.name || ""); }).join("\n"),
            state.nodes[0].node_id
        );
        if (!nodeId) return;

        var sensors = state.telemetry[nodeId] || [];
        if (!sensors.length) {
            toast("That node has no enabled parameters.", "warning");
            return;
        }

        var parameterId = window.prompt(
            "Parameter ID:\n\n" + sensors.map(function (p) { return p.parameter_id + " — " + p.parameter_name; }).join("\n"),
            sensors[0].parameter_id
        );
        if (!parameterId) return;

        var parameter = sensors.find(function (p) { return String(p.parameter_id) === String(parameterId); });
        if (!parameter) {
            toast("Parameter not found.", "error");
            return;
        }

        var name = window.prompt("Widget name:", parameter.parameter_name || parameter.parameter_id);
        state.customWidgets.push({
            id: "dashboard-widget-" + Date.now(),
            name: name || parameter.parameter_name || parameter.parameter_id,
            nodeId: nodeId,
            parameter: parameterId
        });
        saveCustomWidgets();
        renderCustomWidgets();
        toast("Widget added.", "success");
    }

    async function refreshDashboard(showToastFlag, withGraphs) {
        if (state.busy) return;
        state.busy = true;

        var indicator = document.getElementById("dashboard-live-indicator");
        try {
            await loadNodes();
            await loadTelemetry(Boolean(withGraphs));
            updateCounters();
            renderNodes();
            renderFleet();
            renderProblems();
            renderCustomWidgets();
            await Promise.allSettled([loadServerStatus(), loadActivity()]);
            text("dashboard-last-refresh", formatClock(new Date().toISOString()));
            if (indicator) indicator.style.opacity = "1";
            if (showToastFlag) toast("Dashboard refreshed.", "success");
        } catch (error) {
            console.error("Dashboard refresh error:", error);
            var box = document.getElementById("dashboard-node-list");
            if (box) box.innerHTML = '<div class="dashboard-node-empty">Unable to load dashboard data: ' + esc(error.message) + '</div>';
            if (indicator) indicator.style.opacity = ".55";
            if (showToastFlag) toast("Dashboard data could not be loaded.", "error");
        } finally {
            state.busy = false;
        }
    }

    async function refreshGraphs() {
        if (state.graphBusy || document.hidden) return;
        state.graphBusy = true;
        try {
            await loadTelemetry(true);
            renderNodes();
            renderCustomWidgets();
        } finally {
            state.graphBusy = false;
        }
    }

    function startTimers() {
        stopTimers();
        state.refreshTimer = setInterval(function () {
            refreshDashboard(false, false);
        }, 2000);

        state.graphTimer = setInterval(function () {
            refreshGraphs();
        }, 10000);
    }

    function stopTimers() {
        if (state.refreshTimer) clearInterval(state.refreshTimer);
        if (state.graphTimer) clearInterval(state.graphTimer);
        state.refreshTimer = null;
        state.graphTimer = null;
    }

    function bind() {
        document.getElementById("dashboard-refresh")?.addEventListener("click", function () {
            refreshDashboard(true, true);
        });

        document.getElementById("dashboard-search")?.addEventListener("input", function (e) {
            state.search = e.target.value || "";
            renderNodes();
        });

        document.getElementById("dashboard-node-filter")?.addEventListener("change", function (e) {
            state.nodeFilter = e.target.value || "";
            renderNodes();
        });

        document.getElementById("dashboard-status-filter")?.addEventListener("change", function (e) {
            state.statusFilter = e.target.value || "";
            renderNodes();
        });

        document.getElementById("dashboard-show-config")?.addEventListener("click", function (e) {
            state.showConfig = !state.showConfig;
            e.currentTarget.classList.toggle("active", state.showConfig);
            renderNodes();
        });

        document.getElementById("dashboard-show-hidden")?.addEventListener("click", function (e) {
            state.showHidden = !state.showHidden;
            e.currentTarget.classList.toggle("active", state.showHidden);
            renderNodes();
        });

        document.getElementById("dashboard-customize-btn")?.addEventListener("click", openDrawer);
        document.getElementById("close-widget-drawer")?.addEventListener("click", closeDrawer);
        document.getElementById("widget-drawer-overlay")?.addEventListener("click", closeDrawer);
        document.getElementById("save-widgets-btn")?.addEventListener("click", function () {
            saveLayout();
            closeDrawer();
        });
        document.getElementById("reset-widgets-btn")?.addEventListener("click", resetLayout);
        document.getElementById("add-sensor-widget-inline")?.addEventListener("click", addCustomWidget);

        document.getElementById("custom-sensor-widgets")?.addEventListener("click", function (e) {
            var button = e.target.closest("[data-delete-custom-widget]");
            if (!button) return;
            state.customWidgets = state.customWidgets.filter(function (w) {
                return w.id !== button.getAttribute("data-delete-custom-widget");
            });
            saveCustomWidgets();
            renderCustomWidgets();
            toast("Widget removed.", "info");
        });

        document.getElementById("dashboard-node-list")?.addEventListener("click", function (e) {
            var button = e.target.closest("[data-toggle-node]");
            if (!button) return;
            var body = button.closest(".dashboard-node")?.querySelector(".dashboard-node-body");
            if (!body) return;
            var collapsed = body.style.display === "none";
            body.style.display = collapsed ? "" : "none";
            button.textContent = collapsed ? "Collapse" : "Expand";
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closeDrawer();
        });

        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                stopTimers();
            } else {
                refreshDashboard(false, true).then(startTimers);
            }
        });
    }

    bind();
    loadLayout();
    loadCustomWidgets();
    refreshDashboard(false, true).then(startTimers);
});
