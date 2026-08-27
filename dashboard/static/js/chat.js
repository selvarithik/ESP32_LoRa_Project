"use strict";

/* ============================================================
   PRIVATE CHAT
   Gateway <-> registered node
   No M2M / no communication_manager
   ============================================================ */

(() => {

    const GATEWAY_ID = "GATEWAY";

    const state = {
        users: [],
        currentUserId: GATEWAY_ID,
        activeUserId: "",
        messages: [],
        search: ""
    };


    /* ========================================================
       DOM
       ======================================================== */

    function $(id) {
        return document.getElementById(id);
    }


    /* ========================================================
       HELPERS
       ======================================================== */

    function escapeHtml(value) {

        if (
            value === null ||
            value === undefined
        ) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    function getId(user) {

        if (!user) {
            return "";
        }

        return String(
            user.user_id ||
            user.node_id ||
            user.id ||
            ""
        );
    }


    function getName(user) {

        if (!user) {
            return "Unknown";
        }

        return (
            user.name ||
            user.username ||
            user.node_id ||
            user.user_id ||
            "Unknown"
        );
    }


    function updateGatewayIdentity() {

        const select =
            $("chatIdentity");

        if (!select) {
            return;
        }

        select.innerHTML = "";

        const option =
            document.createElement("option");

        option.value = GATEWAY_ID;
        option.textContent = "Gateway Control Center";

        select.appendChild(option);

        select.value = GATEWAY_ID;
        select.disabled = true;

        state.currentUserId = GATEWAY_ID;
    }


    function initials(name) {

        const text =
            String(name || "?")
                .trim();

        if (!text) {
            return "?";
        }

        const parts =
            text
                .split(/\s+/)
                .filter(Boolean);

        if (parts.length === 1) {

            return parts[0]
                .substring(0, 2)
                .toUpperCase();
        }

        return (
            parts[0][0] +
            parts[parts.length - 1][0]
        ).toUpperCase();
    }


    function isOnline(user) {

        return String(
            user?.status || ""
        ).toLowerCase() === "online";
    }


    function formatTime(value) {

        if (!value) {
            return "";
        }

        const date =
            new Date(value);

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return "";
        }

        return new Intl.DateTimeFormat(
            "en-IN",
            {
                timeZone: "Asia/Kolkata",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            }
        ).format(date);
    }


    /* ========================================================
       API
       ======================================================== */

    async function apiGet(url) {

        const response =
            await fetch(
                url,
                {
                    method: "GET",
                    headers: {
                        "Accept":
                            "application/json"
                    },
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data?.error ||
                "Request failed"
            );
        }

        return data;
    }


    async function apiPost(
        url,
        body
    ) {

        const response =
            await fetch(
                url,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",
                        "Accept":
                            "application/json"
                    },
                    body:
                        JSON.stringify(body)
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data?.error ||
                "Request failed"
            );
        }

        return data;
    }


    /* ========================================================
       LOAD USERS
       ======================================================== */

    async function loadUsers() {

        const list =
            $("chatList");

        if (list) {

            list.innerHTML =
                `
                <div class="chat-list-loading">
                    <span class="chat-spinner"></span>
                    Loading chats...
                </div>
                `;
        }

        try {

            const data =
                await apiGet(
                    "/api/chat/users"
                );

            state.users =
                Array.isArray(
                    data.users
                )
                    ? data.users
                    : [];

            renderUserList();

        }
        catch (error) {

            console.error(
                "[CHAT] Users:",
                error
            );

            if (list) {

                list.innerHTML =
                    `
                    <div class="chat-list-empty">
                        ${escapeHtml(
                            error.message ||
                            "Unable to load chats."
                        )}
                    </div>
                    `;
            }
        }
    }


    /* ========================================================
       USER LIST
       ======================================================== */

    function renderUserList() {

        const list =
            $("chatList");

        if (!list) {
            return;
        }

        const search =
            state.search
                .trim()
                .toLowerCase();

        const users =
            state.users.filter(
                user => {

                    if (!search) {
                        return true;
                    }

                    return (
                        getName(user)
                            .toLowerCase()
                            .includes(search) ||
                        getId(user)
                            .toLowerCase()
                            .includes(search)
                    );
                }
            );


        if (!users.length) {

            list.innerHTML =
                `
                <div class="chat-list-empty">
                    ${
                        search
                            ? "No users found."
                            : "No registered nodes available."
                    }
                </div>
                `;

            return;
        }


        list.innerHTML =
            users.map(
                user => {

                    const id =
                        getId(user);

                    const name =
                        getName(user);

                    const active =
                        id ===
                        state.activeUserId;

                    const online =
                        isOnline(user);

                    return `
                        <div
                            class="chat-row ${
                                active
                                    ? "active"
                                    : ""
                            }"
                            data-user-id="${escapeHtml(id)}"
                            role="button"
                            tabindex="0"
                        >

                            <div class="chat-avatar">
                                ${escapeHtml(
                                    initials(name)
                                )}
                            </div>

                            <div class="chat-row-main">

                                <span class="chat-row-name">
                                    ${escapeHtml(name)}
                                </span>

                                <span class="chat-row-preview">
                                    ${
                                        active
                                            ? "Conversation open"
                                            : "Private conversation"
                                    }
                                </span>

                            </div>

                            <div class="chat-row-meta">

                                <span
                                    class="chat-row-status ${
                                        online
                                            ? "online"
                                            : ""
                                    }"
                                >
                                    <span
                                        class="chat-row-status-dot"
                                    ></span>

                                    ${
                                        online
                                            ? "Online"
                                            : "Offline"
                                    }

                                </span>

                            </div>

                        </div>
                    `;
                }
            ).join("");


        list
            .querySelectorAll(".chat-row")
            .forEach(row => {

                row.addEventListener(
                    "click",
                    () => {

                        openChat(
                            row.dataset.userId
                        );
                    }
                );


                row.addEventListener(
                    "keydown",
                    event => {

                        if (
                            event.key ===
                            "Enter"
                        ) {

                            openChat(
                                row.dataset.userId
                            );
                        }
                    }
                );

            });
    }


    /* ========================================================
       OPEN CHAT
       ======================================================== */

    async function openChat(
        userId
    ) {

        if (!userId) {
            return;
        }

        state.activeUserId =
            String(userId);

        const user =
            state.users.find(
                item =>
                    getId(item) ===
                    state.activeUserId
            );

        if (!user) {
            return;
        }

        const empty =
            $("chatEmpty");

        const active =
            $("chatActive");

        if (empty) {
            empty.hidden = true;
        }

        if (active) {
            active.hidden = false;
        }

        renderUserList();

        updateChatHeader();

        disableComposer(true);

        await loadMessages();

        disableComposer(false);

        const input =
            $("chatMessageInput");

        if (input) {
            input.focus();
        }
    }


    /* ========================================================
       HEADER
       ======================================================== */

    function updateChatHeader() {

        const user =
            state.users.find(
                item =>
                    getId(item) ===
                    state.activeUserId
            );

        const avatar =
            $("chatHeaderAvatar");

        const name =
            $("chatHeaderName");

        const status =
            $("chatHeaderStatus");


        if (!user) {

            if (avatar) {
                avatar.textContent = "?";
            }

            if (name) {
                name.textContent =
                    "Select a chat";
            }

            if (status) {
                status.textContent =
                    "Offline";
            }

            return;
        }


        const userName =
            getName(user);


        if (avatar) {
            avatar.textContent =
                initials(userName);
        }

        if (name) {
            name.textContent =
                userName;
        }

        if (status) {

            if (isOnline(user)) {

                status.textContent =
                    "Online";

            }
            else if (
                user.last_seen
            ) {

                status.textContent =
                    "Last seen " +
                    formatTime(
                        user.last_seen
                    );

            }
            else {

                status.textContent =
                    "Offline";
            }
        }
    }


    /* ========================================================
       LOAD MESSAGES
       ======================================================== */

    async function loadMessages() {

        if (!state.activeUserId) {
            return;
        }

        const container =
            $("chatMessages");

        if (container) {

            container.innerHTML =
                `
                <div class="chat-no-messages">
                    Loading messages...
                </div>
                `;
        }


        try {

            const params =
                new URLSearchParams({
                    user_id:
                        GATEWAY_ID,

                    with_user_id:
                        state.activeUserId,

                    limit:
                        "200"
                });


            const data =
                await apiGet(
                    "/api/chat/messages?" +
                    params.toString()
                );


            state.messages =
                Array.isArray(
                    data.messages
                )
                    ? data.messages
                    : [];


            renderMessages();

            await markIncomingSeen();

        }
        catch (error) {

            console.error(
                "[CHAT] Messages:",
                error
            );

            if (container) {

                container.innerHTML =
                    `
                    <div class="chat-no-messages">
                        ${escapeHtml(
                            error.message ||
                            "Unable to load messages."
                        )}
                    </div>
                    `;
            }
        }
    }


    /* ========================================================
       RENDER MESSAGES
       ======================================================== */

    function renderMessages() {

        const container =
            $("chatMessages");

        if (!container) {
            return;
        }


        if (!state.messages.length) {

            container.innerHTML =
                `
                <div class="chat-no-messages">
                    <div class="chat-welcome-icon">
                        CHAT
                    </div>

                    <h3>No messages yet</h3>

                    <p>
                        Send the first message.
                    </p>
                </div>
                `;

            return;
        }


        container.innerHTML =
            state.messages
                .map(message => {

                    const sender =
                        String(
                            message.sender_node_id ||
                            ""
                        );

                    const sent =
                        sender ===
                        GATEWAY_ID;

                    const text =
                        message.message_text ||
                        message.content ||
                        message.message ||
                        "";

                    const status =
                        String(
                            message.status ||
                            "SENT"
                        ).toUpperCase();

                    const statusClass =
                        status.toLowerCase();

                    const statusText =
                        status === "SEEN"
                            ? "✓✓"
                            : (
                                status === "DELIVERED"
                                    ? "✓✓"
                                    : "✓"
                            );

                    return `
                        <div
                            class="message-line ${
                                sent
                                    ? "outgoing"
                                    : "incoming"
                            }"
                        >

                            <div class="message-bubble">
                                <div class="message-text">
                                    ${escapeHtml(text)}
                                </div>

                                <div class="message-meta">

                                    <span>
                                        ${escapeHtml(
                                            formatTime(
                                                message.created_at
                                            )
                                        )}
                                    </span>

                                    ${
                                        sent
                                            ? `
                                                <span
                                                    class="message-status ${escapeHtml(statusClass)}"
                                                    title="${escapeHtml(status)}"
                                                >
                                                    ${statusText}
                                                </span>
                                              `
                                            : ""
                                    }

                                </div>

                            </div>
                        </div>
                    `;
                })
                .join("");


        container.scrollTop =
            container.scrollHeight;
    }


    /* ========================================================
       SEEN
       ======================================================== */

    async function markIncomingSeen() {

        const incoming =
            state.messages.filter(
                message =>
                    String(
                        message.receiver_node_id
                    ) === GATEWAY_ID &&
                    message.status !== "SEEN"
            );

        for (
            const message
            of incoming
        ) {

            try {

                await apiPost(
                    `/api/chat/messages/${
                        encodeURIComponent(
                            message.message_id
                        )
                    }/seen`,
                    {
                        receiver_id:
                            GATEWAY_ID
                    }
                );

            }
            catch (error) {

                console.warn(
                    "[CHAT] Seen update:",
                    error
                );
            }
        }
    }


    /* ========================================================
       SEND
       ======================================================== */

    async function sendMessage() {

        if (!state.activeUserId) {

            alert(
                "Select a chat first."
            );

            return;
        }


        const input =
            $("chatMessageInput");

        const button =
            $("chatSendButton");

        if (!input) {
            return;
        }


        const text =
            input.value.trim();

        if (!text) {
            return;
        }


        input.disabled = true;

        if (button) {
            button.disabled = true;
        }


        try {

            const data =
                await apiPost(
                    "/api/chat/messages",
                    {
                        sender_id:
                            GATEWAY_ID,

                        recipient_id:
                            state.activeUserId,

                        content:
                            text
                    }
                );


            if (
                !data.success
            ) {

                throw new Error(
                    data.error ||
                    "Message failed"
                );
            }


            input.value = "";

            await loadMessages();

        }
        catch (error) {

            console.error(
                "[CHAT] Send:",
                error
            );

            alert(
                error.message ||
                "Unable to send message."
            );

        }
        finally {

            input.disabled = false;

            if (button) {
                button.disabled = false;
            }

            input.focus();
        }
    }


    /* ========================================================
       COMPOSER
       ======================================================== */

    function disableComposer(
        disabled
    ) {

        const input =
            $("chatMessageInput");

        const button =
            $("chatSendButton");

        if (input) {
            input.disabled =
                disabled;
        }

        if (button) {
            button.disabled =
                disabled;
        }
    }


    /* ========================================================
       EVENTS
       ======================================================== */

    function setupEvents() {

        const search =
            $("chatSearch");

        if (search) {

            search.addEventListener(
                "input",
                () => {

                    state.search =
                        search.value;

                    renderUserList();
                }
            );
        }


        const form =
            $("chatComposer");

        if (form) {

            form.addEventListener(
                "submit",
                event => {

                    event.preventDefault();

                    sendMessage();
                }
            );
        }


        const input =
            $("chatMessageInput");

        if (input) {

            input.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key ===
                        "Enter" &&
                        !event.shiftKey
                    ) {

                        event.preventDefault();

                        sendMessage();
                    }
                }
            );


            input.addEventListener(
                "input",
                () => {

                    input.style.height =
                        "auto";

                    input.style.height =
                        Math.min(
                            input.scrollHeight,
                            140
                        ) + "px";
                }
            );
        }


        const refresh =
            $("chatRefreshButton");

        if (refresh) {

            refresh.addEventListener(
                "click",
                async () => {

                    await loadUsers();

                    if (
                        state.activeUserId
                    ) {

                        await loadMessages();
                    }
                }
            );
        }


        const reload =
            $("chatReloadMessages");

        if (reload) {

            reload.addEventListener(
                "click",
                async () => {

                    await loadMessages();
                }
            );
        }


        const identity =
            $("chatIdentity");

        if (identity) {

            identity.addEventListener(
                "change",
                () => {

                    updateGatewayIdentity();
                }
            );
        }
    }


    /* ========================================================
       INITIALIZE
       ======================================================== */

    async function initialize() {

        console.log(
            "[CHAT] Initializing"
        );

        updateGatewayIdentity();

        setupEvents();

        updateGatewayIdentity();

        disableComposer(true);

        await loadUsers();

        console.log(
            "[CHAT] Ready. Users:",
            state.users
        );
    }


    document.addEventListener(
        "DOMContentLoaded",
        initialize
    );

})();
