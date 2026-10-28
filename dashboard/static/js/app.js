/* ============================================================
   Selvarithik LORA GATEWAY
   COMMON APPLICATION JAVASCRIPT
   ============================================================ */

"use strict";

window.gateway = window.gateway || {};

const gateway = window.gateway;


/* ============================================================
   CONFIGURATION
   ============================================================ */

gateway.apiBase = "";

/* Periodic reconciliation is required even when a socket remains connected.
   Pause hidden pages, coalesce events, and restart after browser back/forward cache. */
gateway.watch = function (refresh, options = {}) {
    let timer = null, running = false, stopped = false;
    const interval = options.interval || 5000;
    async function run() {
        if (stopped || document.hidden || running || (options.enabled && !options.enabled())) return;
        running = true;
        try { await refresh(); }
        catch (error) { console.error("Background refresh failed:", error); }
        finally { running = false; }
    }
    const start = () => { if (!timer && !stopped) timer = setInterval(run, interval); };
    const pause = () => { clearInterval(timer); timer = null; };
    const visible = () => { if (document.hidden) pause(); else { start(); run(); } };
    const hide = () => pause();
    const show = event => { if (event.persisted) { start(); run(); } };
    document.addEventListener("visibilitychange", visible);
    window.addEventListener("pagehide", hide);
    window.addEventListener("pageshow", show);
    const events = options.events || [];
    events.forEach(event => gateway.socket?.on(event, run));
    start();
    if (options.immediate !== false) run();
    return () => {
        stopped = true; pause();
        document.removeEventListener("visibilitychange", visible);
        window.removeEventListener("pagehide", hide);
        window.removeEventListener("pageshow", show);
        events.forEach(event => gateway.socket?.off(event, run));
    };
};



gateway.timeZone = "Asia/Kolkata";


/* ============================================================
   HTML ESCAPE
   ============================================================ */

gateway.escape = function (value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
};


/* ============================================================
   STATUS NORMALIZATION
   ============================================================ */

gateway.status = function (value) {

    const status = String(
        value || "offline"
    ).toLowerCase().trim();

    if (
        status === "online" ||
        status === "connected" ||
        status === "active"
    ) {
        return "online";
    }

    if (
        status === "disabled"
    ) {
        return "disabled";
    }

    if (
        status === "warning" ||
        status === "warn"
    ) {
        return "warning";
    }

    if (
        status === "alarm" ||
        status === "critical" ||
        status === "error"
    ) {
        return "alarm";
    }

    return "offline";
};


/* ============================================================
   DATE / TIME
   ============================================================ */

gateway.time = function (value) {

    if (!value) {
        return "—";
    }

    try {

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return "—";
        }

        return new Intl.DateTimeFormat(
            "en-IN",
            {
                timeZone: gateway.timeZone,
                year: "numeric",
                month: "short",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false
            }
        ).format(date);

    } catch (error) {

        console.error(
            "Time formatting error:",
            error
        );

        return "—";
    }
};


/* ============================================================
   CURRENT CLOCK
   ============================================================ */

gateway.updateClock = function () {

    const elements = document.querySelectorAll(
        "[data-live-clock], #live-clock, #header-clock"
    );

    const dateElement =
        document.getElementById("date");

    const timeElement =
        document.getElementById("time");

    const now = new Date();

    let dateText = "—";
    let timeText = "—";

    try {

        dateText = new Intl.DateTimeFormat(
            "en-IN",
            {
                timeZone: gateway.timeZone,
                year: "numeric",
                month: "short",
                day: "2-digit"
            }
        ).format(now);

        timeText = new Intl.DateTimeFormat(
            "en-IN",
            {
                timeZone: gateway.timeZone,
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false
            }
        ).format(now);

    } catch (error) {
        console.error(error);
    }


    elements.forEach(
        element => {
            element.textContent =
                `${dateText} ${timeText}`;
        }
    );


    if (dateElement) {
        dateElement.textContent = dateText;
    }


    if (timeElement) {
        timeElement.textContent = timeText;
    }
};


gateway.startClock = function () {

    gateway.updateClock();

    if (gateway.clockTimer) {
        clearInterval(
            gateway.clockTimer
        );
    }

    gateway.clockTimer = setInterval(
        gateway.updateClock,
        1000
    );
};


/* ============================================================
   HTTP SEND
   ============================================================ */

gateway.send = async function (
    url,
    method = "GET",
    body = null
) {

    const normalizedMethod =
        String(method || "GET").toUpperCase();

    const options = {
        method: normalizedMethod,
        cache: "no-store",
        signal: AbortSignal.timeout(12000),
        headers: {
            "Accept": "application/json"
        }
    };
    options.headers["X-CSRF-Token"] = document.querySelector('meta[name="sensor-csrf"]')?.content || "";


    if (
        body !== null &&
        body !== undefined
    ) {

        options.headers[
            "Content-Type"
        ] = "application/json";

        options.body = JSON.stringify(
            body
        );
    }


    let response;

    try {

        response = await fetch(
            gateway.apiBase + url,
            options
        );

    } catch (error) {

        throw new Error(
            error.message ||
            "Network request failed"
        );

    }


    const data =
        await parseResponseBody(response);


    if (!response.ok) {

        throw new Error(
            getErrorMessage(response, data)
        );
    }


    if (
        data &&
        data.success === false
    ) {

        throw new Error(
            (typeof data.error === "object" ? data.error.code || data.error.message : data.error) ||
            data.message ||
            "Server request failed"
        );
    }


    return data;
};


gateway.get = function (url) {

    return gateway.send(
        url,
        "GET"
    );

};


gateway.post = function (
    url,
    data
) {

    return gateway.send(
        url,
        "POST",
        data
    );

};


gateway.put = function (
    url,
    data
) {

    return gateway.send(
        url,
        "PUT",
        data
    );

};


gateway.delete = function (url) {

    return gateway.send(
        url,
        "DELETE"
    );

};


async function parseResponseBody(response) {

    if (response.status === 204) {
        return null;
    }


    const text =
        await response.text();

    if (!text.trim()) {
        return null;
    }


    try {

        return JSON.parse(text);

    } catch (error) {

        if (!response.ok) {
            return {
                error:
                    getStatusMessage(
                        response.status
                    )
            };
        }

        throw new Error(
            "Invalid server response"
        );

    }

}


function getErrorMessage(
    response,
    data
) {

    if (data) {

        return (
            (typeof data.error === "object" ? data.error.code || data.error.message : data.error) ||
            data.message ||
            getStatusMessage(response.status)
        );

    }


    return getStatusMessage(response.status);

}


function getStatusMessage(status) {

    switch (status) {

        case 400:
            return "Bad request";

        case 404:
            return "API endpoint not found";

        case 409:
            return "Request conflict";

        case 500:
            return "Server error";

        default:
            return `Request failed (${status})`;

    }

}


/* ============================================================
   TOAST
   ============================================================ */

gateway.toast = function (
    message,
    type = "success"
) {

    let container =
        document.getElementById(
            "toast-container"
        );


    if (!container) {

        container = document.createElement(
            "div"
        );

        container.id =
            "toast-container";

        container.className =
            "toast-container";

        document.body.appendChild(
            container
        );
    }


    const toast =
        document.createElement(
            "div"
        );

    toast.className =
        `toast toast-${type}`;


    const icon =
        type === "error"
            ? "!"
            : type === "warning"
                ? "!"
                : "✓";


    toast.innerHTML = `
        <span class="toast-icon">
            ${icon}
        </span>

        <span class="toast-message">
            ${gateway.escape(message)}
        </span>
    `;


    container.appendChild(
        toast
    );


    requestAnimationFrame(
        () => {
            toast.classList.add(
                "show"
            );
        }
    );


    setTimeout(
        () => {

            toast.classList.remove(
                "show"
            );

            setTimeout(
                () => toast.remove(),
                300
            );

        },
        3500
    );
};


/* ============================================================
   COMMON LOADING / ERROR STATES
   ============================================================ */

gateway.showLoading = function (
    element,
    message = "Loading..."
) {

    if (!element) {
        return;
    }


    if (isTableSection(element)) {

        element.innerHTML = `
            <tr>
                <td
                    colspan="${getTableColumnCount(element)}"
                    class="loading">
                    ${gateway.escape(message)}
                </td>
            </tr>
        `;

        return;
    }


    element.innerHTML = `
        <div class="loading">
            ${gateway.escape(message)}
        </div>
    `;

};


gateway.showError = function (
    element,
    message = "Unable to load data",
    retryCallback
) {

    if (!element) {
        return;
    }


    const retryId =
        `gateway-retry-${Date.now()}-${Math.random()
            .toString(16)
            .slice(2)}`;


    if (isTableSection(element)) {

        element.innerHTML = `
            <tr>
                <td
                    colspan="${getTableColumnCount(element)}"
                    class="loading">
                    <strong>
                        ${gateway.escape(message)}
                    </strong>

                    ${
                        typeof retryCallback === "function"
                            ? `
                                <br><br>
                                <button
                                    type="button"
                                    class="btn btn-secondary"
                                    id="${retryId}">
                                    Retry
                                </button>
                            `
                            : ""
                    }
                </td>
            </tr>
        `;

    } else {

        element.innerHTML = `
            <div class="loading">
                <strong>
                    ${gateway.escape(message)}
                </strong>

                ${
                    typeof retryCallback === "function"
                        ? `
                            <br><br>
                            <button
                                type="button"
                                class="btn btn-secondary"
                                id="${retryId}">
                                Retry
                            </button>
                        `
                        : ""
                }
            </div>
        `;

    }


    if (typeof retryCallback === "function") {

        document
            .getElementById(retryId)
            ?.addEventListener(
                "click",
                retryCallback
            );

    }

};


function isTableSection(element) {

    return [
        "TBODY",
        "THEAD",
        "TFOOT"
    ].includes(
        element.tagName
    );

}


function getTableColumnCount(element) {

    const table =
        element.closest("table");

    const count =
        table
            ?.querySelectorAll("thead th")
            ?.length;

    return count || 1;

}


/* ============================================================
   COMMON REFRESH BUTTON
   ============================================================ */

gateway.bindRefresh = function (
    selector,
    callback
) {

    const button =
        document.querySelector(
            selector
        );

    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        async () => {

            if (
                typeof callback !==
                "function"
            ) {
                return;
            }

            try {

                button.disabled = true;

                await callback();

            } finally {

                button.disabled = false;
            }
        }
    );
};


/* ============================================================
   THEME MANAGEMENT
   Fixed gateway UI: BLUE / ORANGE / GREEN + WHITE.
   User-selectable palette and dark mode are removed.
   ============================================================ */

const GATEWAY_UI_PALETTE = {
    blue: "#0057FF",
    orange: "#FC6C26",
    green: "#009E4D",
    white: "#FFFFFF"
};

gateway.initAppearanceEditor = function () {
    /* Compatibility hook retained for older callers. */
};

gateway.setTheme = function (theme, persist = false) {
    const active = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", active);
    if (persist) { try { localStorage.setItem("gateway_theme", active); } catch (_) {} }
    document.dispatchEvent(new CustomEvent("gateway:themechange", { detail: { theme: active } }));
};

gateway.initTheme = function () {
    let stored;
    try { stored = localStorage.getItem("gateway_theme"); } catch (_) {}
    gateway.setTheme(stored === "dark" || stored === "light" ? stored :
        (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
};

gateway.toggleTheme = function () {
    gateway.setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);
};

gateway.applyPalette = function () {
    const root = document.documentElement;

    root.removeAttribute("data-accent");
    root.removeAttribute("data-palette");

    window.dispatchEvent(
        new CustomEvent("gateway:palettechange", {
            detail: {
                palette: "gateway-triad",
                colors: GATEWAY_UI_PALETTE
            }
        })
    );
};

gateway.initPalette = function () {
    gateway.applyPalette();
};

/* ============================================================
   CONNECTION HEALTH
   ============================================================ */

gateway.initConnectionHealth = function () {
    // Transport state is managed by the shared socket, not arbitrary HTTP responses.
    if (gateway.socket) return;

    const pill =
        document.getElementById(
            "global-connection-pill"
        );

    const text =
        document.getElementById(
            "global-connection-text"
        );

    if (!pill || !text) {
        return;
    }

    const setState = function (state) {

        pill.classList.remove(
            "is-live",
            "is-error",
            "is-connecting"
        );

        if (state === "live") {

            pill.classList.add(
                "is-live"
            );

            text.textContent =
                "LIVE";

        } else if (state === "error") {

            pill.classList.add(
                "is-error"
            );

            text.textContent =
                "CONNECTION ERROR";

        } else {

            pill.classList.add(
                "is-connecting"
            );

            text.textContent =
                "CONNECTING";
        }
    };

    setState("connecting");

    if (!window.__selvarithikFetchPatched) {

        window.__selvarithikFetchPatched = true;

        const originalFetch =
            window.fetch.bind(window);

        window.fetch = async function (
            input,
            init
        ) {

            try {

                const response =
                    await originalFetch(
                        input,
                        init
                    );

                window.dispatchEvent(
                    new CustomEvent(
                        "gateway:request",
                        {
                            detail: {
                                ok: response.ok,
                                status: response.status,
                                url: String(
                                    response.url || input || ""
                                )
                            }
                        }
                    )
                );

                return response;

            } catch (error) {

                window.dispatchEvent(
                    new CustomEvent(
                        "gateway:request",
                        {
                            detail: {
                                ok: false,
                                status: 0,
                                url: String(input || "")
                            }
                        }
                    )
                );

                throw error;
            }
        };
    }

    window.addEventListener(
        "gateway:request",
        event => {

            const ok =
                Boolean(
                    event.detail?.ok
                );

            setState(
                ok
                    ? "live"
                    : "error"
            );
        }
    );
};

/* ============================================================
   INITIAL THEME / CONNECTION
   ============================================================ */
/* ============================================================
   NAVIGATION, SEARCH & MOBILE MENU
   ============================================================ */

gateway.highlightActiveNav = function () {
    const currentPath = window.location.pathname.replace(/\/+$/, "") || "/";

    document.querySelectorAll(".nav-item, .mobile-nav-link").forEach(link => {
        const linkPath = (link.getAttribute("data-path") || "").replace(/\/+$/, "") || "/";
        link.classList.toggle("active", linkPath === currentPath);
    });
};

gateway.initGlobalSearch = function () {
    const modal = document.getElementById("global-search-modal");
    const input = document.getElementById("global-nav-search");
    const results = document.getElementById("global-search-results");
    const openButton = document.getElementById("global-nav-search-button");
    if (!input) return;

    const searchable = Array.from(document.querySelectorAll(".nav-item[data-path]"));

    const pageItems = () => searchable.map(link => ({
        title: (link.querySelector("span") || link).textContent.trim(),
        href: link.getAttribute("href"),
        path: link.getAttribute("data-path") || "",
        label: link.getAttribute("data-search-label") || link.textContent
    }));

    const render = (query) => {
        if (!results) return;
        const q = String(query || "").trim().toLowerCase();
        const items = pageItems().filter(item => {
            return !q || [item.title, item.path, item.label].join(" ").toLowerCase().includes(q);
        });

        if (!items.length) {
            results.innerHTML = '<div class="search-result"><span>No page found</span><small>Use an existing dashboard route</small></div>';
            return;
        }

        results.innerHTML = items.map((item, index) => `
            <button class="search-result ${index === 0 ? "active" : ""}" type="button" data-search-href="${gateway.escape(item.href)}">
                <span>${gateway.escape(item.title)}</span>
                <small>${gateway.escape(item.path)}</small>
            </button>
        `).join("");
    };

    const openSearch = () => {
        if (!modal) return;
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        render(input.value);
        setTimeout(() => {
            input.focus();
            input.select();
        }, 30);
    };

    const closeSearch = () => {
        if (!modal) return;
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
    };

    openButton?.addEventListener("click", openSearch);
    document.querySelectorAll("[data-close-search]").forEach(element => {
        element.addEventListener("click", closeSearch);
    });

    input.addEventListener("input", () => render(input.value));

    input.addEventListener("keydown", (event) => {
        const all = Array.from(results?.querySelectorAll(".search-result[data-search-href]") || []);
        const active = results?.querySelector(".search-result.active");
        const index = all.indexOf(active);

        if (event.key === "Escape") {
            closeSearch();
            return;
        }

        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            if (!all.length) return;
            all.forEach(item => item.classList.remove("active"));
            const step = event.key === "ArrowDown" ? 1 : -1;
            all[(index + step + all.length) % all.length].classList.add("active");
            return;
        }

        if (event.key !== "Enter") return;
        event.preventDefault();

        if (active && active.dataset.searchHref) {
            window.location.href = active.dataset.searchHref;
            return;
        }

        const q = input.value.trim().toLowerCase();
        if (!q) return;

        const match = searchable.find(link => link.textContent.toLowerCase().includes(q));
        if (match) {
            window.location.href = match.getAttribute("href");
            return;
        }

        gateway.toast?.(`No page found for "${input.value.trim()}"`, "info");
    });

    results?.addEventListener("click", event => {
        const target = event.target.closest("[data-search-href]");
        if (target) window.location.href = target.dataset.searchHref;
    });

    document.addEventListener("keydown", event => {
        const mac = navigator.platform && navigator.platform.toLowerCase().includes("mac");
        if ((mac ? event.metaKey : event.ctrlKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            openSearch();
        }
        if (event.key === "Escape" && modal?.classList.contains("open")) {
            closeSearch();
        }
    });
};

gateway.initMobileNav = function () {
    const menuBtn = document.getElementById("mobile-menu-btn");
    const drawer = document.getElementById("mobileNavDrawer");

    if (menuBtn && drawer) {
        const closeButton =
            drawer.querySelector(".mobile-drawer-close-v6");

        const closeDrawer = () => {
            drawer.classList.remove("open");
            drawer.setAttribute("aria-hidden", "true");
            menuBtn.setAttribute("aria-expanded", "false");
        };

        menuBtn.addEventListener("click", () => {
            const open =
                !drawer.classList.contains("open");

            drawer.classList.toggle(
                "open",
                open
            );

            drawer.setAttribute(
                "aria-hidden",
                open ? "false" : "true"
            );

            menuBtn.setAttribute(
                "aria-expanded",
                open ? "true" : "false"
            );
        });

        closeButton?.addEventListener(
            "click",
            closeDrawer
        );

        drawer.querySelectorAll("a").forEach(link => {
            link.addEventListener(
                "click",
                closeDrawer
            );
        });
    }
};

/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    gateway.initTheme();
    gateway.initPalette();
    gateway.highlightActiveNav();
    gateway.initGlobalSearch();
    gateway.initMobileNav();
    gateway.initConnectionHealth();
    gateway.startClock();
});
