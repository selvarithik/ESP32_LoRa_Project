/* ============================================================
   SELVARITHIK'S LORA GATEWAY
   COMMON APPLICATION JAVASCRIPT
   ============================================================ */

"use strict";

window.gateway = window.gateway || {};

const gateway = window.gateway;


/* ============================================================
   CONFIGURATION
   ============================================================ */

gateway.apiBase = "";

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
        headers: {
            "Accept": "application/json"
        }
    };


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
            data.error ||
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
            data.error ||
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

gateway.initTheme = function () {
    const root = document.documentElement;

    root.setAttribute("data-theme", "light");
    root.removeAttribute("data-accent");
    root.removeAttribute("data-palette");

    localStorage.removeItem("gateway_theme");
    localStorage.removeItem("gateway_accent");
    localStorage.removeItem("gateway_palette");

    document.dispatchEvent(
        new CustomEvent("gateway:themechange", {
            detail: { theme: "light", palette: "gateway-triad" }
        })
    );
};

gateway.toggleTheme = function () {
    gateway.initTheme();
};

gateway.applyPalette = function () {
    const root = document.documentElement;

    root.setAttribute("data-theme", "light");
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
    const input = document.getElementById("global-nav-search");
    const modal = document.getElementById("global-search-modal");
    if (!input) return;

    const searchable = Array.from(document.querySelectorAll(".nav-item[data-path]"));

    input.addEventListener("keydown", (event) => {
        /* modern-shell.js owns keyboard selection while the search dialog is open. */
        if (modal && modal.classList.contains("open")) return;
        if (event.key !== "Enter") return;

        const q = input.value.trim().toLowerCase();
        if (!q) return;

        const match = searchable.find(link => link.textContent.toLowerCase().includes(q));
        if (match) {
            window.location.href = match.getAttribute("href");
            return;
        }

        gateway.toast?.(`No page found for "${input.value.trim()}"`, "info");
    });
};

gateway.initMobileNav = function () {
    const menuBtn = document.getElementById("mobile-menu-btn");
    const drawer = document.getElementById("mobileNavDrawer");
    const overlay = document.getElementById("mobileNavOverlay");

    if (!menuBtn || !drawer) return;

    const closeButton = drawer.querySelector(".mobile-drawer-close-v6");

    const closeDrawer = () => {
        drawer.classList.remove("open");
        drawer.setAttribute("aria-hidden", "true");
        menuBtn.setAttribute("aria-expanded", "false");
        overlay?.classList.remove("open");
        overlay?.setAttribute("aria-hidden", "true");
        document.body.classList.remove("nav-open");
    };

    const openDrawer = () => {
        drawer.classList.add("open");
        drawer.setAttribute("aria-hidden", "false");
        menuBtn.setAttribute("aria-expanded", "true");
        overlay?.classList.add("open");
        overlay?.setAttribute("aria-hidden", "false");
        document.body.classList.add("nav-open");
        closeButton?.focus();
    };

    menuBtn.setAttribute("aria-expanded", "false");
    menuBtn.addEventListener("click", () => {
        drawer.classList.contains("open") ? closeDrawer() : openDrawer();
    });

    closeButton?.addEventListener("click", closeDrawer);
    overlay?.addEventListener("click", closeDrawer);

    drawer.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", closeDrawer);
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && drawer.classList.contains("open")) {
            closeDrawer();
            menuBtn.focus();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 1180 && drawer.classList.contains("open")) {
            closeDrawer();
        }
    }, { passive: true });

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


/* ============================================================
   Sidebar collapse — persistent desktop preference
   ============================================================ */
(function initSidebarCollapse() {
    function setup() {
        const body = document.body;
        const button = document.getElementById("sidebar-collapse-btn");
        if (!body || !button || button.dataset.bound === "1") return;
        button.dataset.bound = "1";

        const key = "selvarithik-sidebar-collapsed";
        const apply = (collapsed) => {
            body.classList.toggle("sidebar-collapsed", collapsed);
            button.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
            button.setAttribute("title", collapsed ? "Expand sidebar" : "Collapse sidebar");
        };

        let collapsed = false;
        try {
            collapsed = localStorage.getItem(key) === "1";
        } catch (_) {}
        apply(collapsed);

        button.addEventListener("click", () => {
            collapsed = !body.classList.contains("sidebar-collapsed");
            apply(collapsed);
            try {
                localStorage.setItem(key, collapsed ? "1" : "0");
            } catch (_) {}
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setup, { once: true });
    } else {
        setup();
    }
})();
