"use strict";

document.addEventListener("DOMContentLoaded", () => {

    const nodesTable =
        document.getElementById("dashboard-nodes");

    if (!nodesTable) {
        return;
    }

    let selectedNode = null;
    let refreshTimer = null;


    /* =========================================
       START DASHBOARD
    ========================================= */

    initDashboard();


    async function initDashboard() {

        const refreshButton =
            document.getElementById(
                "dashboard-refresh"
            );

        if (refreshButton) {
            refreshButton.addEventListener(
                "click",
                loadDashboard
            );
        }

        await loadDashboard();

        /*
         * Refresh sensor/node data every 3 seconds.
         * This does NOT refresh the webpage.
         */
        if (refreshTimer) {

            clearInterval(
                refreshTimer
            );

        }


        refreshTimer =
            setInterval(
                loadDashboard,
                2000
            );
    }


    /* =========================================
       LOAD NODES
    ========================================= */

    async function loadDashboard() {

        try {

            const response =
                await gateway.get(
                    "/api/nodes"
                );

            const nodes =
                Array.isArray(response)
                    ? response
                    : response.nodes || [];


            updateStatistics(nodes);

            renderNodes(nodes);


            /*
             * Select first node automatically
             */
            if (
                !selectedNode &&
                nodes.length > 0
            ) {
                selectedNode =
                    nodes[0].node_id;
            }


            if (selectedNode) {

                await loadSensors(
                    selectedNode
                );

            } else {

                showNoNode();

            }


        } catch (error) {

            console.error(
                "Dashboard error:",
                error
            );

            showDashboardError();

            gateway.toast(
                "Unable to load dashboard data",
                "error"
            );
        }
    }


    /* =========================================
       STATISTICS
    ========================================= */

    function updateStatistics(nodes) {

        const total =
            document.getElementById(
                "total-nodes"
            );

        const online =
            document.getElementById(
                "online-nodes"
            );

        const sensorCount =
            document.getElementById(
                "sensor-count"
            );

        const alarmCount =
            document.getElementById(
                "alarm-count"
            );


        const onlineNodes =
            nodes.filter(node =>
                gateway.status(
                    node.status
                ) === "online"
            );


        if (total) {
            total.textContent =
                nodes.length;
        }


        if (online) {
            online.textContent =
                onlineNodes.length;
        }


        /*
         * Sensor count and alarms will be updated
         * after sensor data is loaded.
         */
        if (
            sensorCount &&
            sensorCount.textContent === "—"
        ) {
            sensorCount.textContent = "0";
        }


        if (
            alarmCount &&
            alarmCount.textContent === "—"
        ) {
            alarmCount.textContent = "0";
        }
    }


    /* =========================================
       NODE TABLE
    ========================================= */

    function renderNodes(nodes) {

        if (!nodes.length) {

            nodesTable.innerHTML = `
                <tr>
                    <td colspan="4"
                        class="loading">

                        <div style="
                            font-size:24px;
                            margin-bottom:8px;
                        ">
                            ⌁
                        </div>

                        <strong>
                            No Nodes Configured
                        </strong>

                        <div style="
                            margin-top:5px;
                            font-size:9px;
                        ">
                            Add a node from Node Management.
                        </div>

                    </td>
                </tr>
            `;

            return;
        }


        nodesTable.innerHTML =
            nodes.map(node => {

                const status =
                    gateway.status(
                        node.status
                    );


                const isSelected =
                    selectedNode ===
                    node.node_id;


                return `
                    <tr
                        class="${
                            isSelected
                                ? "dashboard-node-selected"
                                : ""
                        }"
                        data-node-id="${
                            gateway.escape(
                                node.node_id
                            )
                        }"
                        style="${
                            isSelected
                                ? `
                                    background:#FFF1E7;
                                    border-left:3px solid #E87522;
                                  `
                                : ""
                        }"
                    >

                        <td>

                            <div style="
                                display:flex;
                                align-items:center;
                                gap:9px;
                            ">

                                <div style="
                                    width:30px;
                                    height:30px;
                                    display:flex;
                                    align-items:center;
                                    justify-content:center;
                                    border-radius:7px;
                                    background:#F2F4F7;
                                    color:#17212B;
                                    font-weight:700;
                                ">
                                    ◉
                                </div>

                                <div>

                                    <strong style="
                                        display:block;
                                        font-size:10px;
                                    ">
                                        ${
                                            gateway.escape(
                                                node.name ||
                                                node.node_id
                                            )
                                        }
                                    </strong>

                                    <small style="
                                        color:#98A2B3;
                                        font-size:8px;
                                    ">
                                        ${
                                            gateway.escape(
                                                node.node_id
                                            )
                                        }
                                    </small>

                                </div>

                            </div>

                        </td>


                        <td>
                            ${
                                gateway.escape(
                                    node.communication_type ||
                                    "—"
                                )
                            }
                        </td>


                        <td>

                            <span class="
                                status ${status}
                            ">

                                ${status.toUpperCase()}

                            </span>

                        </td>


                        <td>

                            ${
                                gateway.time(
                                    node.last_seen
                                )
                            }

                        </td>

                    </tr>
                `;

            }).join("");


        /*
         * Clicking a node changes the selected node.
         */
        nodesTable
            .querySelectorAll(
                "tr[data-node-id]"
            )
            .forEach(row => {

                row.addEventListener(
                    "click",
                    async () => {

                        selectedNode =
                            row.dataset.nodeId;

                        renderNodes(nodes);

                        await loadSensors(
                            selectedNode
                        );
                    }
                );

            });
    }


    /* =========================================
       LOAD SENSOR DATA
    ========================================= */

    async function loadSensors(nodeId) {

        const sensorContainer =
            document.getElementById(
                "dashboard-sensors"
            );

        const selectedNodeLabel =
            document.getElementById(
                "selected-node"
            );


        if (!sensorContainer) {
            return;
        }


        if (selectedNodeLabel) {
            selectedNodeLabel.textContent =
                `Node: ${nodeId}`;
        }


        try {

            /*
             * Your backend already supports:
             *
             * /api/nodes/NODE-002/parameters
             */

            const response =
                 await gateway.get(
                  `/api/nodes/${encodeURIComponent(
                     nodeId
                   )}/parameters/latest`
                );


            const parameters =
                response.parameters || [];


            updateSensorStatistics(
                parameters
            );


            renderSensors(
                parameters
            );


        } catch (error) {

            console.error(
                "Sensor loading error:",
                error
            );


            sensorContainer.innerHTML = `
                <div class="empty-state"
                     style="
                        grid-column:1/-1;
                        padding:30px;
                        text-align:center;
                     ">

                    Unable to load sensor data.

                </div>
            `;
        }
    }


    /* =========================================
       SENSOR STATISTICS
    ========================================= */

    function updateSensorStatistics(
        parameters
    ) {

        const sensorCount =
            document.getElementById(
                "sensor-count"
            );

        const alarmCount =
            document.getElementById(
                "alarm-count"
            );


        const visibleParameters =
            parameters.filter(
                parameter =>
                    parameter.enabled !== false &&
                    parameter.display_enabled !== false
            );


        const alarms =
            parameters.filter(
                parameter =>
                    parameter.alarm_status === "ALARM" ||
                    parameter.status === "ALARM"
            );


        if (sensorCount) {

            sensorCount.textContent =
                visibleParameters.length;
        }


        if (alarmCount) {

            alarmCount.textContent =
                alarms.length;
        }
    }


    /* =========================================
       SENSOR CARDS
    ========================================= */

    function renderSensors(parameters) {

        const container =
            document.getElementById(
                "dashboard-sensors"
            );


        if (!container) {
            return;
        }


        const visible =
            parameters.filter(
                parameter =>
                    parameter.enabled !== false &&
                    parameter.display_enabled !== false
            );


        if (!visible.length) {

            container.innerHTML = `
                <div class="empty-state"
                     style="
                        grid-column:1/-1;
                        text-align:center;
                        padding:30px;
                     ">

                    No sensor parameters configured.

                </div>
            `;

            return;
        }


        container.innerHTML =
            visible.map(parameter => {

                const status =
                    gateway.status(
                        parameter.alarm_status ||
                        parameter.status
                    );


                const value =
                    parameter.value ??
                    parameter.text_value ??
                    "—";


                return `
                    <div class="sensor-card">

                        <div class="sensor-card-name">

                            ${
                                gateway.escape(
                                    parameter.parameter_name ||
                                    parameter.parameter_id
                                )
                            }

                        </div>


                        <div class="sensor-value">

                            ${
                                gateway.escape(
                                    value
                                )
                            }

                            <span class="sensor-unit">

                                ${
                                    gateway.escape(
                                        parameter.unit ||
                                        ""
                                    )
                                }

                            </span>

                        </div>


                        <div class="sensor-footer">

                            <span class="quality-good">

                                ${
                                    gateway.escape(
                                        parameter.quality ||
                                        "GOOD"
                                    )
                                }

                            </span>


                            <span class="
                                status ${status}
                            ">

                                ${status.toUpperCase()}

                            </span>

                        </div>

                    </div>
                `;

            }).join("");
    }


    /* =========================================
       NO NODE
    ========================================= */

    function showNoNode() {

        const container =
            document.getElementById(
                "dashboard-sensors"
            );

        if (!container) {
            return;
        }

        container.innerHTML = `
            <div class="empty-state"
                 style="
                    grid-column:1/-1;
                    text-align:center;
                    padding:30px;
                 ">

                Select a node to view
                live sensor data.

            </div>
        `;
    }


    /* =========================================
       ERROR
    ========================================= */

    function showDashboardError() {

        if (nodesTable) {

            nodesTable.innerHTML = `
                <tr>
                    <td colspan="4"
                        class="loading">

                        Unable to load node data.

                        <br><br>

                        <button
                            class="btn btn-secondary"
                            id="dashboard-retry">

                            Retry

                        </button>

                    </td>
                </tr>
            `;


            document
                .getElementById(
                    "dashboard-retry"
                )
                ?.addEventListener(
                    "click",
                    loadDashboard
                );
        }
    }

});
