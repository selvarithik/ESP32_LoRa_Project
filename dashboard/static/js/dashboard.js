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
        showConfig: false,
        showHidden: true,
        busy: false,
        graphBusy: false,
        refreshTimer: null,
        graphTimer: null,
        history: {},
        snapshotPending: false
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
        return SensorUI.connection(node).online;
    }

    function parameterStatus(p) {
        if (!p || !p.timestamp) return "offline";
        if (Date.now() - new Date(p.timestamp).getTime() > SensorUI.freshnessTimeout(p) * 1000) return "stale";
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
        if (!p || !p.timestamp) return "NO DATA";
        if (parameterStatus(p) === "stale") return "STALE";
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
            cache: "no-store",
            signal: AbortSignal.timeout(12000)
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

        var signature = JSON.stringify(state.nodes.map(n => [n.node_id, n.name]));
        if (select.dataset.options === signature) return;
        select.dataset.options = signature;
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
                "?hours=1"
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
            return k === "alarm" || k === "error" || k === "stale";
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
        var node = state.nodes.find(n => n.node_id === p._nodeId);
        return SensorUI.card(p, node, state.graphs[p._nodeId + "::" + p.parameter_id]?.data || []);
    }

    var widgetPresets = {
        auto: ["Automatic", ""],
        pressure: ["Pressure", "M4 17a9 9 0 1 1 16 0M12 13l4-5M6 17h12"],
        flow: ["Flow rate", "M3 7h14l-3-3M17 7l-3 3M21 17H7l3-3M7 17l3 3"],
        level: ["Tank level", "M5 3v18h14V3M5 13h14M8 16h8"],
        soil: ["Soil moisture", "M3 20h18M12 20V9M12 14C4 14 4 5 4 5c8 0 8 9 8 9M12 10c0-7 8-7 8-7s0 7-8 7"],
        ph: ["pH", "M9 3h6M10 3v7l-6 9v2h16v-2l-6-9V3M7 16h10"],
        light: ["Light / illuminance", "M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0"],
        gas: ["Gas / CO2", "M4 15h12a4 4 0 1 0-4-4M3 10h4a3 3 0 1 0-3-3M5 19h11"],
        vibration: ["Vibration", "M2 12h3l3-7 4 14 4-14 3 7h3"],
        rpm: ["Motor / RPM", "M12 10V3c7 0 9 6 2 9h7c0 7-6 9-9 2v7c-7 0-9-6-2-9H3c0-7 6-9 9-2"],
        location: ["GPS / position", "M12 22s8-8 8-13a8 8 0 1 0-16 0c0 5 8 13 8 13M15 9a3 3 0 1 1-6 0 3 3 0 0 1 6 0"]
    };
    function telemetryIcon(p) {
        var text = [p.parameter_id, p.parameter_name, p.parameter_type, p.unit].join(" ").toLowerCase();
        var path = '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4"/>';
        if (/temp|celsius|heat/.test(text)) path = '<path d="M9 14.5V5a3 3 0 0 1 6 0v9.5a5 5 0 1 1-6 0Z"/><path d="M12 9v8"/><circle cx="12" cy="18" r="1"/>';
        else if (/humid|moist|water|rh/.test(text)) path = '<path d="M12 3c-2 4-7 8-7 12a7 7 0 0 0 14 0c0-4-5-8-7-12Z"/><path d="M8 15a4 4 0 0 0 4 4"/>';
        else if (/batt|charge/.test(text)) path = '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 10v4M6 10v4m4-4v4m4-4v4"/>';
        else if (/volt|power|current/.test(text)) path = '<path d="m13 2-9 12h7l-1 8 10-13h-8l1-7Z"/>';
        else if (/rssi|signal|snr|radio/.test(text)) path = '<path d="M4 20v-3m5 3v-7m5 7V9m5 11V4"/>';
        else if (/packet|count/.test(text)) path = '<path d="m12 3 9 5v9l-9 5-9-5V8l9-5Zm-9 5 9 5 9-5M12 13v9"/>';
        var preset = p.widgetType || Object.keys(widgetPresets).find(key => key !== "auto" && new RegExp(key === "light" ? "light|lux" : key === "location" ? "gps|position|location" : key === "rpm" ? "rpm|motor|speed" : key === "gas" ? "gas|co2" : key).test(text));
        if (preset && widgetPresets[preset]?.[1]) path = '<path d="' + widgetPresets[preset][1] + '"/>';
        return '<svg viewBox="0 0 24 24" focusable="false">' + path + '</svg>';
    }

    function sparklineSvg(p) {
        var samples = state.history[p._nodeId + "::" + p.parameter_id] || [];
        if (samples.length < 2) {
            return '<div class="dashboard-sparkline is-empty" aria-hidden="true"><span></span></div>';
        }

        var min = Math.min.apply(null, samples), max = Math.max.apply(null, samples);
        var points = samples.map(function (value, i) {
            return (i * 84 / (samples.length - 1)).toFixed(1) + "," + (max === min ? 21 : 36 - (value - min) / (max - min) * 30).toFixed(1);
        });
        return '<svg class="dashboard-sparkline" viewBox="0 0 84 42" aria-hidden="true" focusable="false">' +
            '<polyline points="' + points.join(" ") + '"></polyline>' +
            '</svg>';
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
            '<text x="' + (left-7) + '" y="' + (top+4) + '" text-anchor="end" fill="currentColor" font-size="8">' + esc(formatValue(maxY, p.decimal_places)) + '</text>' +
            '<text x="' + (left-7) + '" y="' + (top+ih/2+3) + '" text-anchor="end" fill="currentColor" font-size="8">' + esc(formatValue((minY + maxY) / 2, p.decimal_places)) + '</text>' +
            '<text x="' + (left-7) + '" y="' + (top+ih+3) + '" text-anchor="end" fill="currentColor" font-size="8">' + esc(formatValue(minY, p.decimal_places)) + '</text>';

        return '<article class="dashboard-graph-card">' +
            '<div class="dashboard-graph-head"><div class="dashboard-graph-title">' +
                '<strong>' + esc(p.parameter_name || p.parameter_id) + '</strong>' +
                '<span>' + esc((cfg.time_range || "configured range")) + ' · ' + points.length + ' samples</span>' +
            '</div><div class="dashboard-graph-stat">' + esc(formatValue(points[points.length-1].value, p.decimal_places)) + ' ' + esc(p.unit || "") + '</div></div>' +
            '<svg class="dashboard-graph-svg" viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' + esc(p.parameter_name || p.parameter_id) + ' telemetry graph">' +
                grid + labels + points.map(function(pt) { var x = left + ((pt.time-firstT)/span)*iw; var y = top + (1-(pt.value-minY)/(maxY-minY))*ih; return '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="3" fill="currentColor"><title>' + esc(formatClock(new Date(pt.time).toISOString()) + ": " + formatValue(pt.value, p.decimal_places) + " " + (p.unit || "")) + '</title></circle>'; }).join("") +
                '<text x="' + left + '" y="' + (h-3) + '">' + esc(formatClock(new Date(firstT).toISOString())) + '</text><text x="' + (w-right) + '" y="' + (h-3) + '" text-anchor="end">' + esc(formatClock(new Date(lastT).toISOString())) + '</text>' +
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

        gateway.patchHtml(container, filtered.map(function (node) {
            var params = (state.telemetry[node.node_id] || []).filter(function (p) {
                return p && p.enabled !== false;
            });

            var shown = params.filter(function (p) { return p.display_enabled !== false; }).sort((a,b) => (SensorUI.config(a).position || 0) - (SensorUI.config(b).position || 0));

            var cards = shown.map(sensorCard).join("");
            if (!cards) cards = '<div class="dashboard-node-empty">No enabled sensor parameters configured for this node.</div>';



            var reported={};try{reported=typeof node.latest_status==="string"?JSON.parse(node.latest_status):node.latest_status||{};}catch(_){}
            var connection = SensorUI.connection(node);
            var nodeOnline = connection.online;
            var problemCount = params.filter(function (p) {
                var status = parameterStatus(p);
                return status === "alarm" || status === "error";
            }).length;
            return '<article class="dashboard-node" data-node-id="' + esc(node.node_id) + '">' +
                '<header class="dashboard-node-head">' +
                    '<div>' +
                        '<div class="dashboard-node-title-row">' +
                            '<span class="dashboard-node-status ' + (nodeOnline ? "online" : "offline") + '"></span>' +
                            '<div class="dashboard-node-name" title="' + esc(node.name || node.node_id) + '">' + esc(node.name || node.node_id) + '</div>' +
                        '</div>' +
                        '<div class="dashboard-node-id">' + esc(node.node_id) + (node.simulated ? ' · SIMULATED' : '') + '</div>' +
                    '</div>' +
                    '<button type="button" class="btn btn-secondary esp32-detail-button" data-esp32-details="' + esc(node.node_id) + '">ESP32 details</button>' +
                    '<div class="dashboard-node-state-pill ' + (nodeOnline ? "online" : "offline") + '"><span>' + esc(nodeOnline ? "ONLINE" : "OFFLINE") + '</span><strong>' + esc(nodeOnline ? (problemCount ? problemCount + " alerts" : "Connected") : "Connection unavailable") + '</strong></div>' +
                    '<div class="dashboard-node-basics" aria-label="Basic ESP32 details">' +
                        '<span><small>Role</small><strong>' + esc(node.device_role || reported.role || 'Unknown') + '</strong></span>' +
                        '<span><small>MCU</small><strong>' + esc(node.mcu_model || node.mcu_family || 'Not reported') + '</strong></span>' +
                        '<span><small>Transmit</small><strong>' + esc(reported.telemetry_seconds ? reported.telemetry_seconds + ' s' : 'Not reported') + '</strong></span>' +
                        '<span><small>' + (nodeOnline ? 'Wi-Fi RSSI' : 'Last Wi-Fi RSSI') + '</small><strong>' + esc(typeof reported.wifi_rssi === 'number' ? reported.wifi_rssi + ' dBm' : 'Not reported') + '</strong></span>' +
                        (node.master_id && node.master_id !== node.node_id ? '<span><small>Master</small><strong>' + esc(node.master_id) + '</strong></span>' : '') +
                        '<span><small>Last seen</small><strong>' + esc(formatTime(node.last_seen)) + '</strong></span>' +
                    '</div>' +
                '</header>' +
                (!nodeOnline ? '<p class="dashboard-node-error"><strong>Offline:</strong> ' + esc(connection.reason) + '</p>' : "") +
                '<div class="dashboard-node-body">' +
                    (state.showConfig
                        ? '<div class="dashboard-node-inspector"><div class="dashboard-node-inspector-head">Node Configuration</div><div class="dashboard-node-inspector-grid">' + nodeConfigFields(node) + '</div></div>'
                        : "") +
                    '<div class="dashboard-node-sensors sensor-live-grid">' + cards + '</div>' +
                '</div>' +
            '</article>';
        }).join(""));
    }

    async function openEsp32Details(nodeId) {
        var node = state.nodes.find(item => String(item.node_id) === String(nodeId));
        if (!node) return;
        document.querySelector('.esp32-details-dialog')?.remove();
        var opener = document.activeElement;
        var dialog = document.createElement('dialog');
        dialog.className = 'esp32-details-dialog';
        dialog.setAttribute('aria-labelledby', 'esp32-details-title');
        dialog.innerHTML = '<header><h2 id="esp32-details-title">ESP32 details</h2><button class="btn btn-secondary" type="button" data-close-device>Close</button></header><p role="status">Loading device details…</p><dl class="esp32-details-grid"></dl>';
        document.body.append(dialog);
        dialog.querySelector('[data-close-device]').onclick = () => dialog.close();
        dialog.addEventListener('click', event => { if (event.target === dialog) { var box=dialog.getBoundingClientRect(); if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)dialog.close(); } });
        dialog.addEventListener('close', () => { dialog.remove(); if(opener?.isConnected)opener.focus(); }, {once:true});
        dialog.showModal();
        var observed = null;
        try { var overview = await getJson('/api/operations/overview'); observed = overview.devices.find(item => item.node_id === nodeId); }
        catch (_) { /* Retain the already loaded telemetry snapshot, clearly labelled below. */ }
        if (!dialog.isConnected) return;
        var reported = {}; try { reported = typeof node.latest_status === 'string' ? JSON.parse(node.latest_status) : node.latest_status || {}; } catch (_) {}
        var x = observed?.reported || reported;
        var network = observed?.diagnostics?.GET_NETWORK;
        var connection = SensorUI.connection(node);
        var fields = [
            ['Device name', node.name || x.device_name || nodeId], ['Device ID', nodeId],
            ['Connection', observed?.health || (connection.online ? 'ONLINE' : 'OFFLINE')],
            ['Role', node.device_role || x.role || 'Unknown'], ['Master ID', node.master_id || 'Not assigned'],
            ['Hardware MAC', x.hardware_mac || observed?.hardware_mac || node.hardware_mac || 'Not reported'],
            ['Firmware', x.firmware_version || node.firmware_version || 'Not reported'],
            ['MCU', [node.mcu_family,node.mcu_model].filter(Boolean).join(' / ') || 'Not reported'],
            ['Address', node.node_address || 'Not reported'],
            ['Transmission interval', reported.telemetry_seconds ? reported.telemetry_seconds + ' s' : 'Not reported'],
            ['Last seen', formatTime(node.last_seen)],
            ['Transport (last report)', x.transport || node.communication_type || 'Not reported'],
            ['Last queried IP', network?.data?.station_ip || network?.data?.ip || 'Not queried'],
            ['Network query time', network?.received_at || 'Not queried']
        ];
        (Array.isArray(reported.sensors) ? reported.sensors : []).forEach(sensor => fields.push([sensor.sensor_type || 'Sensor', String(sensor.status || 'UNKNOWN').replaceAll('_',' ') + (sensor.sensor_type === 'MQ135' ? ' · raw and uncalibrated' : '')]));
        dialog.querySelector('[role="status"]').textContent = (observed ? 'Latest available Gateway observations.' : 'Telemetry snapshot; live device details could not be refreshed.') + (!connection.online ? ' Device offline; saved reports are historical.' : ' Queried values show their query time.');
        dialog.querySelector('dl').innerHTML = fields.map(([name,value]) => '<div><dt>' + esc(name) + '</dt><dd>' + esc(value) + '</dd></div>').join('');
    }

    function findTelemetryCard(card) {
        var nodeEl = card && card.closest(".dashboard-node");
        if (!nodeEl) return null;
        var nodeId = nodeEl.getAttribute("data-node-id");
        var parameterId = card.dataset.id;
        var node = state.nodes.find(function (item) { return String(item.node_id) === String(nodeId); });
        var parameter = (state.telemetry[nodeId] || []).find(function (p) {
            return String(p.parameter_id) === parameterId;
        });
        return node && parameter ? { node: node, parameter: parameter } : null;
    }

    async function openTelemetryDetail(card) {
        var found = findTelemetryCard(card);
        if (!found) return;
        try {
            var definitions = await getJson("/api/nodes/" + encodeURIComponent(found.node.node_id) + "/parameters");
            SensorUI.open(found.node, found.parameter, () => (definitions.parameters || []).map(definition => Object.assign({}, definition,
                (state.telemetry[found.node.node_id] || []).find(p => p.parameter_id === definition.parameter_id) || {})));
        } catch (error) { toast(error.message, "error"); }
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
                if (k === "alarm" || k === "error" || k === "stale") {
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
            gateway.patchHtml(box, '<div class="dashboard-empty">No active problems.</div>');
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
                if (k === "alarm" || k === "error" || k === "stale") problemCount += 1;
            });
        });

        text("total-nodes", state.nodes.length);
        text("online-nodes", onlineCount);
        text("sensor-count", paramCount);
        text("alarm-count", problemCount);

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

        gateway.patchHtml(box, state.customWidgets.map(function (widget) {
            var found = allParameters().find(function (item) {
                return item.node.node_id === widget.nodeId &&
                    (String(item.parameter.parameter_id) === String(widget.parameter) ||
                     String(item.parameter.parameter_name) === String(widget.parameter));
            });
            var p = found && found.parameter;
            return '<article class="dashboard-custom-card" data-id="' + esc(widget.id) + '">' +
                '<header><span class="widget-icon">' + telemetryIcon(Object.assign({}, p || {}, { widgetType: widget.widgetType })) + '</span><div><strong>' + esc(widget.name || widget.parameter) + '</strong>' +
                '<div style="margin-top:3px;color:var(--d-dim);font-size:8px">' + esc(widget.nodeId) + '</div></div>' +
                '<button type="button" data-delete-custom-widget="' + esc(widget.id) + '" aria-label="Delete widget">×</button></header>' +
                '<div class="custom-value">' + esc(p && p.value !== null && p.value !== undefined ? formatValue(p.value,p.decimal_places) : "—") +
                ' <span style="font-size:9px;color:var(--d-muted)">' + esc((p && p.unit) || "") + '</span></div>' +
                '</article>';
        }).join(""));
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
        if (!state.nodes.length) { toast("No nodes configured.", "warning"); return; }
        var overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.innerHTML = '<form class="modal" id="add-widget-form"><h2>Add widget</h2>' +
            '<label>Node<select class="input" name="node" required></select></label>' +
            '<label>Parameter<select class="input" name="parameter" required></select></label>' +
            '<label>Widget preset<select class="input" name="preset">' + Object.keys(widgetPresets).map(key => '<option value="' + key + '">' + widgetPresets[key][0] + '</option>').join("") + '</select></label>' +
            '<label>Title<input class="input" name="title" maxlength="80"></label>' +
            '<output class="widget-preview"></output><div class="modal-actions">' +
            '<button type="button" class="btn btn-secondary" id="widget-cancel">Cancel</button>' +
            '<button type="submit" class="btn btn-primary">Add widget</button></div></form>';
        var form = overlay.querySelector("form");
        var nodeSelect = form.elements.node;
        var parameterSelect = form.elements.parameter;
        state.nodes.forEach(function (node) {
            nodeSelect.add(new Option(node.name || node.node_id, node.node_id));
        });
        function preview() {
            var p = (state.telemetry[nodeSelect.value] || []).find(function (item) { return item.parameter_id === parameterSelect.value; });
            form.elements.title.value = p ? (p.parameter_name || p.parameter_id) : "";
            overlay.querySelector("output").textContent = p ? formatValue(p.value, p.decimal_places) + " " + (p.unit || "") : "No enabled parameters";
            form.querySelector('[type="submit"]').disabled = !p;
        }
        function chooseNode() {
            parameterSelect.replaceChildren();
            (state.telemetry[nodeSelect.value] || []).forEach(function (p) {
                parameterSelect.add(new Option(p.parameter_name || p.parameter_id, p.parameter_id));
            });
            preview();
        }
        nodeSelect.addEventListener("change", chooseNode);
        parameterSelect.addEventListener("change", preview);
        overlay.querySelector("#widget-cancel").addEventListener("click", function () { overlay.remove(); });
        overlay.addEventListener("click", function (event) { if (event.target === overlay) overlay.remove(); });
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            state.customWidgets.push({ id: "widget-" + Date.now(), name: form.elements.title.value || parameterSelect.value, nodeId: nodeSelect.value, parameter: parameterSelect.value, widgetType: form.elements.preset.value });
            saveCustomWidgets(); renderCustomWidgets(); overlay.remove(); toast("Widget added.", "success");
        });
        chooseNode();
        document.body.appendChild(overlay);
    }

    async function refreshDashboard(showToastFlag, withGraphs) {
        if (state.busy) { state.snapshotPending = true; return; }
        state.busy = true;

        var indicator = document.getElementById("dashboard-live-indicator");
        try {
            var snapshot = await getJson("/api/live/snapshot");
            state.nodes = snapshot.nodes || [];
            state.nodes.forEach(function (node) {
                state.telemetry[node.node_id] = node.parameters || [];
                state.telemetry[node.node_id].forEach(function (p) { p._nodeId = node.node_id; remember(p); });
            });
            populateNodeFilter();
            if (withGraphs) await Promise.allSettled(state.nodes.flatMap(function (node) {
                return (state.telemetry[node.node_id] || []).filter(function (p) { return p.display_enabled !== false; }).map(function (p) { return loadGraph(node.node_id, p); });
            }));
            updateCounters();
            renderNodes();
            renderProblems();
            renderCustomWidgets();
            renderMainChart();
            renderActivity(snapshot.logs || []);
            text("dashboard-last-refresh", formatClock(new Date().toISOString()));
            if (indicator) { indicator.style.opacity = "1"; indicator.textContent = gateway.socket?.connected ? "Live" : "Polling"; }
            /* Charts are integrated into sensor cards. */
            if (showToastFlag) toast("Dashboard refreshed.", "success");
        } catch (error) {
            console.error("Dashboard refresh error:", error);
            var box = document.getElementById("dashboard-node-list");
            if (box && !state.nodes.length) box.innerHTML = '<div class="dashboard-node-empty">Unable to load dashboard data: ' + esc(error.message) + '</div>';
            if (indicator) { indicator.style.opacity = ".55"; indicator.textContent = "Refresh failed · retrying"; }
            if (showToastFlag) toast("Dashboard data could not be loaded.", "error");
        } finally {
            state.busy = false;
            if (state.snapshotPending) { state.snapshotPending = false; refreshDashboard(false, false); }
        }
    }

    function startTimers() {
        stopTimers();
        state.refreshTimer = gateway.watch(() => refreshDashboard(false, false), {immediate:false});
        state.graphTimer = gateway.watch(() => { renderNodes(); renderProblems(); updateCounters(); }, {interval:1000, immediate:false});
    }

    function remember(p) {
        var key = p._nodeId + "::" + p.parameter_id;
        var samples = state.history[key] || (state.history[key] = []);
        if (p.timestamp && samples.timestamp !== p.timestamp && p.value !== null && Number.isFinite(Number(p.value))) {
            samples.push(Number(p.value));
            if (samples.length > 60) samples.shift();
            samples.timestamp = p.timestamp;
        }
        if (p.timestamp && p.value !== null && Number.isFinite(Number(p.value))) {
            var graph = state.graphs[key] || (state.graphs[key] = {config:{},data:[]});
            var last = graph.data[graph.data.length - 1];
            if (!last || new Date(p.timestamp) > new Date(last.timestamp)) {
                graph.data.push({value:p.value,timestamp:p.timestamp});
                graph.data = graph.data.slice(-180);
            }
        }
    }

    var paintPending = false;
    function applyTelemetry(update) {
        if (document.hidden) return;
        if (!update || !Array.isArray(update.parameters)) { refreshDashboard(false, false); return; }
        var node = state.nodes.find(function (item) { return item.node_id === update.node_id; });
        if (!node) { refreshDashboard(false, false); return; }
        var params = state.telemetry[update.node_id] || [];
        (update.parameters || []).forEach(function (incoming) {
            var p = params.find(function (item) { return item.parameter_id === incoming.parameter_id; });
            if (!p) { p = { parameter_id: incoming.parameter_id }; params.push(p); }
            if (p.timestamp && new Date(incoming.timestamp) <= new Date(p.timestamp)) return;
            Object.assign(p, incoming, { _nodeId: update.node_id });
            remember(p);
        });
        if (node.enabled) node.status = "online";
        if (!node.last_seen || new Date(update.received_at) > new Date(node.last_seen)) node.last_seen = update.received_at;
        state.telemetry[update.node_id] = params;
        if (!paintPending) {
            paintPending = true;
            requestAnimationFrame(function () {
                paintPending = false;
                updateCounters(); renderNodes(); renderProblems(); renderCustomWidgets(); renderMainChart();
                text("dashboard-last-refresh", formatClock(update.received_at));
            });
        }
    }

    function stopTimers() {
        if (state.refreshTimer) state.refreshTimer();
        if (state.graphTimer) state.graphTimer();
        state.refreshTimer = null;
        state.graphTimer = null;
    }

    var chartKeys = null;
    try { chartKeys = JSON.parse(localStorage.getItem("gateway_chart_keys")); } catch (_) {}
    if (!Array.isArray(chartKeys)) chartKeys = null;
    function renderMainChart() {
        var container = document.getElementById("telemetry-main-chart");
        if (!container) return;
        var parameters = allParameters();
        if (chartKeys === null) chartKeys = parameters.filter(e => e.parameter.graph_enabled).map(e => e.node.node_id + "::" + e.parameter.parameter_id);
        gateway.patchHtml(container, chartKeys.map(function(key) {
            var found = parameters.find(e => e.node.node_id + "::" + e.parameter.parameter_id === key);
            if (!found) return "";
            return '<section class="chart-entry" data-id="' + esc(key) + '"><div class="chart-entry-toolbar"><span>' +
                esc(found.node.name || found.node.node_id) + ' / ' + esc(found.parameter.unit || "") +
                '</span><button class="btn btn-secondary" type="button" data-remove-chart="' + esc(key) + '" aria-label="Remove ' +
                esc(found.parameter.parameter_name || found.parameter.parameter_id) + ' graph">Remove</button></div>' +
                graphSvg(found.node.node_id, found.parameter) + '</section>';
        }).join("") || '<div class="dashboard-empty">No graphs added.</div>');
    }

    function addChart() {
        var overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.innerHTML = '<form class="modal"><h2>Add graphs</h2><div class="graph-options"></div><div class="modal-actions"><button class="btn btn-secondary modal-close-btn" type="button">Cancel</button><button class="btn btn-primary">Add graphs</button></div></form>';
        var available = allParameters().filter(e => !(chartKeys || []).includes(e.node.node_id + "::" + e.parameter.parameter_id));
        overlay.querySelector(".graph-options").innerHTML = available.map((e,i) => '<label><input type="checkbox" name="graph" value="' + i + '"> ' + esc((e.node.name || e.node.node_id) + " / " + (e.parameter.parameter_name || e.parameter.parameter_id)) + '</label>').join("") || '<p>All configured parameters already have graphs.</p>';
        overlay.querySelector(".modal-close-btn").onclick = () => overlay.remove();
        overlay.querySelector("form").onsubmit = async event => {
            event.preventDefault();
            var selected = Array.from(overlay.querySelectorAll("input:checked")).map(input => available[Number(input.value)]);
            chartKeys = chartKeys || [];
            selected.forEach(e => chartKeys.push(e.node.node_id + "::" + e.parameter.parameter_id));
            localStorage.setItem("gateway_chart_keys", JSON.stringify(chartKeys));
            overlay.remove();
            await Promise.allSettled(selected.map(e => loadGraph(e.node.node_id, e.parameter)));
            renderMainChart();
        };
        document.body.appendChild(overlay);
    }

    function bind() {
        document.getElementById("add-telemetry-chart")?.addEventListener("click", () => window.location.assign("/sensors#sensor-management"));
        document.getElementById("telemetry-main-chart")?.addEventListener("click", function(event) {
            var button = event.target.closest("[data-remove-chart]");
            if (!button) return;
            chartKeys = chartKeys.filter(key => key !== button.dataset.removeChart);
            localStorage.setItem("gateway_chart_keys", JSON.stringify(chartKeys)); renderMainChart();
        });
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
            window.location.assign("/sensors#sensor-management");
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
        document.getElementById("add-sensor-widget-inline")?.addEventListener("click", () => SensorUI.chooseWidgets(state.nodes, () => refreshDashboard(false, true)));

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
            var deviceDetails = e.target.closest('[data-esp32-details]');
            if (deviceDetails) { openEsp32Details(deviceDetails.dataset.esp32Details); return; }
            var remove = e.target.closest("[data-sensor-remove]");
            if (remove) {
                var found = findTelemetryCard(remove.closest(".dashboard-sensor-card"));
                if (!found) return;
                getJson("/api/nodes/" + encodeURIComponent(found.node.node_id) + "/parameters/" + encodeURIComponent(found.parameter.parameter_id), {
                    method: "PUT", headers: {"Content-Type":"application/json","X-CSRF-Token":document.querySelector('meta[name="sensor-csrf"]')?.content || ""},
                    body: JSON.stringify({display_enabled:false})
                }).then(() => refreshDashboard(false,true)).catch(error => toast(error.message,"error"));
                return;
            }
            var card = e.target.closest(".dashboard-sensor-card");
            if (!card) return;
            openTelemetryDetail(card);
        });

        document.getElementById("dashboard-node-list")?.addEventListener("keydown", function (e) {
            if (e.target.closest("button,a,input,select")) return;
            if (e.key !== "Enter" && e.key !== " ") return;
            var card = e.target.closest(".dashboard-sensor-card");
            if (!card) return;
            e.preventDefault();
            openTelemetryDetail(card);
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") {
                document.querySelector(".dashboard-telemetry-modal")?.remove();
            }
            if (e.key === "Escape") closeDrawer();
        });


    }

    bind();
    loadLayout();
    loadCustomWidgets();
    var socket = gateway.socket;
    socket?.on("telemetry_update", applyTelemetry);
    socket?.on("connect", function () { refreshDashboard(false, true); text("dashboard-live-indicator", "Live"); });
    socket?.on("disconnect", function () { text("dashboard-live-indicator", "Reconnecting"); });
    refreshDashboard(false, true).then(startTimers);

});
