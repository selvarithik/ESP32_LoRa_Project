/* One reconnecting Socket.IO connection shared by page controllers. */
"use strict";
gateway.socket = typeof io === "function" ? io({
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 15000,
    randomizationFactor: 0.5
}) : null;
document.addEventListener("DOMContentLoaded", () => {
    const pill = document.getElementById("global-connection-pill");
    const label = document.getElementById("global-connection-text");
    const update = () => {
        const connected = Boolean(gateway.socket?.connected);
        pill?.classList.toggle("is-live", connected);
        pill?.classList.toggle("is-connecting", !connected);
        pill?.classList.remove("is-error");
        if (label) label.textContent = connected ? "LIVE" : "OFFLINE";
    };
    gateway.socket?.on("connect", update);
    gateway.socket?.on("disconnect", update);
    gateway.socket?.on("connect_error", update);
    update();
});
window.addEventListener("pagehide", () => gateway.socket?.disconnect());

// pagehide disconnects explicitly; reconnect when the browser restores this page.
window.addEventListener("pageshow", event => { if (event.persisted) gateway.socket?.connect(); });
