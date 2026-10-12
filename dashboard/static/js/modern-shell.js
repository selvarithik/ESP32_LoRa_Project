"use strict";

(function () {
  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  }

  ready(function () {
    var modal = document.getElementById("global-search-modal");
    var input = document.getElementById("global-nav-search");
    var results = document.getElementById("global-search-results");
    var openButton = document.getElementById("global-nav-search-button");
    var links = Array.prototype.slice.call(document.querySelectorAll(".modern-nav .nav-item[data-path]"));
    var mobileLinks = Array.prototype.slice.call(document.querySelectorAll(".mobile-nav-link[data-path]"));
    var collapseButton = document.getElementById("sidebar-collapse-btn");
    var mobileMenuButton = document.getElementById("mobile-menu-btn");
    var mobileDrawer = document.getElementById("mobileNavDrawer");
    var mobileCloseButton = document.querySelector(".mobile-drawer-close-v6");

    function currentPath() {
      return window.location.pathname.replace(/\\/$/, "") || "/";
    }

    function syncActiveNavigation() {
      var path = currentPath();
      links.concat(mobileLinks).forEach(function (link) {
        var target = (link.getAttribute("data-path") || "").replace(/\\/$/, "") || "/";
        link.classList.toggle("active", target === path);
      });
    }

    function closeMobileNavigation() {
      if (!mobileDrawer) return;
      mobileDrawer.classList.remove("open");
      mobileDrawer.setAttribute("aria-hidden", "true");
    }

    function openMobileNavigation() {
      if (!mobileDrawer) return;
      mobileDrawer.classList.add("open");
      mobileDrawer.setAttribute("aria-hidden", "false");
    }

    function pageItems() {
      return links.map(function (link) {
        return {
          title: (link.querySelector("span") || link).textContent.trim(),
          href: link.getAttribute("href"),
          path: link.getAttribute("data-path") || "",
          label: link.getAttribute("data-search-label") || link.textContent
        };
      });
    }

    function render(query) {
      if (!results) return;
      var q = String(query || "").trim().toLowerCase();
      var items = pageItems().filter(function (item) {
        return !q || [item.title, item.path, item.label].join(" ").toLowerCase().indexOf(q) >= 0;
      });

      if (!items.length) {
        results.innerHTML = '<div class="search-result"><span>No page found</span><small>Use the existing navigation routes</small></div>';
        return;
      }

      results.innerHTML = items.map(function (item, index) {
        return '<button class="search-result' + (index === 0 ? " active" : "") + '" type="button" data-search-href="' + item.href + '">' +
          '<span>' + escapeHtml(item.title) + '</span><small>' + escapeHtml(item.path) + '</small></button>';
      }).join("");
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, function (ch) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[ch];
      });
    }

    function openSearch() {
      if (!modal || !input) return;
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
      render(input.value);
      setTimeout(function () {
        input.focus();
        input.select();
      }, 30);
    }

    function closeSearch() {
      if (!modal) return;
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }

    syncActiveNavigation();

    collapseButton?.addEventListener("click", function () {
      var collapsed = document.body.classList.toggle("sidebar-collapsed");
      try { localStorage.setItem("gateway_sidebar_collapsed", collapsed ? "1" : "0"); } catch (error) {}
      collapseButton.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
      collapseButton.setAttribute("title", collapsed ? "Expand sidebar" : "Collapse sidebar");
    });

    try {
      if (localStorage.getItem("gateway_sidebar_collapsed") === "1") {
        document.body.classList.add("sidebar-collapsed");
      }
    } catch (error) {}

    mobileMenuButton?.addEventListener("click", openMobileNavigation);
    mobileCloseButton?.addEventListener("click", closeMobileNavigation);
    mobileDrawer?.addEventListener("click", function (event) {
      if (event.target === mobileDrawer) closeMobileNavigation();
    });
    mobileLinks.forEach(function (link) {
      link.addEventListener("click", closeMobileNavigation);
    });

    openButton?.addEventListener("click", openSearch);
    document.querySelectorAll("[data-close-search]").forEach(function (el) {
      el.addEventListener("click", closeSearch);
    });

    input?.addEventListener("input", function () {
      render(input.value);
    });

    input?.addEventListener("keydown", function (event) {
      var active = results?.querySelector(".search-result.active");
      var all = Array.prototype.slice.call(results?.querySelectorAll(".search-result[data-search-href]") || []);
      var index = all.indexOf(active);

      if (event.key === "Escape") {
        closeSearch();
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        if (all.length) {
          all.forEach(function (item) { item.classList.remove("active"); });
          all[(index + 1 + all.length) % all.length].classList.add("active");
        }
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        if (all.length) {
          all.forEach(function (item) { item.classList.remove("active"); });
          all[(index - 1 + all.length) % all.length].classList.add("active");
        }
      } else if (event.key === "Enter") {
        event.preventDefault();
        if (active && active.dataset.searchHref) {
          window.location.href = active.dataset.searchHref;
        }
      }
    });

    results?.addEventListener("click", function (event) {
      var target = event.target.closest("[data-search-href]");
      if (target) window.location.href = target.dataset.searchHref;
    });

    document.addEventListener("keydown", function (event) {
      var mac = navigator.platform && navigator.platform.toLowerCase().indexOf("mac") >= 0;
      if ((mac ? event.metaKey : event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        openSearch();
      }
      if (event.key === "Escape" && modal?.classList.contains("open")) {
        closeSearch();
      }
    });
  });
})();
