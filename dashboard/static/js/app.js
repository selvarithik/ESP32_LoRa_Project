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
   THEME, ACCENT & APPEARANCE MANAGEMENT
   ============================================================ */

const THEME_PRESETS = {
    light: "light",
    dark: "dark",
    midnight: "midnight",
    clean: "clean",
    contrast: "contrast"
};

const ACCENTS = ["orange", "emerald", "cyan", "indigo", "amber"];

const CUSTOM_COLOR_VARS = {
    "color-primary": "--brand-primary",
    "color-page-bg": "--bg-app",
    "color-surface": "--bg-surface",
    "color-header-bg": "--header-bg",
    "color-header-text": "--header-text",
    "color-header-muted": "--header-muted",
    "color-nav-bg": "--nav-bg",
    "color-nav-text": "--nav-text",
    "color-text-main": "--text-main",
    "color-text-muted": "--text-muted",
    "color-border": "--border-color",
    "color-icon": "--global-icon"
};

function isHexColor(value) {
    return /^#[0-9A-Fa-f]{6}$/.test(String(value || "").trim());
}

function hexToRgb(hex) {
    if (!isHexColor(hex)) return null;
    const n = parseInt(hex.slice(1), 16);
    return {
        r: (n >> 16) & 255,
        g: (n >> 8) & 255,
        b: n & 255
    };
}

function mixHex(hexA, hexB, amount) {
    const a = hexToRgb(hexA);
    const b = hexToRgb(hexB);
    if (!a || !b) return hexA;
    const t = Math.max(0, Math.min(1, amount));
    const c = {
        r: Math.round(a.r + (b.r - a.r) * t),
        g: Math.round(a.g + (b.g - a.g) * t),
        b: Math.round(a.b + (b.b - a.b) * t)
    };
    return "#" + [c.r, c.g, c.b].map(v => v.toString(16).padStart(2, "0")).join("");
}

function hexToRgbaString(hex, alpha) {
    const rgb = hexToRgb(hex);
    if (!rgb) return `rgba(0,0,0,${alpha})`;
    return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

gateway.applyPrimaryColor = function (hex) {
    if (!isHexColor(hex)) return;
    const root = document.documentElement;
    root.style.setProperty("--brand-primary", hex);
    root.style.setProperty("--brand-primary-hover", mixHex(hex, "#000000", 0.14));
    root.style.setProperty("--brand-primary-light", mixHex(hex, "#FFFFFF", 0.90));
    root.style.setProperty("--brand-primary-border", mixHex(hex, "#FFFFFF", 0.58));
    root.style.setProperty("--brand-primary-glow", hexToRgbaString(hex, 0.25));
    root.style.setProperty("--nav-active-bg", hexToRgbaString(hex, 0.18));
};

gateway.applyCustomColors = function (colors) {
    if (!colors || typeof colors !== "object") return;
    const root = document.documentElement;

    Object.entries(CUSTOM_COLOR_VARS).forEach(([inputId, cssVar]) => {
        const value = colors[inputId];
        if (inputId === "color-primary") {
            if (isHexColor(value)) gateway.applyPrimaryColor(value);
            return;
        }
        if (isHexColor(value)) {
            root.style.setProperty(cssVar, value);
        }
    });
};

gateway.clearCustomColors = function () {
    const root = document.documentElement;
    Object.values(CUSTOM_COLOR_VARS).forEach(cssVar => root.style.removeProperty(cssVar));
    [
        "--brand-primary-hover",
        "--brand-primary-light",
        "--brand-primary-border",
        "--brand-primary-glow",
        "--nav-active-bg"
    ].forEach(cssVar => root.style.removeProperty(cssVar));
    localStorage.removeItem("gateway_custom_colors");
    gateway.syncAppearanceInputs();
};

function cssColorToHex(value) {
    const text = String(value || "").trim();
    if (isHexColor(text)) return text.toUpperCase();

    const match = text.match(/^rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/i);
    if (!match) return "";
    const rgb = [Number(match[1]), Number(match[2]), Number(match[3])];
    if (rgb.some(v => !Number.isFinite(v) || v < 0 || v > 255)) return "";
    return "#" + rgb.map(v => v.toString(16).padStart(2, "0")).join("").toUpperCase();
}

gateway.syncAppearanceInputs = function () {
    const rootStyles = getComputedStyle(document.documentElement);
    Object.entries(CUSTOM_COLOR_VARS).forEach(([inputId, cssVar]) => {
        const input = document.getElementById(inputId);
        if (!input) return;
        const value = cssColorToHex(rootStyles.getPropertyValue(cssVar));
        if (value) input.value = value;
    });
};

gateway.initAppearanceEditor = function () {
    const openBtn = document.getElementById("appearance-editor-btn");
    const closeBtn = document.getElementById("appearance-close-btn");
    const saveBtn = document.getElementById("appearance-save-btn");
    const resetBtn = document.getElementById("appearance-reset-btn");
    const overlay = document.getElementById("appearance-overlay");
    const drawer = document.getElementById("appearance-drawer");

    if (!drawer || !overlay) return;

    const open = () => {
        gateway.syncAppearanceInputs();
        drawer.classList.add("open");
        overlay.classList.add("open");
        drawer.setAttribute("aria-hidden", "false");
        overlay.setAttribute("aria-hidden", "false");
    };

    const close = () => {
        drawer.classList.remove("open");
        overlay.classList.remove("open");
        drawer.setAttribute("aria-hidden", "true");
        overlay.setAttribute("aria-hidden", "true");
    };

    openBtn?.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById("accent-dropdown-menu")?.classList.remove("show");
        open();
    });

    closeBtn?.addEventListener("click", close);
    overlay.addEventListener("click", close);

    saveBtn?.addEventListener("click", () => {
        const colors = {};
        Object.keys(CUSTOM_COLOR_VARS).forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input && isHexColor(input.value)) colors[inputId] = input.value;
        });

        gateway.applyCustomColors(colors);
        localStorage.setItem("gateway_custom_colors", JSON.stringify(colors));
        gateway.syncAppearanceInputs();
        close();

        window.dispatchEvent(new CustomEvent("gateway:themechange"));
        gateway.toast?.("Appearance updated", "success");
    });

    resetBtn?.addEventListener("click", () => {
        gateway.clearCustomColors();
        window.dispatchEvent(new CustomEvent("gateway:themechange"));
        gateway.toast?.("Custom colors reset", "info");
    });

    document.querySelectorAll("[data-theme-preset]").forEach(btn => {
        btn.addEventListener("click", () => {
            const preset = btn.getAttribute("data-theme-preset");
            if (!THEME_PRESETS[preset]) return;

            document.documentElement.setAttribute("data-theme", preset);
            localStorage.setItem("gateway_theme", preset);

            document.querySelectorAll(".theme-preset-btn").forEach(b => {
                b.classList.toggle("active", b.getAttribute("data-theme-preset") === preset);
            });

            window.dispatchEvent(new CustomEvent("gateway:themechange"));
        });
    });
};

gateway.initTheme = function () {
    const savedTheme = localStorage.getItem("gateway_theme") || "light";
    const savedAccent = localStorage.getItem("gateway_accent") || "orange";
    const savedCustom = localStorage.getItem("gateway_custom_colors");

    const root = document.documentElement;
    root.setAttribute("data-theme", THEME_PRESETS[savedTheme] || "light");
    root.setAttribute("data-accent", ACCENTS.includes(savedAccent) ? savedAccent : "orange");

    if (savedCustom) {
        try {
            gateway.applyCustomColors(JSON.parse(savedCustom));
        } catch (error) {
            console.warn("Invalid saved custom colors:", error);
            localStorage.removeItem("gateway_custom_colors");
        }
    }

    document.querySelectorAll(".accent-swatch").forEach(swatch => {
        swatch.classList.toggle(
            "active",
            swatch.getAttribute("data-accent-choice") === root.getAttribute("data-accent")
        );
    });

    document.querySelectorAll(".theme-preset-btn").forEach(btn => {
        btn.classList.toggle(
            "active",
            btn.getAttribute("data-theme-preset") === root.getAttribute("data-theme")
        );
    });

    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    themeToggleBtn?.addEventListener("click", () => gateway.toggleTheme());

    const accentBtn = document.getElementById("accent-picker-btn");
    const accentMenu = document.getElementById("accent-dropdown-menu");

    if (accentBtn && accentMenu) {
        accentBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            accentMenu.classList.toggle("show");
        });

        document.addEventListener("click", (e) => {
            if (!accentMenu.contains(e.target) && e.target !== accentBtn) {
                accentMenu.classList.remove("show");
            }
        });

        document.querySelectorAll(".accent-swatch").forEach(swatch => {
            swatch.addEventListener("click", () => {
                const choice = swatch.getAttribute("data-accent-choice");
                if (choice && ACCENTS.includes(choice)) {
                    gateway.setAccent(choice);
                    accentMenu.classList.remove("show");
                }
            });
        });
    }

    gateway.initAppearanceEditor();
    gateway.syncAppearanceInputs();
};

gateway.toggleTheme = function () {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nextTheme);
    localStorage.setItem("gateway_theme", nextTheme);

    document.querySelectorAll(".theme-preset-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-theme-preset") === nextTheme);
    });

    window.dispatchEvent(new CustomEvent("gateway:themechange"));
};

gateway.setAccent = function (accent) {
    if (!ACCENTS.includes(accent)) return;

    document.documentElement.setAttribute("data-accent", accent);
    localStorage.setItem("gateway_accent", accent);

    /* Selecting a preset accent releases only a custom primary-color override. */
    const root = document.documentElement;
    root.style.removeProperty("--brand-primary");
    root.style.removeProperty("--brand-primary-hover");
    root.style.removeProperty("--brand-primary-light");
    root.style.removeProperty("--brand-primary-border");
    root.style.removeProperty("--brand-primary-glow");
    root.style.removeProperty("--nav-active-bg");

    try {
        const saved = JSON.parse(localStorage.getItem("gateway_custom_colors") || "{}");
        delete saved["color-primary"];
        localStorage.setItem("gateway_custom_colors", JSON.stringify(saved));
    } catch (_) {
        /* Ignore invalid local storage and continue. */
    }

    document.querySelectorAll(".accent-swatch").forEach(swatch => {
        swatch.classList.toggle(
            "active",
            swatch.getAttribute("data-accent-choice") === accent
        );
    });

    window.dispatchEvent(new CustomEvent("gateway:themechange"));
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
