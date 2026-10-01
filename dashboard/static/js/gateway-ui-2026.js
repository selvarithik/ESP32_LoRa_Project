/* ============================================================
   SELVARITHIK'S LORA GATEWAY
   UI 2026 — MICRO INTERACTIONS
   ============================================================ */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const body = document.body;

    body?.classList.add("ui-modern");
    root?.setAttribute("data-theme", "light");
    root?.removeAttribute("data-accent");
    root?.removeAttribute("data-palette");

    const tooltip = document.createElement("div");
    tooltip.className = "ui-nav-hover-card";
    tooltip.setAttribute("role", "tooltip");
    tooltip.innerHTML =
        '<div class="ui-nav-hover-card__kicker">Gateway</div>' +
        '<div class="ui-nav-hover-card__title"></div>' +
        '<div class="ui-nav-hover-card__text"></div>';
    document.body.appendChild(tooltip);

    const titleNode = tooltip.querySelector(".ui-nav-hover-card__title");
    const textNode = tooltip.querySelector(".ui-nav-hover-card__text");

    let activeLink = null;
    let closeTimer = null;

    const escapeHtml = (value) => {
        if (window.gateway?.escape) return window.gateway.escape(value);
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    const hideTooltip = () => {
        if (closeTimer) {
            clearTimeout(closeTimer);
            closeTimer = null;
        }
        tooltip.classList.remove("is-visible");
        activeLink = null;
    };

    const positionTooltip = (link) => {
        const rect = link.getBoundingClientRect();
        const gap = 12;
        const width = tooltip.offsetWidth || 280;
        const height = tooltip.offsetHeight || 120;

        let left = rect.right + gap;
        let top = rect.top + rect.height / 2 - height / 2;

        if (left + width > window.innerWidth - 10) {
            left = Math.max(10, rect.left - width - gap);
        }

        top = Math.max(10, Math.min(top, window.innerHeight - height - 10));
        tooltip.style.left = Math.round(left) + "px";
        tooltip.style.top = Math.round(top) + "px";
    };

    const showTooltip = (link) => {
        if (window.matchMedia("(hover: none)").matches) return;

        if (closeTimer) {
            clearTimeout(closeTimer);
            closeTimer = null;
        }

        activeLink = link;
        titleNode.textContent = link.dataset.tooltipTitle || link.getAttribute("aria-label") || "Gateway";
        textNode.textContent = link.dataset.tooltipText || "Open this gateway section.";
        tooltip.classList.add("is-visible");
        requestAnimationFrame(() => positionTooltip(link));
    };

    document.querySelectorAll(".nav-item.nav-v6").forEach((link) => {
        link.addEventListener("mouseenter", () => showTooltip(link));
        link.addEventListener("mouseleave", () => {
            closeTimer = setTimeout(hideTooltip, 60);
        });
        link.addEventListener("focus", () => showTooltip(link));
        link.addEventListener("blur", hideTooltip);
    });

    window.addEventListener("resize", () => {
        if (activeLink) positionTooltip(activeLink);
    }, { passive: true });

    window.addEventListener("scroll", hideTooltip, { passive: true });

    document.addEventListener("click", (event) => {
        const button = event.target.closest(".dashboard-action, .dashboard-mini-tool");
        if (!button || button.disabled) return;

        const rect = button.getBoundingClientRect();
        const ripple = document.createElement("span");
        ripple.style.position = "absolute";
        ripple.style.pointerEvents = "none";
        ripple.style.borderRadius = "999px";
        ripple.style.width = "20px";
        ripple.style.height = "20px";
        ripple.style.left = (event.clientX - rect.left - 10) + "px";
        ripple.style.top = (event.clientY - rect.top - 10) + "px";
        ripple.style.background = "rgba(255,255,255,.32)";
        ripple.style.transform = "scale(0)";
        ripple.style.opacity = "1";
        ripple.style.transition = "transform 380ms ease, opacity 380ms ease";

        if (getComputedStyle(button).position === "static") {
            button.style.position = "relative";
        }

        button.appendChild(ripple);
        requestAnimationFrame(() => {
            ripple.style.transform = "scale(8)";
            ripple.style.opacity = "0";
        });

        setTimeout(() => ripple.remove(), 420);
    });

    window.addEventListener("gateway:palettechange", () => {
        root.removeAttribute("data-palette");
        root.setAttribute("data-theme", "light");
    });

    window.addEventListener("gateway:themechange", () => {
        root.setAttribute("data-theme", "light");
    });
});
