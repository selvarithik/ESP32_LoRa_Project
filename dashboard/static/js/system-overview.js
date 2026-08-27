"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const eventsEl = document.getElementById("overview-events");
    if (!eventsEl) return;

    let timer = null;
    let loading = false;

    init();

    async function init() {
        await loadOverview();
        if (timer) clearInterval(timer);
        timer = setInterval(loadOverview, 5000);
        window.addEventListener("beforeunload", () => clearInterval(timer), { once: true });
    }

    async function loadOverview() {
        if (loading) return;
        loading = true;
        try {
            const [status, nodesResponse, logsResponse] = await Promise.all([
                gateway.get("/api/status"),
                gateway.get("/api/nodes"),
                gateway.get("/api/logs")
            ]);

            const nodes = Array.isArray(nodesResponse) ? nodesResponse : (nodesResponse.nodes || []);
            const logs = Array.isArray(logsResponse) ? logsResponse : (logsResponse.logs || []);

            updateHealth(status, nodes);
            renderEvents(logs.slice(0, 15));
        } catch (error) {
            console.error("System overview error:", error);
            gateway.showError(eventsEl, "Unable to load system health", loadOverview);
        } finally {
            loading = false;
        }
    }

    function updateHealth(status, nodes) {
        const online = nodes.filter(n => gateway.status(n.status) === "online").length;
        const disabled = nodes.filter(n => !n.enabled).length;
        const offline = nodes.filter(n => gateway.status(n.status) === "offline" && n.enabled).length;
        const communication = nodes.length ? (online > 0 ? "ACTIVE" : "STANDBY") : "NO NODES";
        const health = offline > 0 ? "WARNING" : "HEALTHY";

        setHealth("overview-gateway-status", status?.status === "online" ? "ONLINE" : "OFFLINE", status?.status === "online" ? "online" : "alarm");
        setHealth("overview-node-status", nodes.length ? `${online} ONLINE / ${offline} OFFLINE / ${disabled} DISABLED` : "NO NODES", offline ? "warning" : "online");
        setHealth("overview-communication-status", communication, online ? "online" : "warning");
        setHealth("overview-sensor-status", nodes.length ? "AVAILABLE" : "NO NODES", nodes.length ? "online" : "warning");
        setHealth("overview-system-health", health, health === "HEALTHY" ? "online" : "warning");
    }

    function setHealth(id, text, state) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = `● ${text}`;
        el.className = `health-${state}`;
    }

    function renderEvents(logs) {
        if (!logs.length) {
            eventsEl.innerHTML = `<div class="empty-state">No recent events.</div>`;
            return;
        }
        eventsEl.innerHTML = logs.map(log => `
            <div class="timeline-item">
                <span class="timeline-dot"></span>
                <div class="timeline-message">
                    <strong>${gateway.escape(log.message || "Event")}</strong>
                    <div>${gateway.escape(log.source || "SYSTEM")}${log.node_id ? ` · ${gateway.escape(log.node_id)}` : ""}</div>
                </div>
                <span class="timeline-time">${gateway.time(log.timestamp)}</span>
            </div>
        `).join("");
    }
});
