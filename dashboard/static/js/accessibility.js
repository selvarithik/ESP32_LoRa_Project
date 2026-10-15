/* Shared tabs and focus management for existing drawers and dialogs. */
"use strict";
document.addEventListener("DOMContentLoaded", () => {
    const themeSwitch = document.getElementById("theme-toggle");
    const syncThemeSwitch = () => themeSwitch?.setAttribute("aria-checked", String(document.documentElement.dataset.theme === "dark"));
    themeSwitch?.addEventListener("click", () => gateway.toggleTheme());
    document.addEventListener("gateway:themechange", syncThemeSwitch);
    syncThemeSwitch();
    const sidebar = document.getElementById("side-navigation");
    const profile = sidebar?.querySelector("details");
    sidebar?.addEventListener("mouseleave", () => { if (!sidebar.contains(document.activeElement)) profile?.removeAttribute("open"); });
    sidebar?.addEventListener("focusout", () => { requestAnimationFrame(() => { if (!sidebar.matches(":hover") && !sidebar.contains(document.activeElement)) profile?.removeAttribute("open"); }); });
    document.querySelectorAll("[data-v3-tab]").forEach(button => {
        button.setAttribute("role", "tab");
        button.addEventListener("click", () => {
            document.querySelectorAll("[data-v3-tab]").forEach(tab => {
                const selected = tab === button;
                tab.classList.toggle("active", selected);
                tab.setAttribute("aria-selected", String(selected));
            });
            document.querySelectorAll("[data-v3-panel]").forEach(panel => {
                panel.classList.toggle("active", panel.dataset.v3Panel === button.dataset.v3Tab);
            });
        });
        button.setAttribute("aria-selected", String(button.classList.contains("active")));
    });
    document.querySelectorAll(".nav-item.active,.mobile-nav-link.active").forEach(link => link.setAttribute("aria-current", "page"));
    const selectors = ".drawer,.mobile-nav-drawer-v6,.search-modal,.dashboard-widget-drawer,.modal-overlay,.dashboard-telemetry-modal,.cmd-modal-overlay,.modal-backdrop";
    const origins = new Map();
    const visible = el => el.classList.contains("open") ||
        (el.matches(".modal-overlay,.dashboard-telemetry-modal,.cmd-modal-overlay,.modal-backdrop") &&
         el.getClientRects().length && getComputedStyle(el).visibility !== "hidden" && getComputedStyle(el).display !== "none");
    const focusable = el => [...el.querySelectorAll('a[href],button,input,select,textarea,[tabindex="0"]')].filter(item => !item.disabled && item.getClientRects().length && getComputedStyle(item).visibility !== "hidden");
    const sync = () => {
        document.querySelectorAll(selectors).forEach(el => {
            const opened = Boolean(visible(el));
            el.inert = !opened;
            if (opened && !origins.has(el)) {
                origins.set(el, el.returnFocus || document.activeElement);
                const dialog = el.querySelector('[role="dialog"]') || el;
                dialog.setAttribute("role", "dialog");
                dialog.setAttribute("aria-modal", "true");
                if (!dialog.hasAttribute("aria-label")) dialog.setAttribute("aria-label", dialog.querySelector("h2,h3")?.textContent || "Gateway dialog");
                if (!el.contains(document.activeElement)) focusable(el)[0]?.focus();
            }
        });
        for (const [el, origin] of origins) {
            if (!el.isConnected || !visible(el)) {
                origins.delete(el);
                if (origin?.isConnected) origin.focus();
            }
        }
    };
    const observer = new MutationObserver(sync);
    observer.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["class", "style"] });
    sync();
    document.addEventListener("keydown", event => {
        const dialog = [...origins.keys()].at(-1);
        if (!dialog) return;
        if (event.key === "Tab") {
            const controls = focusable(dialog);
            const first = controls[0], last = controls.at(-1);
            if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) { event.preventDefault(); last?.focus(); }
            else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) { event.preventDefault(); first?.focus(); }
        }
        if (event.key === "Escape") {
            dialog.querySelector('[data-close-telemetry],.mobile-drawer-close-v6,.modal-close-btn,.drawer-header button,.dashboard-drawer-close,[id$="cancel"]')?.click();
        }
    });
    window.addEventListener("pagehide", () => observer.disconnect());
});
