/* Patch escaped templates in place so telemetry updates preserve focus and DOM identity. */
"use strict";
gateway.patchHtml = function (target, html) {
    const template = document.createElement("template");
    template.innerHTML = html;
    const key = node => node.nodeType === 1 ? (node.dataset.nodeId || node.dataset.id || node.id || "") : "";
    const patch = (parent, next) => {
        [...next.childNodes].forEach((fresh, index) => {
            let current = parent.childNodes[index];
            if (key(fresh) && key(current || {}) !== key(fresh)) {
                const match = [...parent.childNodes].find(node => key(node) === key(fresh));
                if (match) { parent.insertBefore(match, current || null); current = match; }
            }
            if (!current) { parent.appendChild(fresh.cloneNode(true)); return; }
            if (current.nodeType !== fresh.nodeType || current.nodeName !== fresh.nodeName || key(current) !== key(fresh)) {
                current.replaceWith(fresh.cloneNode(true)); return;
            }
            if (fresh.nodeType === 3) {
                if (current.nodeValue !== fresh.nodeValue) {
                    current.nodeValue = fresh.nodeValue;
                    if (parent.classList?.contains("dashboard-sensor-value") && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
                        parent.animate([{ backgroundColor: "#ffdfbd" }, { backgroundColor: "transparent" }], { duration: 250 });
                    }
                }
                return;
            }
            if (fresh.nodeType !== 1) return;
            [...current.attributes].forEach(attr => { if (!fresh.hasAttribute(attr.name)) current.removeAttribute(attr.name); });
            [...fresh.attributes].forEach(attr => { if (current.getAttribute(attr.name) !== attr.value) current.setAttribute(attr.name, attr.value); });
            patch(current, fresh);
        });
        while (parent.childNodes.length > next.childNodes.length) parent.lastChild.remove();
    };
    patch(target, template.content);
};
