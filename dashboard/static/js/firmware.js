"use strict";

/* ============================================================
   FIRMWARE / OTA DASHBOARD
   Server-side firmware management only.
   Real ESP32 OTA is implemented in a later phase.
   ============================================================ */

(function () {

    const state = {
        releases: [],
        devices: [],
        jobs: [],
        events: [],
        selectedRelease: null,
        config: null,
        refreshBusy: false
    };

    const TERMINAL_JOB_STATES = new Set([
        "SUCCESS",
        "FAILED",
        "ROLLBACK",
        "CANCELLED"
    ]);

    const ESCAPE_MAP = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    };

    function $(id) {
        return document.getElementById(id);
    }

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ESCAPE_MAP[char]);
    }

    function formatDate(value) {
        if (!value) return "—";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return date.toLocaleString();
    }

    function formatBytes(value) {
        const bytes = Number(value || 0);
        if (!bytes) return "0 B";
        const units = ["B", "KB", "MB", "GB"];
        let size = bytes;
        let unit = 0;
        while (size >= 1024 && unit < units.length - 1) {
            size /= 1024;
            unit += 1;
        }
        return `${size >= 10 || unit === 0 ? size.toFixed(0) : size.toFixed(1)} ${units[unit]}`;
    }

    function normalizeStatus(value) {
        return String(value || "IDLE").toLowerCase().replace(/[^a-z0-9]+/g, "_");
    }

    function statusBadge(value) {
        const text = String(value || "UNKNOWN");
        return `<span class="status ${escapeHtml(normalizeStatus(text))}">${escapeHtml(text)}</span>`;
    }

    function showToast(message, type = "info") {
        const container = $("toast-container");
        if (!container) {
            window.alert(message);
            return;
        }

        const toast = document.createElement("div");
        toast.className = `toast ${escapeHtml(type)}`;
        toast.textContent = message;
        container.appendChild(toast);

        window.setTimeout(() => {
            toast.remove();
        }, 3500);
    }

    async function requestJson(url, options = {}) {
        const response = await fetch(url, {
            credentials: "same-origin",
            ...options
        });

        const contentType = response.headers.get("Content-Type") || "";
        let data;

        if (contentType.includes("application/json")) {
            data = await response.json();
        } else {
            const text = await response.text();
            data = { success: response.ok, error: text || "Request failed." };
        }

        if (!response.ok || data.success === false) {
            throw new Error(data.error || `Request failed (${response.status})`);
        }

        return data;
    }

    function setLoading(id, columns, message) {
        const element = $(id);
        if (!element) return;
        element.innerHTML = `<tr><td colspan="${columns}" class="loading">${escapeHtml(message)}</td></tr>`;
    }

    function openUploadPanel(open = true) {
        const panel = $("firmware-upload-panel");
        if (!panel) return;
        panel.classList.toggle("open", open);
        if (open) {
            panel.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    function showValidation(release) {
        const box = $("firmware-validation");
        if (!box) return;

        box.classList.add("show");
        box.innerHTML = `
            <div class="firmware-validation-card">
                <div><span>Release ID</span><strong>${escapeHtml(release.release_id)}</strong></div>
                <div><span>Version</span><strong>${escapeHtml(release.version)}</strong></div>
                <div><span>Size</span><strong>${escapeHtml(formatBytes(release.file_size))}</strong></div>
                <div><span>SHA-256</span><strong>${escapeHtml(release.sha256)}</strong></div>
                <div><span>Status</span><strong>${statusBadge(release.status)}</strong></div>
                <div><span>Hardware</span><strong>${escapeHtml(release.hardware_model)}</strong></div>
                <div><span>Channel</span><strong>${escapeHtml(release.channel)}</strong></div>
                <div><span>Validation</span><strong>VALID</strong></div>
            </div>
        `;
    }

    function hideValidation() {
        const box = $("firmware-validation");
        if (!box) return;
        box.classList.remove("show");
        box.innerHTML = "";
    }

    function updateCounters() {
        const devices = state.devices;
        const total = devices.length;
        const updatingStates = new Set([
            "APPROVED",
            "CHECKING",
            "DOWNLOADING",
            "VERIFYING",
            "READY_TO_BOOT",
            "REBOOTING",
            "VALIDATING"
        ]);

        let updating = 0;
        let failed = 0;
        let available = 0;
        let upToDate = 0;

        devices.forEach(device => {
            const stateName = String(device.ota_state || "IDLE").toUpperCase();
            if (updatingStates.has(stateName)) updating += 1;
            if (stateName === "FAILED" || stateName === "ROLLBACK") failed += 1;
            if (stateName === "UPDATE_AVAILABLE") available += 1;
            if ((stateName === "IDLE" || stateName === "SUCCESS") && !device.target_version) upToDate += 1;
        });

        $("fw-total-devices").textContent = String(total);
        $("fw-up-to-date").textContent = String(upToDate);
        $("fw-updates-available").textContent = String(available);
        $("fw-updating").textContent = String(updating);
        $("fw-failed").textContent = String(failed);
    }

    function renderReleases() {
        const table = $("firmware-releases-table");
        if (!table) return;

        if (!state.releases.length) {
            table.innerHTML = '<tr><td colspan="10" class="loading">No firmware releases found.</td></tr>';
            return;
        }

        table.innerHTML = state.releases.map(release => {
            const actions = [];
            const status = String(release.status || "DRAFT").toUpperCase();

            actions.push(`<button class="btn btn-secondary js-release-details" data-id="${escapeHtml(release.release_id)}">Details</button>`);
            if (["TESTING", "APPROVED", "ACTIVE"].includes(status)) {
                actions.push(`<a class="btn btn-secondary" href="/api/firmware/download/${encodeURIComponent(release.release_id)}">Download</a>`);
            }

            if (status === "DRAFT") {
                actions.push(`<button class="btn btn-secondary js-release-status" data-id="${escapeHtml(release.release_id)}" data-status="TESTING">Testing</button>`);
            } else if (status === "TESTING") {
                actions.push(`<button class="btn btn-primary js-release-status" data-id="${escapeHtml(release.release_id)}" data-status="APPROVED">Approve</button>`);
            } else if (status === "APPROVED") {
                actions.push(`<button class="btn btn-primary js-release-status" data-id="${escapeHtml(release.release_id)}" data-status="ACTIVE">Activate</button>`);
            } else if (status === "ACTIVE") {
                actions.push(`<button class="btn btn-secondary js-release-status" data-id="${escapeHtml(release.release_id)}" data-status="RETIRED">Retire</button>`);
            }

            return `
                <tr>
                    <td>${escapeHtml(release.version)}</td>
                    <td>${escapeHtml(release.build)}</td>
                    <td>${escapeHtml(release.hardware_model)}</td>
                    <td>${escapeHtml(release.hardware_revision)}</td>
                    <td>${escapeHtml(release.channel)}</td>
                    <td>${escapeHtml(formatBytes(release.file_size))}</td>
                    <td><span class="firmware-hash" title="${escapeHtml(release.sha256)}">${escapeHtml(release.sha256)}</span></td>
                    <td>${statusBadge(release.status)}</td>
                    <td>${escapeHtml(formatDate(release.created_at))}</td>
                    <td><div class="firmware-actions">${actions.join("")}</div></td>
                </tr>
            `;
        }).join("");

        table.querySelectorAll(".js-release-details").forEach(button => {
            button.addEventListener("click", () => showReleaseDetails(button.dataset.id));
        });

        table.querySelectorAll(".js-release-status").forEach(button => {
            button.addEventListener("click", () => changeReleaseStatus(button.dataset.id, button.dataset.status));
        });
    }

    function renderDevices() {
        const table = $("firmware-devices-table");
        if (!table) return;

        if (!state.devices.length) {
            table.innerHTML = '<tr><td colspan="8" class="loading">No devices registered.</td></tr>';
            return;
        }

        table.innerHTML = state.devices.map(device => {
            const hardware = [
                device.hardware_model || device.hardware_family || "—",
                device.hardware_revision || ""
            ].filter(Boolean).join(" / ");
            const stateName = String(device.ota_state || "IDLE").toUpperCase();
            const canUpdate = !new Set([
                "APPROVED",
                "CHECKING",
                "DOWNLOADING",
                "VERIFYING",
                "READY_TO_BOOT",
                "REBOOTING",
                "VALIDATING"
            ]).has(stateName);

            const action = canUpdate
                ? `<button class="btn btn-primary js-device-update" data-id="${escapeHtml(device.node_id)}">Check / Update</button>`
                : `<button class="btn btn-secondary" disabled>In Progress</button>`;

            return `
                <tr>
                    <td>${escapeHtml(device.node_id)}</td>
                    <td>${escapeHtml(hardware)}</td>
                    <td>${escapeHtml(device.current_version || "—")}</td>
                    <td>${escapeHtml(device.target_version || "—")}</td>
                    <td>${statusBadge(stateName)}</td>
                    <td>${escapeHtml(device.channel || "stable")}</td>
                    <td>${escapeHtml(formatDate(device.last_update_at))}</td>
                    <td>${action}</td>
                </tr>
            `;
        }).join("");

        table.querySelectorAll(".js-device-update").forEach(button => {
            button.addEventListener("click", () => checkAndCreateUpdate(button.dataset.id));
        });
    }

    function renderJobs() {
        const table = $("firmware-jobs-table");
        if (!table) return;

        if (!state.jobs.length) {
            table.innerHTML = '<tr><td colspan="9" class="loading">No update jobs found.</td></tr>';
            return;
        }

        table.innerHTML = state.jobs.map(job => `
            <tr>
                <td>${escapeHtml(job.job_id)}</td>
                <td>${escapeHtml(job.node_id)}</td>
                <td>${escapeHtml(job.from_version || "—")}</td>
                <td>${escapeHtml(job.target_version || "—")}</td>
                <td>${statusBadge(job.state)}</td>
                <td>
                    <div class="firmware-progress">
                        <div class="firmware-progress-track">
                            <div class="firmware-progress-bar" style="width:${Math.max(0, Math.min(100, Number(job.progress || 0)))}%"></div>
                        </div>
                        <span>${escapeHtml(job.progress)}%</span>
                    </div>
                </td>
                <td>${escapeHtml(formatDate(job.started_at))}</td>
                <td>${escapeHtml(formatDate(job.completed_at))}</td>
                <td>${escapeHtml(job.result || job.error || "—")}</td>
            </tr>
        `).join("");
    }

    function renderHistory() {
        const table = $("firmware-history-table");
        if (!table) return;

        if (!state.events.length) {
            table.innerHTML = '<tr><td colspan="7" class="loading">No OTA history found.</td></tr>';
            return;
        }

        table.innerHTML = state.events.map(event => `
            <tr>
                <td>${escapeHtml(formatDate(event.created_at))}</td>
                <td>${escapeHtml(event.event_type || "—")}</td>
                <td>${escapeHtml(event.node_id || "—")}</td>
                <td>${escapeHtml(event.job_id || "—")}</td>
                <td>${statusBadge(event.state || "INFO")}</td>
                <td>${event.progress == null ? "—" : `${escapeHtml(event.progress)}%`}</td>
                <td>${escapeHtml(event.message || event.error || "—")}</td>
            </tr>
        `).join("");
    }

    function showModal(title, body) {
        const root = $("modal-root");
        if (!root) {
            window.alert(`${title}\n\n${body.replace(/<[^>]+>/g, "")}`);
            return;
        }

        root.innerHTML = `
            <div class="modal-backdrop js-modal-close">
                <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="firmware-modal-title">
                    <div class="modal-header">
                        <div><h3 id="firmware-modal-title">${escapeHtml(title)}</h3></div>
                        <button type="button" class="icon-btn js-modal-close" title="Close">×</button>
                    </div>
                    <div class="modal-body">${body}</div>
                </div>
            </div>
        `;

        root.querySelectorAll(".js-modal-close").forEach(element => {
            element.addEventListener("click", event => {
                if (event.target === element || element.classList.contains("icon-btn")) {
                    root.innerHTML = "";
                }
            });
        });
    }

    async function showReleaseDetails(releaseId) {
        try {
            const data = await requestJson(`/api/firmware/releases/${encodeURIComponent(releaseId)}`);
            const release = data.release;
            const body = `
                <div class="firmware-detail-grid">
                    <div><span>Release ID</span><strong>${escapeHtml(release.release_id)}</strong></div>
                    <div><span>Version</span><strong>${escapeHtml(release.version)}</strong></div>
                    <div><span>Build</span><strong>${escapeHtml(release.build)}</strong></div>
                    <div><span>Status</span><strong>${statusBadge(release.status)}</strong></div>
                    <div><span>Hardware Family</span><strong>${escapeHtml(release.hardware_family)}</strong></div>
                    <div><span>Hardware Model</span><strong>${escapeHtml(release.hardware_model)}</strong></div>
                    <div><span>Hardware Revision</span><strong>${escapeHtml(release.hardware_revision)}</strong></div>
                    <div><span>Channel</span><strong>${escapeHtml(release.channel)}</strong></div>
                    <div><span>Size</span><strong>${escapeHtml(formatBytes(release.file_size))}</strong></div>
                    <div><span>SHA-256</span><strong>${escapeHtml(release.sha256)}</strong></div>
                    <div><span>Mandatory</span><strong>${release.mandatory ? "YES" : "NO"}</strong></div>
                    <div><span>Created</span><strong>${escapeHtml(formatDate(release.created_at))}</strong></div>
                </div>
                <div class="firmware-detail-notes">
                    <span>Release Notes</span>
                    <p>${escapeHtml(release.release_notes || "No release notes.")}</p>
                </div>
            `;
            showModal(`Firmware ${release.version}`, body);
        } catch (error) {
            showToast(error.message, "error");
        }
    }

    async function changeReleaseStatus(releaseId, status) {
        try {
            const data = await requestJson(`/api/firmware/releases/${encodeURIComponent(releaseId)}/status`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status })
            });
            showToast(`Release moved to ${data.release.status}.`, "success");
            await refreshAll();
        } catch (error) {
            showToast(error.message, "error");
        }
    }

    async function uploadFirmware(event) {
        event.preventDefault();
        const form = $("firmware-upload-form");
        if (!form) return;

        const fileInput = form.querySelector('input[type="file"][name="firmware"]');
        const file = fileInput && fileInput.files ? fileInput.files[0] : null;
        if (!file) {
            showToast("Select a firmware file first.", "error");
            return;
        }

        const formData = new FormData(form);
        formData.set("mandatory", form.querySelector('[name="mandatory"]')?.checked ? "true" : "false");

        const submit = form.querySelector('button[type="submit"]');
        if (submit) submit.disabled = true;

        try {
            const data = await requestJson("/api/firmware/releases", {
                method: "POST",
                body: formData
            });
            showValidation(data.release);
            showToast(`Firmware ${data.release.version} uploaded as DRAFT.`, "success");
            form.reset();
            const hwFamily = form.querySelector('[name="hardware_family"]');
            const hwModel = form.querySelector('[name="hardware_model"]');
            const hwRevision = form.querySelector('[name="hardware_revision"]');
            if (hwFamily) hwFamily.value = "ESP32";
            if (hwModel) hwModel.value = "ESP32-WROOM-32";
            if (hwRevision) hwRevision.value = "REV-A";
            openUploadPanel(false);
            await refreshAll();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            if (submit) submit.disabled = false;
        }
    }

    async function loadConfig() {
        const data = await requestJson("/api/firmware/config");
        state.config = data.config;
        applyConfig();
    }

    function applyConfig() {
        if (!state.config) return;
        if ($("ota-enabled")) $("ota-enabled").checked = Boolean(state.config.ota_enabled);
        if ($("ota-channel")) $("ota-channel").value = state.config.update_channel || "stable";
        if ($("ota-automatic")) $("ota-automatic").checked = Boolean(state.config.automatic_updates);
        if ($("ota-check-interval")) $("ota-check-interval").value = Number(state.config.check_interval_hours || 6);
        if ($("ota-manual-approval")) $("ota-manual-approval").checked = Boolean(state.config.manual_approval);
        if ($("ota-rollback")) $("ota-rollback").checked = Boolean(state.config.rollback_enabled);
        if ($("ota-allow-downgrade")) $("ota-allow-downgrade").checked = Boolean(state.config.allow_downgrade);
        if ($("ota-require-https")) $("ota-require-https").checked = Boolean(state.config.require_https);
    }

    async function saveConfig() {
        const payload = {
            ota_enabled: $("ota-enabled")?.checked !== false,
            update_channel: $("ota-channel")?.value || "stable",
            automatic_updates: Boolean($("ota-automatic")?.checked),
            check_interval_hours: Number($("ota-check-interval")?.value || 6),
            manual_approval: Boolean($("ota-manual-approval")?.checked),
            rollback_enabled: Boolean($("ota-rollback")?.checked),
            allow_downgrade: Boolean($("ota-allow-downgrade")?.checked),
            require_https: $("ota-require-https")?.checked !== false
        };

        const data = await requestJson("/api/firmware/config", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        state.config = data.config;
        applyConfig();
        showToast("OTA configuration saved.", "success");
    }

    async function checkAndCreateUpdate(nodeId) {
        const device = state.devices.find(item => item.node_id === nodeId);
        if (!device) return;

        try {
            const checkPayload = {
                hardware_family: device.hardware_family,
                hardware_model: device.hardware_model,
                hardware_revision: device.hardware_revision,
                firmware_version: device.current_version || "0.0.0",
                build: Number(device.current_build || 0),
                channel: device.channel || "stable",
                ota_protocol_version: 1
            };

            const check = await requestJson(`/api/firmware/device/${encodeURIComponent(nodeId)}/check`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(checkPayload)
            });

            if (!check.update_available || !check.release) {
                showToast(`${nodeId}: no update available.`, "info");
                await refreshAll();
                return;
            }

            const release = check.release;
            if (!window.confirm(`Update ${nodeId} from ${device.current_version || "unknown"} to ${release.version}?`)) {
                return;
            }

            const job = await requestJson("/api/firmware/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    node_id: nodeId,
                    release_id: release.release_id,
                    authorized: true
                })
            });

            showToast(`OTA job ${job.job.job_id} created.`, "success");
            await refreshAll();
        } catch (error) {
            showToast(error.message, "error");
        }
    }

    async function refreshAll() {
        if (state.refreshBusy) return;
        state.refreshBusy = true;

        try {
            const [releases, devices, jobs] = await Promise.all([
                requestJson("/api/firmware/releases"),
                requestJson("/api/firmware/devices"),
                requestJson("/api/firmware/jobs")
            ]);

            state.releases = Array.isArray(releases.releases) ? releases.releases : [];
            state.devices = Array.isArray(devices.devices) ? devices.devices : [];
            state.jobs = Array.isArray(jobs.jobs) ? jobs.jobs : [];
            state.events = Array.isArray(jobs.events) ? jobs.events : [];

            updateCounters();
            renderReleases();
            renderDevices();
            renderJobs();
            renderHistory();

            if (!state.config) {
                await loadConfig();
            }
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            state.refreshBusy = false;
        }
    }

    function bindEvents() {
        $("firmware-refresh")?.addEventListener("click", refreshAll);
        $("firmware-upload-open")?.addEventListener("click", () => openUploadPanel(true));
        $("firmware-upload-clear")?.addEventListener("click", () => {
            $("firmware-upload-form")?.reset();
            hideValidation();
            openUploadPanel(false);
        });
        $("firmware-upload-form")?.addEventListener("submit", uploadFirmware);

        [
            "ota-enabled",
            "ota-channel",
            "ota-automatic",
            "ota-check-interval",
            "ota-manual-approval",
            "ota-rollback",
            "ota-allow-downgrade",
            "ota-require-https"
        ].forEach(id => $(id)?.addEventListener("change", saveConfig));
    }

    async function initialize() {
        bindEvents();
        setLoading("firmware-releases-table", 10, "Loading releases...");
        setLoading("firmware-devices-table", 8, "Loading device firmware...");
        setLoading("firmware-jobs-table", 9, "Loading update jobs...");
        setLoading("firmware-history-table", 7, "Loading update history...");

        console.log("[FIRMWARE] Initializing");
        await refreshAll();
        console.log("[FIRMWARE] Ready", state);

        window.setInterval(async () => {
            const hasActiveJobs = state.jobs.some(job => !TERMINAL_JOB_STATES.has(String(job.state || "").toUpperCase()));
            if (hasActiveJobs) {
                await refreshAll();
            }
        }, 3000);
    }

    document.addEventListener("DOMContentLoaded", initialize);

})();
