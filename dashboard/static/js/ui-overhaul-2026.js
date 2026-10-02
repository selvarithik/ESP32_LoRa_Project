/* =========================================================
   SELVARITHIK A&D LORA GATEWAY — UI OVERHAUL INTERACTIONS
   Small, non-invasive accessibility and navigation improvements.
   ========================================================= */
"use strict";

(() => {
  const ready = (fn) => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  };

  ready(() => {
    const search = document.getElementById("global-nav-search");
    const drawer = document.getElementById("mobileNavDrawer");
    const menu = document.getElementById("mobile-menu-btn");

    // Keyboard shortcut: Ctrl/Cmd + K focuses page search.
    document.addEventListener("keydown", (event) => {
      const tag = document.activeElement?.tagName;
      const typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        search?.focus();
        search?.select();
      }

      if (event.key === "Escape" && drawer?.classList.contains("open")) {
        drawer.classList.remove("open");
        drawer.setAttribute("aria-hidden", "true");
        menu?.setAttribute("aria-expanded", "false");
      }

      // Do not steal Escape from dialogs/forms.
      if (event.key === "Escape" && typing) return;
    });

    // Clicking the drawer backdrop closes it.
    drawer?.addEventListener("click", (event) => {
      if (event.target === drawer) {
        drawer.classList.remove("open");
        drawer.setAttribute("aria-hidden", "true");
        menu?.setAttribute("aria-expanded", "false");
      }
    });

    // Mark the active route for assistive technology.
    const current = window.location.pathname.replace(/\/+$/, "") || "/";
    document.querySelectorAll(".nav-item[data-path], .mobile-nav-link[data-path]")
      .forEach((link) => {
        const path = (link.getAttribute("data-path") || "").replace(/\/+$/, "") || "/";
        if (path === current) {
          link.setAttribute("aria-current", "page");
        } else {
          link.removeAttribute("aria-current");
        }
      });

    // Search supports direct page navigation and "/" as a quick focus key.
    document.addEventListener("keydown", (event) => {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) return;
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      event.preventDefault();
      search?.focus();
    });

    // Prevent horizontal layout jumps when very wide tables are present.
    document.querySelectorAll("table").forEach((table) => {
      if (!table.parentElement?.classList.contains("table-responsive") &&
          !table.parentElement?.classList.contains("table-wrap") &&
          !table.parentElement?.classList.contains("table-container")) {
        const wrapper = document.createElement("div");
        wrapper.className = "table-responsive";
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      }
    });
  });
})();
