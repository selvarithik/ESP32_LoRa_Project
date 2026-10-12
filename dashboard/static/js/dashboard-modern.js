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

    /* Toasts + sensor detail popup */
    var toastBox = document.createElement("div"); toastBox.className = "dm-toasts"; toastBox.setAttribute("aria-live", "polite");
    document.body.appendChild(toastBox);
    function toast(msg, kind) {
      var t = document.createElement("div"); t.className = "dm-toast " + (kind || ""); t.textContent = msg;
      toastBox.appendChild(t);
      setTimeout(function () { t.classList.add("out"); setTimeout(function () { t.remove(); }, 260); }, 3200);
    }

    var overlay = document.createElement("div");
    overlay.className = "dm-modal-overlay";
    overlay.innerHTML = '<div class="dm-modal" role="dialog" aria-modal="true" aria-label="Sensor details">' +
      '<div class="dm-modal-head"><button class="dm-modal-close" type="button" aria-label="Close">&times;</button>' +
      '<small></small><h3></h3><div class="dm-modal-value"></div></div><div class="dm-modal-body"></div></div>';
    document.body.appendChild(overlay);
    var lastFocus = null;
    function closeModal() { overlay.classList.remove("open"); lastFocus && lastFocus.focus && lastFocus.focus(); }
    overlay.addEventListener("click", function (e) { if (e.target === overlay || e.target.closest(".dm-modal-close")) closeModal(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && overlay.classList.contains("open")) closeModal(); });

    root.addEventListener("click", function (event) {
      var card = event.target.closest(".dashboard-sensor-card");
      if (!card) return;
      var node = card.closest("[data-node-name]");
      var nodeName = node ? { textContent: node.getAttribute("data-node-name") } : null;
      var name = card.querySelector(".dashboard-sensor-name");
      var value = card.querySelector(".dashboard-sensor-value");
      var status = card.querySelector(".dashboard-sensor-status");
      overlay.querySelector("small").textContent = (nodeName ? nodeName.textContent : "Sensor") + (status ? "  ·  " + status.textContent.trim() : "");
      overlay.querySelector("h3").textContent = name ? name.textContent : "Sensor";
      overlay.querySelector(".dm-modal-value").innerHTML = value ? value.innerHTML : "";
      overlay.querySelector(".dm-modal-body").innerHTML = Array.prototype.map.call(card.querySelectorAll(".dashboard-sensor-meta>div"), function (d) { return "<div>" + d.innerHTML + "</div>"; }).join("");
      lastFocus = document.activeElement;
      overlay.classList.add("open");
      overlay.querySelector(".dm-modal-close").focus();
    });

    /* Toast when the problem count changes (value already rendered by dashboard.js) */
    var prevProblems = null;
    var alarm = document.getElementById("alarm-count");
    alarm && new MutationObserver(function () {
      var n = Number(alarm.textContent);
      if (!isFinite(n) || n === prevProblems) return;
      if (prevProblems !== null) toast(n > prevProblems ? "Problems increased to " + n : (n === 0 ? "All problems cleared" : "Problems reduced to " + n), n > prevProblems ? "warn" : "ok");
      prevProblems = n;
    }).observe(alarm, { childList: true, characterData: true, subtree: true });

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
