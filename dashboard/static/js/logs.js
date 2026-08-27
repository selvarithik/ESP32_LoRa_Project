"use strict";

document.addEventListener("DOMContentLoaded", () => {

    const table =
        document.getElementById("logs-table");

    if (!table) return;

    let autoRefresh = false;
    let refreshTimer = null;


    init();


    async function init() {

        bindEvents();
        await loadLogs();

    }


    /* =========================================
       EVENTS
    ========================================= */

    function bindEvents() {

        document
            .getElementById("logs-refresh")
            ?.addEventListener(
                "click",
                loadLogs
            );


        document
            .getElementById("logs-search")
            ?.addEventListener(
                "input",
                loadLogs
            );


        document
            .getElementById("logs-severity")
            ?.addEventListener(
                "change",
                loadLogs
            );


        document
            .getElementById("logs-date")
            ?.addEventListener(
                "change",
                loadLogs
            );


        document
            .getElementById("logs-auto-refresh")
            ?.addEventListener(
                "change",
                event => {

                    autoRefresh =
                        event.target.checked;

                    setupAutoRefresh();

                }
            );


        document
            .getElementById("logs-clear")
            ?.addEventListener(
                "click",
                clearFilters
            );

    }


    /* =========================================
       LOAD LOGS
    ========================================= */

    async function loadLogs() {

        gateway.showLoading(
            table,
            "Loading logs..."
        );


        try {

            const params =
                new URLSearchParams();


            const search =
                document
                    .getElementById(
                        "logs-search"
                    )
                    ?.value
                    ?.trim();


            const severity =
                document
                    .getElementById(
                        "logs-severity"
                    )
                    ?.value;


            const date =
                document
                    .getElementById(
                        "logs-date"
                    )
                    ?.value;


            if (search) {

                params.set(
                    "search",
                    search
                );

            }


            if (
                severity &&
                severity !== "all"
            ) {

                params.set(
                    "severity",
                    severity
                );

            }


            if (date) {

                params.set(
                    "date",
                    date
                );

            }


            const query =
                params.toString();


            /*
             * Try the logs endpoint.
             */
            const response =
                await gateway.get(
                    `/api/logs${
                        query
                            ? "?" + query
                            : ""
                    }`
                );


            const logs =
                Array.isArray(response)
                    ? response
                    : response.logs || [];


            renderLogs(logs);


        } catch (error) {

            console.error(
                "Logs loading error:",
                error
            );


            /*
             * Do not leave a blank page.
             */
            gateway.showError(
                table,
                "Unable to load logs",
                loadLogs
            );


            gateway.toast(
                "Unable to load logs",
                "error"
            );

        }

    }


    /* =========================================
       RENDER
    ========================================= */

    function renderLogs(logs) {

        if (!logs.length) {

            table.innerHTML = `

                <tr>

                    <td colspan="4"
                        class="loading">

                        <div style="
                            font-size:26px;
                            color:#E87522;
                            margin-bottom:8px;
                        ">
                            ≡
                        </div>

                        <strong>
                            No log entries for this filter
                        </strong>

                        <br><br>

                        <button
                            class="btn btn-secondary"
                            id="logs-empty-clear">

                            Clear Filters

                        </button>

                    </td>

                </tr>

            `;


            document
                .getElementById(
                    "logs-empty-clear"
                )
                ?.addEventListener(
                    "click",
                    clearFilters
                );


            return;
        }


        table.innerHTML =
            logs.map(log => {

                const severity =
                    normalizeSeverity(
                        log.severity ||
                        log.level ||
                        "INFO"
                    );


                return `

                    <tr>

                        <td>

                            ${
                                gateway.time(
                                    log.timestamp ||
                                    log.created_at
                                )
                            }

                        </td>


                        <td>

                            <span class="
                                log-severity
                                ${severity}
                            ">

                                ${severity.toUpperCase()}

                            </span>

                        </td>


                        <td>

                            ${
                                gateway.escape(
                                    log.source ||
                                    log.node_id ||
                                    "SYSTEM"
                                )
                            }

                        </td>


                        <td>

                            ${
                                gateway.escape(
                                    log.message ||
                                    log.text ||
                                    "—"
                                )
                            }

                        </td>

                    </tr>

                `;

            }).join("");

    }


    /* =========================================
       SEVERITY
    ========================================= */

    function normalizeSeverity(value) {

        const severity =
            String(value)
                .toLowerCase();


        if (
            severity === "error" ||
            severity === "alarm" ||
            severity === "critical"
        ) {

            return "error";

        }


        if (
            severity === "warning" ||
            severity === "warn"
        ) {

            return "warning";

        }


        return "info";

    }


    /* =========================================
       CLEAR FILTERS
    ========================================= */

    function clearFilters() {

        const search =
            document.getElementById(
                "logs-search"
            );

        const severity =
            document.getElementById(
                "logs-severity"
            );

        const date =
            document.getElementById(
                "logs-date"
            );


        if (search)
            search.value = "";


        if (severity)
            severity.value = "all";


        if (date)
            date.value = "";


        loadLogs();

    }


    /* =========================================
       AUTO REFRESH
    ========================================= */

    function setupAutoRefresh() {

        if (refreshTimer) {

            clearInterval(
                refreshTimer
            );

            refreshTimer = null;

        }


        if (!autoRefresh) {
            return;
        }


        /*
         * Refresh the data only.
         * Never reload the webpage.
         */
        refreshTimer =
            setInterval(
                loadLogs,
                5000
            );

    }

});
