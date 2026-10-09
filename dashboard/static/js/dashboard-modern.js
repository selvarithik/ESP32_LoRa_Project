"use strict";
/* Dashboard page enhancements - presentation only, reads values dashboard.js already renders. */
(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn, { once: true });
    else fn();
  }

  ready(function () {
    var root = document.getElementById("dashboard-console");
    if (!root) return;

    /* KPI count-up: animates numeric changes written by dashboard.js */
    var ids = ["total-nodes", "online-nodes", "sensor-count", "alarm-count"];
    var busy = new WeakSet();
    var shown = {};

    function animate(el, to) {
      var from = shown[el.id] || 0;
      shown[el.id] = to;
      if (reduce || from === to) { if (el.textContent !== String(to)) el.textContent = String(to); return; }
      var start = performance.now(), dur = 600;
      busy.add(el);
      (function step(now) {
        var t = Math.min(1, (now - start) / dur);
        var eased = 1 - Math.pow(1 - t, 3);
        el.textContent = String(Math.round(from + (to - from) * eased));
        if (t < 1) requestAnimationFrame(step); else busy.delete(el);
      })(start);
    }

    function markProblems(value) {
      var card = document.querySelector(".kpi-problems");
      if (!card) return;
      var n = Number(value);
      card.classList.toggle("is-alert", n > 0);
      card.classList.toggle("is-clear", n === 0);
    }

    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      new MutationObserver(function () {
        if (busy.has(el)) return;
        if (el.textContent === String(shown[id])) return;
        var n = Number(el.textContent);
        if (!isFinite(n) || el.textContent.trim() === "") return;
        if (id === "alarm-count") markProblems(n);
        animate(el, n);
      }).observe(el, { childList: true, characterData: true, subtree: true });
    });

    /* Tap / click a sensor card to expand its full detail list */
    root.addEventListener("click", function (event) {
      var card = event.target.closest(".dashboard-sensor-card");
      if (card) card.classList.toggle("expanded");
    });

    /* Refresh button feedback */
    var refresh = document.getElementById("dashboard-refresh");
    refresh && refresh.addEventListener("click", function () {
      refresh.classList.add("is-spinning");
      setTimeout(function () { refresh.classList.remove("is-spinning"); }, 900);
    });

    /* Escape closes the layout drawer */
    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      var close = document.getElementById("close-widget-drawer");
      var drawer = document.getElementById("widget-drawer");
      if (close && drawer && drawer.classList.contains("open")) close.click();
    });
  });
})();
