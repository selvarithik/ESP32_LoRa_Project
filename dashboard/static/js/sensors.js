"use strict";

document.addEventListener("DOMContentLoaded", () => {

    const table = document.getElementById("sensor-table");

    if (!table) return;

    let sensors = [];
    let selectedNode = "";
    let activeFilter = "all";


    init();


    let refreshTimer = null;

    async function init() {

        bindEvents();
        await loadNodes();

        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(() => {
            if (selectedNode) loadSensors();
        }, 3000);
    }


    /* =========================================
       EVENTS
    ========================================= */

    function bindEvents() {

        document
            .getElementById("sensor-node")
            ?.addEventListener(
                "change",
                async event => {

                    selectedNode =
                        event.target.value;

                    await loadSensors();

                }
            );


        document
            .getElementById("sensor-search")
            ?.addEventListener(
                "input",
                renderSensors
            );


        document
            .querySelectorAll(".filter-chip")
            .forEach(chip => {

                chip.addEventListener(
                    "click",
                    () => {

                        document
                            .querySelectorAll(
                                ".filter-chip"
                            )
                            .forEach(item =>
                                item.classList
                                    .remove("active")
                            );

                        chip.classList.add("active");

                        activeFilter =
                            chip.dataset.filter ||
                            "all";

                        renderSensors();

                    }
                );

            });


        document
            .getElementById("sensor-close")
            ?.addEventListener(
                "click",
                closeDrawer
            );


        document
            .getElementById("sensor-overlay")
            ?.addEventListener(
                "click",
                closeDrawer
            );

    }


    /* =========================================
       LOAD NODES
    ========================================= */

    async function loadNodes() {

        const selector =
            document.getElementById(
                "sensor-node"
            );

        if (!selector) return;


        try {

            const response =
                await gateway.get(
                    "/api/nodes"
                );

            const nodes =
                Array.isArray(response)
                    ? response
                    : response.nodes || [];


            if (!nodes.length) {

                selector.innerHTML =
                    `<option value="">
                        No Nodes Configured
                    </option>`;

                table.innerHTML =
                    emptyRow(
                        "No Nodes Configured"
                    );

                return;
            }


            selector.innerHTML =
                `<option value="">
                    Select Node
                </option>` +
                nodes.map(node => {

                    return `
                        <option value="${
                            gateway.escape(
                                node.node_id
                            )
                        }">

                            ${
                                gateway.escape(
                                    node.name ||
                                    node.node_id
                                )
                            }

                        </option>
                    `;

                }).join("");


            /*
             * Automatically select first node.
             */
            selector.value =
                nodes[0].node_id;

            selectedNode =
                nodes[0].node_id;

            await loadSensors();


        } catch (error) {

            console.error(
                "Sensor node loading error:",
                error
            );

            gateway.toast(
                "Unable to load nodes",
                "error"
            );

        }

    }


    /* =========================================
       LOAD SENSOR PARAMETERS
    ========================================= */

    async function loadSensors() {

        if (!selectedNode) {

            table.innerHTML =
                emptyRow(
                    "Select a node to view sensor parameters."
                );

            return;
        }


        table.innerHTML = `
            <tr>
                <td colspan="7"
                    class="loading">
                    Loading sensor parameters...
                </td>
            </tr>
        `;


        try {

            const response =
                await gateway.get(
                    `/api/nodes/${encodeURIComponent(
                        selectedNode
                    )}/parameters`
                );


            sensors =
                response.parameters || [];


            renderSensors();


        } catch (error) {

            console.error(
                "Sensor loading error:",
                error
            );


            table.innerHTML =
                errorRow();


            document
                .getElementById(
                    "sensor-retry"
                )
                ?.addEventListener(
                    "click",
                    loadSensors
                );


            gateway.toast(
                "Unable to load sensor parameters",
                "error"
            );

        }

    }


    /* =========================================
       FILTER + SEARCH
    ========================================= */

    function getFilteredSensors() {

        const search =
            (
                document.getElementById(
                    "sensor-search"
                )?.value || ""
            )
            .toLowerCase()
            .trim();


        return sensors.filter(sensor => {

            const text =
                `
                ${sensor.parameter_name || ""}
                ${sensor.parameter_id || ""}
                ${sensor.parameter_type || ""}
                ${sensor.unit || ""}
                `.toLowerCase();


            if (
                search &&
                !text.includes(search)
            ) {
                return false;
            }


            switch (activeFilter) {

                case "enabled":
                    return sensor.enabled === true ||
                           sensor.enabled === 1;

                case "alarm":
                    return sensor.alarm_enabled === true ||
                           sensor.alarm_enabled === 1;

                case "graph":
                    return sensor.graph_enabled === true ||
                           sensor.graph_enabled === 1;

                default:
                    return true;
            }

        });

    }


    /* =========================================
       RENDER TABLE
    ========================================= */

    function renderSensors() {

        const filtered =
            getFilteredSensors();


        if (!filtered.length) {

            table.innerHTML =
                emptyRow(
                    sensors.length
                        ? "No parameters match the current filter."
                        : "No sensor parameters configured."
                );

            return;
        }


        table.innerHTML =
            filtered.map(sensor => {

                const status =
                    gateway.status(
                        sensor.alarm_status ||
                        sensor.status
                    );


                const value =
                    sensor.value ??
                    sensor.text_value ??
                    "—";


                return `
                    <tr>

                        <td>

                            <div>
                                <strong>
                                    ${
                                        gateway.escape(
                                            sensor.parameter_name ||
                                            sensor.parameter_id
                                        )
                                    }
                                </strong>

                                <small style="
                                    display:block;
                                    margin-top:3px;
                                    color:#98A2B3;
                                    font-size:8px;
                                ">

                                    ${
                                        gateway.escape(
                                            sensor.parameter_id
                                        )
                                    }

                                </small>

                            </div>

                        </td>


                        <td>

                            <strong>
                                ${
                                    gateway.escape(
                                        value
                                    )
                                }
                            </strong>

                        </td>


                        <td>
                            ${
                                gateway.escape(
                                    sensor.unit ||
                                    "—"
                                )
                            }
                        </td>


                        <td>

                            <span class="
                                quality-good
                            ">

                                ${
                                    gateway.escape(
                                        sensor.quality ||
                                        "GOOD"
                                    )
                                }

                            </span>

                        </td>


                        <td>

                            <span class="
                                status ${status}
                            ">

                                ${
                                    (
                                        sensor.alarm_status ||
                                        sensor.status ||
                                        "NORMAL"
                                    ).toUpperCase()
                                }

                            </span>

                        </td>


                        <td>
                            ${
                                gateway.time(
                                    sensor.timestamp ||
                                    sensor.updated_at
                                )
                            }
                        </td>


                        <td>

                            <button
                                class="icon-btn sensor-view"
                                data-id="${
                                    gateway.escape(
                                        sensor.parameter_id
                                    )
                                }">

                                View

                            </button>

                        </td>

                    </tr>
                `;

            }).join("");


        bindViewButtons();

    }


    /* =========================================
       VIEW SENSOR
    ========================================= */

    function bindViewButtons() {

        document
            .querySelectorAll(".sensor-view")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        const sensor =
                            sensors.find(
                                item =>
                                    item.parameter_id ===
                                    button.dataset.id
                            );


                        if (sensor) {
                            openSensorDrawer(
                                sensor
                            );
                        }

                    }
                );

            });

    }


    function openSensorDrawer(sensor) {

        const drawer = document.getElementById(
                "sensor-drawer"
            );

        const overlay = document.getElementById(
                "sensor-overlay"
            );

        const title = document.getElementById(
                "sensor-title"
            );

        const details = document.getElementById(
                "sensor-details"
            );


        if (
            !drawer ||
            !overlay ||
            !details
        ) {
            return;
        }


        title.textContent =
            sensor.parameter_name ||
            sensor.parameter_id;


        details.innerHTML = `

            <h4>GENERAL</h4>

            <div class="detail-grid">

                <div>
                    <small>
                        Parameter ID
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                sensor.parameter_id
                            )
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Parameter Type
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                sensor.parameter_type ||
                                "—"
                            )
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Data Type
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                sensor.data_type ||
                                "—"
                            )
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Unit
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                sensor.unit ||
                                "—"
                            )
                        }
                    </strong>
                </div>

            </div>


            <h4>LIVE VALUE</h4>

            <div class="sensor-detail-live">

                <strong>
                    ${
                        gateway.escape(
                            sensor.value ??
                            sensor.text_value ??
                            "—"
                        )
                    }
                </strong>

                <span>
                    ${
                        gateway.escape(
                            sensor.unit ||
                            ""
                        )
                    }
                </span>

            </div>


            <h4>STATUS</h4>

            <div class="detail-grid">

                <div>
                    <small>
                        Quality
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                sensor.quality ||
                                "GOOD"
                            )
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Status
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                sensor.status ||
                                "NORMAL"
                            )
                        }
                    </strong>
                </div>

            </div>


            <h4>ALARM THRESHOLDS</h4>

            <div class="detail-grid">

                <div>
                    <small>
                        Low Alarm
                    </small>

                    <strong>
                        ${
                            sensor.low_alarm ??
                            "Disabled"
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        High Alarm
                    </small>

                    <strong>
                        ${
                            sensor.high_alarm ??
                            "Disabled"
                        }
                    </strong>
                </div>

            </div>


            <h4>DISPLAY</h4>

            <div class="detail-grid">

                <div>
                    <small>
                        Display
                    </small>

                    <strong>
                        ${
                            sensor.display_enabled
                                ? "Enabled"
                                : "Disabled"
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Graph
                    </small>

                    <strong>
                        ${
                            sensor.graph_enabled
                                ? "Enabled"
                                : "Disabled"
                        }
                    </strong>
                </div>

            </div>


            <div style="
                margin-top:22px;
                display:flex;
                gap:8px;
            ">

                <button
                    class="btn btn-primary"
                    id="sensor-graph-button">

                    View Graph

                </button>


                <button
                    class="btn btn-secondary"
                    id="sensor-edit-button">

                    Edit

                </button>

            </div>

        `;


        drawer.classList.add("open");
        overlay.classList.add("open");


        document
            .getElementById(
                "sensor-graph-button"
            )
            ?.addEventListener(
                "click",
                () => openGraph(sensor)
            );


        document
            .getElementById(
                "sensor-edit-button"
            )
            ?.addEventListener(
                "click",
                () => openSensorEdit(sensor)
            );

    }


    /* =========================================
       EDIT PARAMETER
    ========================================= */

    function openSensorEdit(sensor) {

        const details = document.getElementById("sensor-details");
        if (!details) return;

        details.innerHTML = `
            <form id="sensor-edit-form">
                <h4>GENERAL</h4>
                <div class="detail-grid">
                    <label>Parameter Name<input class="input" name="parameter_name" value="${gateway.escape(sensor.parameter_name || "")}" required></label>
                    <label>Parameter Type<input class="input" name="parameter_type" value="${gateway.escape(sensor.parameter_type || "")}" required></label>
                    <label>Data Type<input class="input" name="data_type" value="${gateway.escape(sensor.data_type || "FLOAT")}" required></label>
                    <label>Unit<input class="input" name="unit" value="${gateway.escape(sensor.unit || "")}"></label>
                    <label>Sensor ID<input class="input" name="sensor_id" value="${gateway.escape(sensor.sensor_id || "")}"></label>
                    <label>Description<input class="input" name="description" value="${gateway.escape(sensor.description || "")}"></label>
                </div>

                <h4>DATA</h4>
                <div class="detail-grid">
                    <label>Decimal Places<input class="input" type="number" name="decimal_places" value="${sensor.decimal_places ?? 2}"></label>
                    <label>Minimum<input class="input" type="number" name="min_value" value="${sensor.min_value ?? ""}"></label>
                    <label>Maximum<input class="input" type="number" name="max_value" value="${sensor.max_value ?? ""}"></label>
                </div>

                <h4>DISPLAY</h4>
                <div class="detail-grid">
                    <label class="switch-row"><span>Enabled</span><input type="checkbox" name="enabled" ${sensor.enabled ? "checked" : ""}></label>
                    <label class="switch-row"><span>Display Enabled</span><input type="checkbox" name="display_enabled" ${sensor.display_enabled ? "checked" : ""}></label>
                    <label class="switch-row"><span>Graph Enabled</span><input type="checkbox" name="graph_enabled" ${sensor.graph_enabled ? "checked" : ""}></label>
                </div>

                <h4>ALARM</h4>
                <div class="detail-grid">
                    <label class="switch-row"><span>Alarm Enabled</span><input type="checkbox" name="alarm_enabled" ${sensor.alarm_enabled ? "checked" : ""}></label>
                    <label>Low Alarm<input class="input" type="number" name="low_alarm" value="${sensor.low_alarm ?? ""}"></label>
                    <label>High Alarm<input class="input" type="number" name="high_alarm" value="${sensor.high_alarm ?? ""}"></label>
                </div>

                <div class="drawer-footer" style="margin-top:18px">
                    <button type="button" class="btn btn-secondary" id="sensor-edit-cancel">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Parameter</button>
                </div>
            </form>
        `;

        document.getElementById("sensor-edit-cancel")?.addEventListener("click", () => openSensorDrawer(sensor));
        document.getElementById("sensor-edit-form")?.addEventListener("submit", async event => {
            event.preventDefault();
            const form = event.currentTarget;
            const payload = {
                parameter_name: form.elements.parameter_name.value.trim(),
                parameter_type: form.elements.parameter_type.value.trim(),
                data_type: form.elements.data_type.value.trim(),
                unit: form.elements.unit.value.trim(),
                sensor_id: form.elements.sensor_id.value.trim() || null,
                description: form.elements.description.value.trim(),
                decimal_places: Number(form.elements.decimal_places.value) || 0,
                min_value: form.elements.min_value.value === "" ? null : Number(form.elements.min_value.value),
                max_value: form.elements.max_value.value === "" ? null : Number(form.elements.max_value.value),
                enabled: form.elements.enabled.checked,
                display_enabled: form.elements.display_enabled.checked,
                graph_enabled: form.elements.graph_enabled.checked,
                alarm_enabled: form.elements.alarm_enabled.checked,
                low_alarm: form.elements.low_alarm.value === "" ? null : Number(form.elements.low_alarm.value),
                high_alarm: form.elements.high_alarm.value === "" ? null : Number(form.elements.high_alarm.value)
            };
            try {
                await gateway.put(`/api/nodes/${encodeURIComponent(sensor.node_id)}/parameters/${encodeURIComponent(sensor.parameter_id)}`, payload);
                gateway.toast("Parameter updated successfully", "success");
                await loadSensors();
                const updated = sensors.find(item => item.parameter_id === sensor.parameter_id);
                if (updated) openSensorDrawer(updated);
            } catch (error) {
                console.error("Sensor edit error:", error);
                gateway.toast(error.message || "Unable to update parameter", "error");
            }
        });
    }


    /* =========================================
       GRAPH
    ========================================= */

    async function openGraph(sensor) {

        const details =
            document.getElementById(
                "sensor-details"
            );


        if (!details) return;


        /*
         * Load existing graph configuration
         * from your backend.
         */
        let graph = null;


        try {

            const response =
                await gateway.get(
                    `/api/nodes/${encodeURIComponent(
                        selectedNode
                    )}/parameters/${encodeURIComponent(
                        sensor.parameter_id
                    )}/graph`
                );

            graph =
                response.graph || null;

        } catch (error) {

            console.warn(
                "Graph configuration unavailable:",
                error
            );

        }


        details.innerHTML = `

            <h4>GRAPH VIEW</h4>

            <div class="graph-summary">

                <div>
                    <small>Current</small>
                    <strong>
                        ${
                            sensor.value ??
                            "—"
                        }
                    </strong>
                </div>

                <div>
                    <small>Min</small>
                    <strong id="graph-min">
                        —
                    </strong>
                </div>

                <div>
                    <small>Max</small>
                    <strong id="graph-max">
                        —
                    </strong>
                </div>

                <div>
                    <small>Average</small>
                    <strong id="graph-average">
                        —
                    </strong>
                </div>

            </div>


            <div class="graph-placeholder">
                <svg id="sensor-graph-svg" viewBox="0 0 800 260" preserveAspectRatio="none" aria-label="Sensor telemetry graph">
                    <polyline id="sensor-graph-line" fill="none" stroke="currentColor" stroke-width="3" points="" />
                </svg>
            </div>


            <h4>GRAPH SETTINGS</h4>

            <div class="detail-grid">

                <div>
                    <small>
                        Graph Type
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                graph?.graph_type ||
                                "line"
                            )
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Time Range
                    </small>

                    <strong>
                        ${
                            gateway.escape(
                                graph?.time_range ||
                                "1h"
                            )
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Max Points
                    </small>

                    <strong>
                        ${
                            graph?.max_points ||
                            300
                        }
                    </strong>
                </div>


                <div>
                    <small>
                        Animation
                    </small>

                    <strong>
                        ${
                            graph?.animation_enabled
                                ? "Enabled"
                                : "Disabled"
                        }
                    </strong>
                </div>

            </div>


            <div style="
                margin-top:20px;
            ">

                <button
                    class="btn btn-secondary"
                    id="graph-back">

                    ← Sensor Details

                </button>

            </div>

        `;


        /*
         * Load telemetry and calculate statistics.
         */
        loadGraphData(sensor);


        document
            .getElementById("graph-back")
            ?.addEventListener(
                "click",
                () =>
                    openSensorDrawer(sensor)
            );

    }


    /* =========================================
       GRAPH DATA
    ========================================= */

    async function loadGraphData(sensor) {

        try {

            const response =
                await gateway.get(
                    `/api/nodes/${encodeURIComponent(
                        selectedNode
                    )}/telemetry/${encodeURIComponent(
                        sensor.parameter_id
                    )}`
                );


            const data =
                response.data || [];


            const values =
                data
                    .map(item =>
                        Number(item.value)
                    )
                    .filter(
                        value =>
                            Number.isFinite(value)
                    );


            if (!values.length) {
                return;
            }


            const min =
                Math.min(...values);

            const max =
                Math.max(...values);

            const average =
                values.reduce(
                    (sum, value) =>
                        sum + value,
                    0
                ) / values.length;


            const minElement =
                document.getElementById(
                    "graph-min"
                );

            const maxElement =
                document.getElementById(
                    "graph-max"
                );

            const averageElement =
                document.getElementById(
                    "graph-average"
                );


            if (minElement)
                minElement.textContent =
                    formatValue(
                        min,
                        sensor
                    );


            if (maxElement)
                maxElement.textContent =
                    formatValue(
                        max,
                        sensor
                    );


            if (averageElement)
                averageElement.textContent =
                    formatValue(
                        average,
                        sensor
                    );

            const line = document.getElementById("sensor-graph-line");
            if (line) {
                const width = 800;
                const height = 240;
                const pad = 20;
                const range = max - min || 1;
                const points = values.slice(-100).map((value, index, arr) => {
                    const x = pad + (index / Math.max(arr.length - 1, 1)) * (width - pad * 2);
                    const y = height - pad - ((value - min) / range) * (height - pad * 2);
                    return `${x.toFixed(1)},${y.toFixed(1)}`;
                }).join(" ");
                line.setAttribute("points", points);
            }


        } catch (error) {

            console.warn(
                "Telemetry unavailable:",
                error
            );

        }

    }


    function formatValue(
        value,
        sensor
    ) {

        const decimals =
            Number.isFinite(
                Number(
                    sensor.decimal_places
                )
            )
                ? Number(
                    sensor.decimal_places
                )
                : 2;


        return Number(value)
            .toFixed(decimals);

    }


    /* =========================================
       CLOSE DRAWER
    ========================================= */

    function closeDrawer() {

        document
            .getElementById(
                "sensor-drawer"
            )
            ?.classList.remove(
                "open"
            );


        document
            .getElementById(
                "sensor-overlay"
            )
            ?.classList.remove(
                "open"
            );

    }


    /* =========================================
       EMPTY / ERROR
    ========================================= */

    function emptyRow(message) {

        return `
            <tr>

                <td colspan="7"
                    class="loading">

                    <div style="
                        font-size:25px;
                        color:#E87522;
                        margin-bottom:8px;
                    ">
                        ◉
                    </div>

                    <strong>
                        ${gateway.escape(message)}
                    </strong>

                </td>

            </tr>
        `;

    }


    function errorRow() {

        return `
            <tr>

                <td colspan="7"
                    class="loading">

                    <strong>
                        Unable to load sensor parameters
                    </strong>

                    <br><br>

                    <button
                        class="btn btn-secondary"
                        id="sensor-retry">

                        Retry

                    </button>

                </td>

            </tr>
        `;

    }

});
