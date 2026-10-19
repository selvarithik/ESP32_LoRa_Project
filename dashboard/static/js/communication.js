"use strict";

/*
 * ============================================================
 * COMMUNICATION CENTER
 * ============================================================
 *
 * Uses the existing gateway API layer from app.js.
 *
 * No duplicate fetch()
 * No duplicate API helper
 * No independent styling system
 *
 * ============================================================
 */


const CommunicationCenter = (() => {

    const state = {
        status: null,
        mesh: null,
        settings: null
    };


    /* ========================================================
       ELEMENT HELPER
    ======================================================== */

    function element(id) {

        return document.getElementById(id);

    }


    /* ========================================================
       SET TEXT
    ======================================================== */

    function setText(id, value) {

        const el = element(id);

        if (!el) {
            return;
        }

        el.textContent =
            value === null ||
            value === undefined ||
            value === ""
                ? "—"
                : String(value);

    }


    /* ========================================================
       NUMBER
    ======================================================== */

    function number(value, fallback = 0) {

        const result = Number(value);

        return Number.isFinite(result)
            ? result
            : fallback;

    }


    /* ========================================================
       LOAD STATUS
    ======================================================== */

    async function loadStatus(updateSettings = true) {

        try {

            const response =
                await gateway.get(
                    "/api/communication/status"
                );


            state.status =
                response || {};


            const master =
                response.master_node_id;


            const gatewayConnection =
                response.gateway_connection ||
                {};


            const settings =
                response.mesh_settings ||
                {};


            state.settings =
                settings;


            setText(
                "communication-master",
                master || "Not configured"
            );


            setText(
                "communication-gateway",
                gatewayConnection.enabled
                    ? gatewayConnection.type || "—"
                    : "Disabled"
            );


            setText(
                "communication-uplink",
                `${number(
                    settings.uplink_threshold
                )}%`
            );


            setText(
                "communication-downlink",
                `${number(
                    settings.downlink_threshold
                )}%`
            );


            loadStatistics(
                response.statistics || {}
            );


            if (updateSettings) loadSettingsForm(
                settings
            );


        } catch (error) {

            console.error(
                "Communication status error:",
                error
            );


            gateway.toast(
                error.message ||
                "Unable to load communication status",
                "error"
            );

        }

    }


    /* ========================================================
       STATISTICS
    ======================================================== */

    function loadStatistics(
        statistics
    ) {

        setText(
            "packets-created",
            number(
                statistics.packets_created
            )
        );


        setText(
            "packets-sent",
            number(
                statistics.packets_sent
            )
        );


        setText(
            "packets-received",
            number(
                statistics.packets_received
            )
        );


        setText(
            "packets-failed",
            number(
                statistics.packets_failed
            )
        );


        setText(
            "ack-received",
            number(
                statistics.ack_received
            )
        );


        setText(
            "packet-retries",
            number(
                statistics.retries
            )
        );


        setText(
            "route-failures",
            number(
                statistics.route_failures
            )
        );


        setText(
            "duplicates-dropped",
            number(
                statistics.duplicates_dropped
            )
        );

    }


    /* ========================================================
       LOAD MESH
    ======================================================== */

    function renderTopology(mesh, nodes) {
        const svg = element("mesh-topology-svg");
        if (!svg) return;
        svg.replaceChildren();
        const ns = "http://www.w3.org/2000/svg";
        function shape(tag, attributes, text) {
            const el = document.createElementNS(ns, tag);
            Object.entries(attributes).forEach(([key, value]) => el.setAttribute(key, value));
            if (text !== undefined) el.textContent = text;
            svg.appendChild(el);
            return el;
        }
        if (!nodes.length) { shape("text", { x: 450, y: 210, "text-anchor": "middle", fill: "currentColor" }, "No mesh nodes configured"); return; }
        const positions = new Map(nodes.map((node, index) => {
            const angle = index * Math.PI * 2 / nodes.length;
            return [node.node_id, { x: 450 + 300 * Math.cos(angle), y: 210 + 145 * Math.sin(angle), node }];
        }));
        const drawn = new Set();
        Object.entries(mesh.neighbors || {}).forEach(([source, neighbors]) => {
            Object.entries(neighbors || {}).forEach(([target, link]) => {
                const a = positions.get(source), b = positions.get(target);
                const key = [source, target].sort().join("::");
                if (!a || !b || drawn.has(key)) return;
                drawn.add(key);
                const line = shape("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: "var(--m-blue)", "stroke-width": 2 });
                const title = document.createElementNS(ns, "title");
                title.textContent = source + " - " + target + " / RSSI " + (link.rssi ?? "unknown");
                line.appendChild(title);
            });
        });
        positions.forEach(({x, y, node}) => {
            shape("circle", { cx: x, cy: y, r: 23, fill: node.node_id === mesh.master_node_id ? "var(--m-orange)" : "var(--m-blue)" });
            shape("text", { x, y: y + 43, "text-anchor": "middle", fill: "currentColor", "font-size": 14 }, node.name || node.node_id);
        });
    }

    async function loadMesh() {

        const tbody =
            element(
                "communication-nodes"
            );


        if (!tbody) {
            return;
        }


        try {

            const response =
                await gateway.get(
                    "/api/communication/mesh"
                );


            state.mesh =
                response || {};


            const mesh =
                response.mesh ||
                response;


           let nodes = mesh.nodes;


/*
 * Server returns nodes as an object:
 *
 * {
 *     "NODE-001": {...},
 *     "NODE-002": {...}
 * }
 *
 * Convert object to array for the table.
 */

             if (
                 nodes &&
                 !Array.isArray(nodes) &&
                 typeof nodes === "object"
                 ) {

             nodes = Object.values(nodes);

            }


             if (!Array.isArray(nodes)) {

                 nodes =
                    Array.isArray(response.nodes)
                  ? response.nodes
                  : [];

                }



            renderTopology(mesh, nodes);
            tbody.innerHTML = "";


            if (!nodes.length) {

                tbody.innerHTML = `
                    <tr>
                        <td
                            colspan="5"
                            class="loading"
                        >
                            No mesh nodes configured.
                        </td>
                    </tr>
                `;

                return;
            }


            nodes.forEach(
                node => {

                    tbody.appendChild(
                        createNodeRow(
                            node
                        )
                    );

                }
            );


        } catch (error) {

            console.error(
                "Mesh loading error:",
                error
            );


            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="5"
                        class="loading"
                    >
                        Unable to load mesh.
                    </td>
                </tr>
            `;


            gateway.toast(
                error.message ||
                "Unable to load mesh",
                "error"
            );

        }

    }


    /* ========================================================
       CREATE NODE ROW
    ======================================================== */

    function createNodeRow(
        node
    ) {

        const tr =
            document.createElement(
                "tr"
            );


        const nodeId =
            node.node_id ||
            "—";


        const role =
            node.role ||
            "NODE";


        const online =
            node.online === true;


        const statusClass =
            online
                ? "status-online"
                : "status-offline";


        const statusText =
            online
                ? "Online"
                : "Offline";


        const neighbors =
            Array.isArray(
                node.neighbors
            )
                ? node.neighbors.length
                : number(
                    node.neighbor_count
                );


        tr.innerHTML = `

            <td>
                <strong>
                    ${gateway.escape(nodeId)}
                </strong>
            </td>

            <td>
                ${gateway.escape(role)}
            </td>

            <td>
                <span class="${statusClass}">
                    ${statusText}
                </span>
            </td>

            <td>
                ${gateway.escape(
                    node.last_seen || "—"
                )}
            </td>

            <td>
                ${neighbors}
            </td>

        `;


        return tr;

    }


    /* ========================================================
       LOAD SETTINGS INTO FORM
    ======================================================== */

    function loadSettingsForm(
        settings
    ) {

        const uplink =
            element(
                "uplink-threshold"
            );


        const downlink =
            element(
                "downlink-threshold"
            );


        const retry =
            element(
                "retry-count"
            );


        const hops =
            element(
                "max-hops"
            );


        if (uplink) {

            uplink.value =
                number(
                    settings.uplink_threshold,
                    30
                );

        }


        if (downlink) {

            downlink.value =
                number(
                    settings.downlink_threshold,
                    30
                );

        }


        if (retry) {

            retry.value =
                number(
                    settings.retry_count,
                    3
                );

        }


        if (hops) {

            hops.value =
                number(
                    settings.max_hops,
                    5
                );

        }

    }


    /* ========================================================
       SAVE SETTINGS
    ======================================================== */

    async function saveSettings(
        event
    ) {

        event.preventDefault();


        const uplink =
            number(
                element(
                    "uplink-threshold"
                )?.value
            );


        const downlink =
            number(
                element(
                    "downlink-threshold"
                )?.value
            );


        const retry =
            number(
                element(
                    "retry-count"
                )?.value
            );


        const hops =
            number(
                element(
                    "max-hops"
                )?.value
            );


        if (
            uplink < 0 ||
            uplink > 100 ||
            downlink < 0 ||
            downlink > 100
        ) {

            gateway.toast(
                "Success rate must be between 0% and 100%.",
                "error"
            );

            return;

        }


        try {

            await gateway.put(
                "/api/communication/settings",
                {
                    uplink_threshold:
                        uplink,

                    downlink_threshold:
                        downlink,

                    retry_count:
                        retry,

                    max_hops:
                        hops
                }
            );


            gateway.toast(
                "Communication settings saved successfully.",
                "success"
            );


            await loadStatus();


        } catch (error) {

            console.error(
                "Communication settings error:",
                error
            );


            gateway.toast(
                error.message ||
                "Unable to save communication settings",
                "error"
            );

        }

    }


    /* ========================================================
       ROUTE TEST
    ======================================================== */

    async function testRoute() {

        const source =
            element(
                "route-source"
            )?.value.trim();


        const destination =
            element(
                "route-destination"
            )?.value.trim();


        const direction =
            element(
                "route-direction"
            )?.value;


        const result =
            element(
                "route-result"
            );


        if (!source) {

            gateway.toast(
                "Enter source node.",
                "error"
            );

            return;

        }


        if (!destination) {

            gateway.toast(
                "Enter destination node.",
                "error"
            );

            return;

        }


        if (!result) {
            return;
        }


        result.textContent =
            "Checking route...";


        try {

            const params =
                new URLSearchParams({

                    source:
                        source,

                    destination:
                        destination,

                    direction:
                        direction

                });


            const response =
                await gateway.get(
                    `/api/communication/route?${params.toString()}`
                );


            const route =
                response.route ||
                {};


            if (
                response.success === false ||
                route.success === false
            ) {

                result.innerHTML = `

                    <strong>
                        Route unavailable
                    </strong>

                    <br>

                    ${gateway.escape(
                        route.error ||
                        response.error ||
                        "No route available."
                    )}

                `;

                return;

            }


            const mode =
                route.mode ||
                "unknown";


            const nextHop =
                route.next_hop ||
                "—";


            const hopCount =
                route.hop_count ??
                "—";


            const score =
                route.score ??
                "—";


            const threshold =
                route.threshold ??
                "—";


            const successRate =
                route.success_rate ??
                "—";


            let routePath =
                "";


            if (
                route.path &&
                Array.isArray(
                    route.path
                )
            ) {

                routePath =
                    route.path.join(
                        " → "
                    );

            }


            result.innerHTML = `

                <strong>
                    ${
                        mode === "relay"
                            ? "Relay Route"
                            : "Direct Route"
                    }
                </strong>

                <div style="margin-top:8px;">

                    Next Hop:
                    <strong>
                        ${gateway.escape(
                            nextHop
                        )}
                    </strong>

                    &nbsp; | &nbsp;

                    Hops:
                    <strong>
                        ${gateway.escape(
                            String(hopCount)
                        )}
                    </strong>

                    &nbsp; | &nbsp;

                    Score:
                    <strong>
                        ${gateway.escape(
                            String(score)
                        )}
                    </strong>

                </div>


                <div style="margin-top:6px;">

                    Threshold:
                    ${gateway.escape(
                        String(threshold)
                    )}%

                    &nbsp; | &nbsp;

                    Success Rate:
                    ${gateway.escape(
                        String(successRate)
                    )}%

                </div>


                ${
                    routePath
                        ? `
                            <div
                                style="margin-top:8px;"
                            >
                                Path:
                                <strong>
                                    ${gateway.escape(
                                        routePath
                                    )}
                                </strong>
                            </div>
                          `
                        : ""
                }

            `;


        } catch (error) {

            console.error(
                "Route test error:",
                error
            );


            result.innerHTML = `

                <strong>
                    Route test failed
                </strong>

                <br>

                ${gateway.escape(
                    error.message ||
                    "Unable to check route."
                )}

            `;

        }

    }

    /* ========================================================
   LOAD MESH LINKS
======================================================== */

async function loadLinks() {

    const tbody =
        element(
            "communication-links"
        );


    if (!tbody) {
        return;
    }


    try {

        const response =
            await gateway.get(
                "/api/communication/mesh"
            );


        const mesh =
            response.mesh ||
            response;


        const neighbors =
            mesh.neighbors ||
            {};


        tbody.innerHTML = "";


        let linkCount = 0;


        Object.entries(
            neighbors
        ).forEach(
            ([nodeId, nodeLinks]) => {

                if (
                    !nodeLinks ||
                    typeof nodeLinks !== "object"
                ) {
                    return;
                }


                Object.entries(
                    nodeLinks
                ).forEach(
                    ([neighborId, link]) => {

                        if (
                            !link ||
                            typeof link !== "object"
                        ) {
                            return;
                        }


                        linkCount++;


                        const tr =
                            document.createElement(
                                "tr"
                            );


                        tr.innerHTML = `

                            <td>
                                <strong>
                                    ${gateway.escape(
                                        nodeId
                                    )}
                                </strong>
                            </td>

                            <td>
                                ${gateway.escape(
                                    neighborId
                                )}
                            </td>

                            <td>
                                ${number(
                                    link.rssi
                                )} dBm
                            </td>

                            <td>
                                ${number(
                                    link.snr
                                )} dB
                            </td>

                            <td>
                                ${number(
                                    link.success_rate
                                )}%
                            </td>

                            <td>
                                ${number(
                                    link.packet_loss
                                )}%
                            </td>

                            <td>
                                ${number(
                                    link.latency_ms
                                )} ms
                            </td>

                            <td>
                                ${number(
                                    link.retries
                                )}
                            </td>

                        `;


                        tbody.appendChild(
                            tr
                        );

                    }
                );

            }
        );


        if (linkCount === 0) {

            tbody.innerHTML = `

                <tr>

                    <td
                        colspan="8"
                        class="loading"
                    >
                        No mesh links available.
                    </td>

                </tr>

            `;

        }


    } catch (error) {

        console.error(
            "Mesh link loading error:",
            error
        );


        tbody.innerHTML = `

            <tr>

                <td
                    colspan="8"
                    class="loading"
                >
                    Unable to load mesh links.
                </td>

            </tr>

        `;

    }

}
    /* ========================================================
       REFRESH
    ======================================================== */

    async function refresh() {

          await Promise.all([
          loadStatus(),
          loadMesh(),
          loadLinks()
         ]);

         }


    /* ========================================================
       BIND EVENTS
    ======================================================== */

    function bindEvents() {

        const refreshButton =
            element(
                "communication-refresh"
            );


        if (refreshButton) {

            refreshButton.addEventListener(
                "click",
                refresh
            );

        }


        const settingsForm =
            element(
                "communication-settings-form"
            );


        if (settingsForm) {

            settingsForm.addEventListener(
                "submit",
                saveSettings
            );

        }


        const routeButton =
            element(
                "route-test"
            );


        if (routeButton) {

            routeButton.addEventListener(
                "click",
                testRoute
            );

        }

    }


    /* ========================================================
       INIT
    ======================================================== */

    function init() {

        bindEvents();

        refresh();
        gateway.watch(() => Promise.all([loadStatus(false), loadMesh()]), {immediate:false});

    }


    return {
        init,
        refresh
    };


})();


/* ============================================================
   START
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        CommunicationCenter.init();

    }
);
