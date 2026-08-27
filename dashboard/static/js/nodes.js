"use strict";

document.addEventListener("DOMContentLoaded", () => {

    const table = document.getElementById("nodes-table");

    if (!table) return;

    let nodes = [];
    let editingNodeId = null;


    /* ============================================================
       INIT
       ============================================================ */

    init();


    async function init() {

        bindEvents();

        await loadNodes();
    }


    /* ============================================================
       EVENTS
       ============================================================ */

    function bindEvents() {

        document
            .getElementById("add-node")
            ?.addEventListener("click", () => {

                openEditDrawer(null);

            });


        document
            .getElementById("node-refresh")
            ?.addEventListener("click", loadNodes);


        document
            .getElementById("node-search")
            ?.addEventListener("input", renderNodes);


        document
            .getElementById("node-drawer-close")
            ?.addEventListener("click", closeDrawer);


        document
            .getElementById("node-cancel")
            ?.addEventListener("click", closeDrawer);


        document
            .getElementById("node-overlay")
            ?.addEventListener("click", closeDrawer);


        document
            .getElementById("node-form")
            ?.addEventListener("submit", saveNode);


        document.addEventListener("click", event => {

            if (
                !event.target.closest(
                    ".node-more-wrap"
                )
            ) {

                closeMoreMenus();

            }

        });


        document.addEventListener("keydown", event => {

            if (event.key === "Escape") {

                closeDrawer();

                closeView();

                closeModal();
            }

        });

    }


    /* ============================================================
       LOAD NODES
       ============================================================ */

    async function loadNodes() {

        gateway.showLoading(
            table,
            "Loading nodes..."
        );

        try {

            const response =
                await gateway.get("/api/nodes");


            nodes =
                Array.isArray(response)
                    ? response
                    : response.nodes || [];


            updateCounters();

            renderNodes();


        } catch (error) {

            console.error(
                "Node loading error:",
                error
            );

            gateway.showError(
                table,
                error.message ||
                "Unable to load nodes",
                loadNodes
            );

            gateway.toast(
                "Unable to load nodes",
                "error"
            );
        }

    }


    /* ============================================================
       COUNTERS
       ============================================================ */

    function updateCounters() {

        const total =
            document.getElementById("node-total");

        const online =
            document.getElementById("node-online");

        const offline =
            document.getElementById("node-offline");

        const disabled =
            document.getElementById("node-disabled");


        const onlineCount =
            nodes.filter(
                node =>
                    isNodeEnabled(node) &&
                    getNodeStatus(node) === "online"
            ).length;


        const disabledCount =
            nodes.filter(
                node => !isNodeEnabled(node)
            ).length;


        const offlineCount =
            nodes.filter(
                node =>
                    getNodeStatus(node) === "offline" &&
                    isNodeEnabled(node)
            ).length;


        if (total)
            total.textContent = nodes.length;


        if (online)
            online.textContent = onlineCount;


        if (offline)
            offline.textContent = offlineCount;


        if (disabled)
            disabled.textContent = disabledCount;
    }


    /* ============================================================
       TABLE
       ============================================================ */

    function renderNodes() {

        const search =
            (
                document.getElementById("node-search")?.value ||
                ""
            )
            .toLowerCase()
            .trim();


        const filtered =
            nodes.filter(node => {

                const text = `
                    ${node.name || ""}
                    ${node.node_id || ""}
                    ${node.mcu_family || ""}
                    ${node.mcu_model || ""}
                    ${node.communication_type || ""}
                    ${node.firmware_version || ""}
                `.toLowerCase();


                return text.includes(search);

            });


        if (!filtered.length) {

            table.innerHTML = `

                <tr>

                    <td
                        colspan="8"
                        class="loading"
                    >

                        <div style="
                            font-size:28px;
                            margin-bottom:8px;
                            color:#E87522;
                        ">
                            +
                        </div>

                        <strong>
                            No Nodes Configured
                        </strong>

                        <div style="
                            margin-top:6px;
                        ">
                            ${
                                search
                                ? "No matching nodes found."
                                : "Add your first gateway node."
                            }
                        </div>

                    </td>

                </tr>
            `;

            return;
        }


        table.innerHTML =
            filtered.map(node => {

                const status =
                    getNodeStatus(node);

                const enabled =
                    isNodeEnabled(node);


                return `

                    <tr>

                        <td>
                            <strong>
                                ${gateway.escape(
                                    node.name ||
                                    "Unnamed Node"
                                )}
                            </strong>
                        </td>


                        <td>
                            ${gateway.escape(
                                node.node_id ||
                                "—"
                            )}
                        </td>


                        <td>
                            ${gateway.escape(
                                node.mcu_model ||
                                node.mcu_family ||
                                "—"
                            )}
                        </td>


                        <td>
                            ${gateway.escape(
                                node.communication_type ||
                                "—"
                            )}
                        </td>


                        <td>
                            ${gateway.escape(
                                node.firmware_version ||
                                "—"
                            )}
                        </td>


                        <td>

                            <span class="
                                status
                                ${status}
                            ">
                                ${status.toUpperCase()}
                            </span>

                        </td>


                        <td>
                            ${gateway.time(
                                node.last_seen
                            )}
                        </td>


                        <td>

                            <div class="node-actions">

                                <button
                                    type="button"
                                    class="node-action-btn view"
                                    data-id="${gateway.escape(
                                        node.node_id
                                    )}"
                                    title="View Node"
                                >
                                    <span class="action-icon">◉</span>
                                    <span>View</span>
                                </button>


                                <button
                                    type="button"
                                    class="node-action-btn edit"
                                    data-id="${gateway.escape(
                                        node.node_id
                                    )}"
                                    title="Edit Node"
                                >
                                    <span class="action-icon">✎</span>
                                    <span>Edit</span>
                                </button>


                                <div class="node-more-wrap">

                                    <button
                                        type="button"
                                        class="node-action-btn more"
                                        data-id="${gateway.escape(
                                            node.node_id
                                        )}"
                                        title="More Actions"
                                        aria-haspopup="true"
                                        aria-expanded="false"
                                    >
                                        <span>More</span>
                                    </button>


                                    <div class="node-more-menu">

                                        <button
                                            type="button"
                                            class="node-menu-item toggle"
                                            data-id="${gateway.escape(
                                                node.node_id
                                            )}"
                                        >
                                            ${
                                                enabled
                                                ? "Disable"
                                                : "Enable"
                                            }
                                        </button>


                                        <button
                                            type="button"
                                            class="node-menu-item delete"
                                            data-id="${gateway.escape(
                                                node.node_id
                                            )}"
                                        >
                                            Delete
                                        </button>

                                    </div>

                                </div>

                            </div>

                        </td>

                    </tr>
                `;

            }).join("");


        bindTableButtons();
    }


    /* ============================================================
       TABLE BUTTONS
       ============================================================ */

    function bindTableButtons() {

        document
            .querySelectorAll(".node-action-btn.view")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        const node =
                            findNode(
                                button.dataset.id
                            );


                        if (node) {

                            openView(node);

                        }

                    }
                );

            });


        document
            .querySelectorAll(".node-action-btn.edit")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        const node =
                            findNode(
                                button.dataset.id
                            );


                        if (node) {

                            openEditDrawer(node);

                        }

                    }
                );

            });


        document
            .querySelectorAll(".node-action-btn.more")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    event => {

                        event.stopPropagation();

                        const wrap =
                            button.closest(
                                ".node-more-wrap"
                            );

                        const wasOpen =
                            wrap?.classList.contains(
                                "open"
                            );

                        closeMoreMenus();

                        if (wrap && !wasOpen) {

                            wrap.classList.add(
                                "open"
                            );

                            button.setAttribute(
                                "aria-expanded",
                                "true"
                            );

                        }

                    }
                );

            });


        document
            .querySelectorAll(".node-menu-item.toggle")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    async event => {

                        event.stopPropagation();

                        const node =
                            findNode(
                                button.dataset.id
                            );


                        if (node) {

                            await setNodeEnabled(
                                node,
                                !isNodeEnabled(node)
                            );

                        }

                    }
                );

            });


        document
            .querySelectorAll(".node-menu-item.delete")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    event => {

                        event.stopPropagation();

                        const node =
                            findNode(
                                button.dataset.id
                            );


                        if (node) {

                            closeMoreMenus();

                            confirmDelete(node);

                        }

                    }
                );

            });

    }


    function closeMoreMenus() {

        document
            .querySelectorAll(
                ".node-more-wrap.open"
            )
            .forEach(wrap => {

                wrap.classList.remove(
                    "open"
                );

                wrap
                    .querySelector(
                        ".node-action-btn.more"
                    )
                    ?.setAttribute(
                        "aria-expanded",
                        "false"
                    );

            });

    }


    /* ============================================================
       FIND NODE
       ============================================================ */

    function findNode(id) {

        return nodes.find(
            node =>
                node.node_id === id
        );

    }


    function isNodeEnabled(node) {

        return !(
            node.enabled === false ||
            node.enabled === 0 ||
            node.enabled === "0" ||
            String(node.enabled).toLowerCase() === "false"
        );

    }


    function getNodeStatus(node) {

        if (!isNodeEnabled(node)) {

            return "disabled";

        }


        return gateway.status(
            node.status
        );

    }


    /* ============================================================
       ADD / EDIT DRAWER
       ============================================================ */

    function openEditDrawer(node = null) {

        const drawer =
            document.getElementById(
                "node-drawer"
            );

        const overlay =
            document.getElementById(
                "node-overlay"
            );

        const title =
            document.getElementById(
                "node-drawer-title"
            );

        const form =
            document.getElementById(
                "node-form"
            );


        if (!drawer || !overlay || !form) {

            console.error(
                "Node edit drawer not found"
            );

            return;
        }


        form.reset();


        editingNodeId =
            node
                ? node.node_id
                : null;


        title.textContent =
            node
                ? "Edit Node"
                : "Add Node";


        if (node) {

            setField(
                form,
                "node_id",
                node.node_id
            );


            setField(
                form,
                "name",
                node.name
            );


            setField(
                form,
                "node_address",
                node.node_address
            );


            setField(
                form,
                "mcu_family",
                node.mcu_family
            );


            setField(
                form,
                "mcu_model",
                node.mcu_model
            );


            setField(
                form,
                "hardware_revision",
                node.hardware_revision
            );


            setField(
                form,
                "firmware_version",
                node.firmware_version
            );


            setField(
                form,
                "communication_type",
                node.communication_type
            );


            if (form.elements.enabled) {

                form.elements.enabled.checked =
                    Boolean(
                        node.enabled
                    );

            }


            if (form.elements.node_id) {

                form.elements.node_id.readOnly =
                    true;

            }

        } else {

            if (form.elements.node_id) {

                form.elements.node_id.readOnly =
                    false;

            }


            if (form.elements.enabled) {

                form.elements.enabled.checked =
                    true;

            }


            setField(
                form,
                "firmware_version",
                "v1.0.0"
            );

        }


        drawer.classList.add("open");

        overlay.classList.add("open");

    }


    function setField(
        form,
        name,
        value
    ) {

        const field =
            form.elements[name];


        if (field) {

            field.value =
                value ?? "";

        }

    }


    function closeDrawer() {

        document
            .getElementById("node-drawer")
            ?.classList.remove(
                "open"
            );


        document
            .getElementById("node-overlay")
            ?.classList.remove(
                "open"
            );


        editingNodeId = null;

    }


    /* ============================================================
       SAVE NODE
       ============================================================ */

    async function saveNode(event) {

        event.preventDefault();


        const form =
            event.currentTarget;


        const data = {

            node_id:
                form.elements.node_id.value.trim(),

            name:
                form.elements.name.value.trim(),

            node_address:
                form.elements.node_address.value.trim(),

            mcu_family:
                form.elements.mcu_family.value.trim(),

            mcu_model:
                form.elements.mcu_model.value.trim(),

            hardware_revision:
                form.elements.hardware_revision.value.trim(),

            firmware_version:
                form.elements.firmware_version.value.trim()
                || "v1.0.0",

            communication_type:
                form.elements.communication_type.value,

            communication_config: {},

            enabled:
                form.elements.enabled.checked
                    ? 1
                    : 0

        };


        if (!data.node_id) {

            gateway.toast(
                "Node ID is required",
                "error"
            );

            return;
        }


        if (!data.name) {

            gateway.toast(
                "Node Name is required",
                "error"
            );

            return;
        }


        if (!data.communication_type) {

            gateway.toast(
                "Communication Type is required",
                "error"
            );

            return;
        }


        try {

            let successMessage;


            if (editingNodeId) {

                await gateway.send(
                    `/api/nodes/${encodeURIComponent(
                        editingNodeId
                    )}`,
                    "PUT",
                    data
                );


                successMessage =
                    "Node updated successfully";

            } else {

                await gateway.send(
                    "/api/nodes",
                    "POST",
                    data
                );


                successMessage =
                    "Node created successfully";

            }


            closeDrawer();

            await loadNodes();

            gateway.toast(
                successMessage
            );


        } catch (error) {

            console.error(
                "Save node error:",
                error
            );


            gateway.toast(
                error.message ||
                "Unable to save node",
                "error"
            );

        }

    }


    /* ============================================================
       VIEW DRAWER
       ============================================================ */

    function openView(node) {

        closeDrawer();


        let view =
            document.getElementById(
                "node-view-drawer"
            );


        let overlay =
            document.getElementById(
                "node-view-overlay"
            );


        if (!overlay) {

            overlay =
                document.createElement(
                    "div"
                );

            overlay.id =
                "node-view-overlay";

            overlay.className =
                "drawer-overlay";


            document.body.appendChild(
                overlay
            );

        }


        if (!view) {

            view =
                document.createElement(
                    "aside"
                );

            view.id =
                "node-view-drawer";

            view.className =
                "drawer node-view-drawer";


            document.body.appendChild(
                view
            );

        }


        view.innerHTML = `

            <div class="drawer-header">

                <div>

                    <h2>
                        Node Details
                    </h2>

                    <p>
                        Read-only node information
                    </p>

                </div>


                <button
                    type="button"
                    class="drawer-close"
                    id="node-view-close"
                >
                    ×
                </button>

            </div>


            <div class="drawer-body">

                <h4>IDENTITY</h4>

                <div class="detail-grid">

                    <div>
                        <small>Node Name</small>
                        <strong>
                            ${gateway.escape(
                                node.name || "—"
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>Node ID</small>
                        <strong>
                            ${gateway.escape(
                                node.node_id || "—"
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>Node Address</small>
                        <strong>
                            ${gateway.escape(
                                node.node_address || "—"
                            )}
                        </strong>
                    </div>

                </div>


                <h4>HARDWARE</h4>

                <div class="detail-grid">

                    <div>
                        <small>MCU Family</small>
                        <strong>
                            ${gateway.escape(
                                node.mcu_family || "—"
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>MCU Model</small>
                        <strong>
                            ${gateway.escape(
                                node.mcu_model || "—"
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>Hardware Revision</small>
                        <strong>
                            ${gateway.escape(
                                node.hardware_revision || "—"
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>Firmware Version</small>
                        <strong>
                            ${gateway.escape(
                                node.firmware_version || "—"
                            )}
                        </strong>
                    </div>

                </div>


                <h4>COMMUNICATION</h4>

                <div class="detail-grid">

                    <div>
                        <small>Communication</small>
                        <strong>
                            ${gateway.escape(
                                node.communication_type || "—"
                            )}
                        </strong>
                    </div>

                </div>


                <h4>STATUS</h4>

                <div class="detail-grid">

                    <div>
                        <small>Current Status</small>
                        <strong>
                            ${gateway.escape(
                                getNodeStatus(node).toUpperCase()
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>Enabled</small>
                        <strong>
                            ${
                                isNodeEnabled(node)
                                ? "Enabled"
                                : "Disabled"
                            }
                        </strong>
                    </div>


                    <div>
                        <small>Last Seen</small>
                        <strong>
                            ${gateway.time(
                                node.last_seen
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>Created</small>
                        <strong>
                            ${gateway.time(
                                node.created_at
                            )}
                        </strong>
                    </div>


                    <div>
                        <small>Updated</small>
                        <strong>
                            ${gateway.time(
                                node.updated_at
                            )}
                        </strong>
                    </div>

                </div>

            </div>


            <div class="drawer-footer">

                <button
                    type="button"
                    class="btn btn-secondary"
                    id="node-view-close-bottom"
                >
                    Close
                </button>


                <button
                    type="button"
                    class="btn btn-primary"
                    id="node-view-edit"
                >
                    Edit Node
                </button>

            </div>
        `;


        view.classList.add("open");

        overlay.classList.add("open");


        document
            .getElementById("node-view-close")
            ?.addEventListener(
                "click",
                closeView
            );


        document
            .getElementById("node-view-close-bottom")
            ?.addEventListener(
                "click",
                closeView
            );


        document
            .getElementById("node-view-edit")
            ?.addEventListener(
                "click",
                () => {

                    closeView();

                    setTimeout(
                        () => {
                            openEditDrawer(node);
                        },
                        100
                    );

                }
            );


        overlay.onclick =
            closeView;

    }


    function closeView() {

        document
            .getElementById(
                "node-view-drawer"
            )
            ?.classList.remove(
                "open"
            );


        document
            .getElementById(
                "node-view-overlay"
            )
            ?.classList.remove(
                "open"
            );

    }


    /* ============================================================
       ENABLE / DISABLE
       ============================================================ */

    async function setNodeEnabled(
        node,
        enabled
    ) {

        closeMoreMenus();


        try {

            await gateway.send(
                `/api/nodes/${encodeURIComponent(
                    node.node_id
                )}/enable`,
                "POST",
                {
                    enabled
                }
            );


            await loadNodes();

            gateway.toast(
                enabled
                    ? "Node enabled successfully"
                    : "Node disabled successfully"
            );


        } catch (error) {

            console.error(
                "Enable node error:",
                error
            );


            gateway.toast(
                error.message ||
                "Unable to update node status",
                "error"
            );

        }

    }


    /* ============================================================
       DELETE
       ============================================================ */

    function confirmDelete(node) {

        let root =
            document.getElementById(
                "modal-root"
            );


        if (!root) {

            root =
                document.createElement(
                    "div"
                );

            root.id =
                "modal-root";

            document.body.appendChild(
                root
            );

        }


        root.innerHTML = `

            <div
                class="modal-overlay"
                id="delete-modal"
            >

                <div class="modal">

                    <div class="modal-icon">
                        !
                    </div>


                    <h2>
                        Delete Node?
                    </h2>


                    <p>
                        Delete

                        <strong>
                            ${gateway.escape(
                                node.name ||
                                node.node_id
                            )}
                        </strong>

                        ?

                        <br>

                        Node ID:

                        <strong>
                            ${gateway.escape(
                                node.node_id
                            )}
                        </strong>
                    </p>


                    <p class="danger-text">
                        This action cannot be undone.
                    </p>


                    <div class="modal-actions">

                        <button
                            type="button"
                            class="btn btn-secondary"
                            id="delete-cancel"
                        >
                            Cancel
                        </button>


                        <button
                            type="button"
                            class="btn btn-danger"
                            id="delete-confirm"
                        >
                            Delete Node
                        </button>

                    </div>

                </div>

            </div>
        `;


        document
            .getElementById(
                "delete-cancel"
            )
            ?.addEventListener(
                "click",
                closeModal
            );


        document
            .getElementById(
                "delete-confirm"
            )
            ?.addEventListener(
                "click",
                async () => {

                    await deleteNode(
                        node.node_id
                    );

                }
            );

    }


    async function deleteNode(nodeId) {

        try {

            await gateway.send(
                `/api/nodes/${encodeURIComponent(
                    nodeId
                )}`,
                "DELETE"
            );


            closeModal();


            await loadNodes();

            gateway.toast(
                "Node deleted successfully"
            );


        } catch (error) {

            console.error(
                "Delete node error:",
                error
            );


            gateway.toast(
                error.message ||
                "Unable to delete node",
                "error"
            );

        }

    }


    function closeModal() {

        const root =
            document.getElementById(
                "modal-root"
            );


        if (root) {

            root.innerHTML = "";

        }

    }


});
