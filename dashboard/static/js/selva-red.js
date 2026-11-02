/* Presentation only. Never writes device, broker, sensor or network configuration. */
"use strict";
document.addEventListener("DOMContentLoaded", () => {
    const shell = document.getElementById("app-shell");
    const toggle = document.getElementById("mobile-menu-btn");
    if (!shell || !toggle) return;
    const desktop = window.matchMedia("(min-width: 1024px) and (hover: hover)");
    function describe() {
        toggle.setAttribute("aria-label", desktop.matches ? "Toggle navigation" : "Open navigation");
        toggle.setAttribute("aria-controls", desktop.matches ? "side-navigation" : "mobileNavDrawer");
        if (desktop.matches) toggle.setAttribute("aria-expanded", String(shell.classList.contains("nav-pinned") || document.querySelector('.modern-sidebar').matches(':hover,:focus-within')));
    }
    toggle.addEventListener("click", event => {
        if (!desktop.matches) return; // Existing authenticated mobile drawer remains in charge.
        event.stopImmediatePropagation();
        shell.classList.toggle("nav-pinned");
        describe();
    }, true);
    desktop.addEventListener("change", describe);
    const sidebar = document.querySelector('.modern-sidebar');
    sidebar.addEventListener('pointerenter', describe);
    sidebar.addEventListener('pointerleave', describe);
    sidebar.addEventListener('focusin', describe);
    sidebar.addEventListener('focusout', () => queueMicrotask(describe));
    describe();
});
