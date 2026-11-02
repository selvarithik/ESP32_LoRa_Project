/* Presentation only: desktop navigation expands by CSS hover/focus; mobile uses app.js. */
"use strict";
document.addEventListener("DOMContentLoaded", () => {
 const toggle=document.getElementById("mobile-menu-btn"),drawer=document.getElementById("mobileNavDrawer");
 if(!toggle||!drawer)return;
 const desktop=window.matchMedia("(min-width: 1024px) and (hover: hover)");
 function describe(){
  toggle.setAttribute("aria-label","Open navigation");
  toggle.setAttribute("aria-controls","mobileNavDrawer");
  if(desktop.matches){drawer.classList.remove("open");drawer.setAttribute("aria-hidden","true");toggle.setAttribute("aria-expanded","false");}
 }
 desktop.addEventListener("change",describe);describe();
});
