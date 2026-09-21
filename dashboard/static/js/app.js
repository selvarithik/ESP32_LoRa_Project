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
   THEME & ACCENT MANAGEMENT
   Fixed light/dark themes + 12 curated accent presets.
   No RGB/HEX/custom appearance editor.
   ============================================================ */

const THEME_PRESETS = {
    light: "light",
    dark: "dark"
};

const ACCENTS = [
    "orange", "emerald", "cyan", "blue",
    "indigo", "violet", "magenta", "rose",
    "red", "amber", "teal", "slate"
];

gateway.initAppearanceEditor = function () {
    /* Legacy hook retained so older pages cannot open a removed color editor. */
};

gateway.initTheme = function () {

    const root = document.documentElement;

    const savedTheme =
        localStorage.getItem("gateway_theme") || "light";

    const savedAccent =
        localStorage.getItem("gateway_accent") || "orange";

    const normalizedTheme =
        savedTheme === "dark" ? "dark" : "light";

    root.setAttribute(
        "data-theme",
        normalizedTheme
    );

    root.setAttribute(
        "data-accent",
        ACCENTS.includes(savedAccent)
            ? savedAccent
            : "orange"
    );

    /* Remove known inline color overrides left by older UI versions. */
    [
        "--brand-primary",
        "--brand-primary-hover",
        "--brand-primary-light",
        "--brand-primary-border",
        "--brand-primary-glow",
        "--nav-active-bg",
        "--bg-app",
        "--bg-surface",
        "--bg-surface-elevated",
        "--bg-surface-subtle",
        "--bg-input",
        "--text-main",
        "--text-muted",
        "--text-subtle",
        "--border-color",
        "--border-subtle",
        "--header-bg",
        "--header-text",
        "--header-muted",
        "--nav-bg",
        "--nav-text",
        "--nav-muted"
    ].forEach(name => root.style.removeProperty(name));

    document
        .querySelectorAll(".accent-swatch")
        .forEach(swatch => {
            swatch.classList.toggle(
                "active",
                swatch.getAttribute("data-accent-choice")
                === root.getAttribute("data-accent")
            );
        });

    const themeToggleBtn =
        document.getElementById("theme-toggle-btn");

    themeToggleBtn?.addEventListener(
        "click",
        () => gateway.toggleTheme()
    );

    const accentBtn =
        document.getElementById("accent-picker-btn");

    const accentMenu =
        document.getElementById("accent-dropdown-menu");

    if (
        accentBtn &&
        accentMenu
    ) {

        accentBtn.addEventListener(
            "click",
            event => {
                event.stopPropagation();

                accentMenu.classList.toggle(
                    "show"
                );
            }
        );

        document.addEventListener(
            "click",
            event => {

                if (
                    !accentMenu.contains(
                        event.target
                    ) &&
                    event.target !== accentBtn
                ) {

                    accentMenu.classList.remove(
                        "show"
                    );
                }
            }
        );

        document
            .querySelectorAll(".accent-swatch")
            .forEach(swatch => {

                swatch.addEventListener(
                    "click",
                    () => {

                        const choice =
                            swatch.getAttribute(
                                "data-accent-choice"
                            );

                        if (
                            choice &&
                            ACCENTS.includes(choice)
                        ) {

                            gateway.setAccent(
                                choice
                            );

                            accentMenu.classList.remove(
                                "show"
                            );
                        }
                    }
                );
            });
    }
};

gateway.toggleTheme = function () {

    const currentTheme =
        document.documentElement.getAttribute(
            "data-theme"
        ) || "light";

    const nextTheme =
        currentTheme === "dark"
            ? "light"
            : "dark";

    document.documentElement.setAttribute(
        "data-theme",
        nextTheme
    );

    localStorage.setItem(
        "gateway_theme",
        nextTheme
    );

    window.dispatchEvent(
        new CustomEvent(
            "gateway:themechange"
        )
    );
};

gateway.setAccent = function (accent) {

    if (!ACCENTS.includes(accent)) {
        return;
    }

    document.documentElement.setAttribute(
        "data-accent",
        accent
    );

    localStorage.setItem(
        "gateway_accent",
        accent
    );

    document
        .querySelectorAll(".accent-swatch")
        .forEach(swatch => {

            swatch.classList.toggle(
                "active",
                swatch.getAttribute(
                    "data-accent-choice"
                ) === accent
            );
        });

    window.dispatchEvent(
        new CustomEvent(
            "gateway:themechange"
        )
    );
};

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
    if (!input) return;

    const searchable = Array.from(document.querySelectorAll(".nav-item[data-path]"));

    input.addEventListener("keydown", (event) => {
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

    if (menuBtn && drawer) {
        menuBtn.addEventListener("click", () => {
            drawer.classList.toggle("open");
            menuBtn.setAttribute("aria-expanded", drawer.classList.contains("open") ? "true" : "false");
        });

        drawer.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                drawer.classList.remove("open");
                menuBtn.setAttribute("aria-expanded", "false");
            });
        });
    }
};

/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    gateway.initTheme();
    gateway.highlightActiveNav();
    gateway.initGlobalSearch();
    gateway.initMobileNav();
    gateway.startClock();
});
