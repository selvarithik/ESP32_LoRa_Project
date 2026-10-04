/*
  UI V3 shell interactions.
  Header search command palette, navigation motion, appearance toggle, ripple.
*/
(function(){
  "use strict";

  const routes = [
    ["/","Dashboard","Live gateway overview, node availability and telemetry."],
    ["/nodes","Nodes","Manage connected gateway nodes."],
    ["/sensors","Sensors","Monitor configured telemetry parameters."],
    ["/command-center","Command Center","Create and monitor gateway commands."],
    ["/communication","Communication","Gateway connectivity and network state."],
    ["/firmware","Firmware & OTA","Firmware releases and OTA operations."],
    ["/logs","Logs","Gateway events and diagnostics."],
    ["/system-overview","System Health","Gateway runtime health and services."],
    ["/system","System","Gateway configuration and maintenance."],
    ["/chat","Private Chat","Private gateway communication."]
  ];

  const esc = (v) => String(v).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));

  function makePalette(){
    if(document.getElementById("v3-command-backdrop")) return;
    const backdrop=document.createElement("div");
    backdrop.id="v3-command-backdrop";
    backdrop.className="v3-command-backdrop";

    const palette=document.createElement("section");
    palette.id="v3-command-palette";
    palette.className="v3-command-palette";
    palette.setAttribute("role","dialog");
    palette.setAttribute("aria-modal","true");
    palette.setAttribute("aria-label","Search pages");

    palette.innerHTML=
      '<div class="v3-command-head">'+
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 5 5"/></svg>'+
        '<input class="v3-command-input" id="v3-command-input" placeholder="Search pages..." autocomplete="off" />'+
        '<span class="v3-command-hint">ESC</span>'+
      '</div>'+
      '<div class="v3-command-list" id="v3-command-list"></div>';

    document.body.append(backdrop,palette);
    backdrop.addEventListener("click",closePalette);
    palette.addEventListener("click",e=>{
      const item=e.target.closest("[data-route]");
      if(item) window.location.href=item.dataset.route;
    });

    renderRoutes("");
  }

  function renderRoutes(query){
    const list=document.getElementById("v3-command-list");
    if(!list) return;
    const q=(query||"").trim().toLowerCase();
    const items=routes.filter(r=>!q || r.join(" ").toLowerCase().includes(q));
    list.innerHTML=items.length ? items.map((r,i)=>
      '<button class="v3-command-item'+(i===0?' is-active':'')+'" type="button" data-route="'+esc(r[0])+'">'+
        '<span class="v3-command-icon">↗</span>'+
        '<span class="v3-command-copy"><strong>'+esc(r[1])+'</strong><span>'+esc(r[2])+'</span></span>'+
      '</button>'
    ).join("") :
      '<div class="v3-command-copy" style="padding:22px;color:var(--v3-muted)">No page found.</div>';
  }

  function openPalette(){
    makePalette();
    const b=document.getElementById("v3-command-backdrop");
    const p=document.getElementById("v3-command-palette");
    b.classList.add("is-open"); p.classList.add("is-open");
    const input=document.getElementById("v3-command-input");
    input.value="";
    renderRoutes("");
    requestAnimationFrame(()=>input.focus());
  }

  function closePalette(){
    document.getElementById("v3-command-backdrop")?.classList.remove("is-open");
    document.getElementById("v3-command-palette")?.classList.remove("is-open");
  }

  function bindSearch(){
    const search=document.getElementById("global-nav-search");
    if(!search) return;
    search.setAttribute("readonly","readonly");
    search.setAttribute("aria-label","Open page search");
    search.addEventListener("focus",openPalette);
    search.addEventListener("click",openPalette);
    document.addEventListener("keydown",e=>{
      if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==="k"){
        e.preventDefault(); openPalette();
      }
      if(e.key==="/" && !["INPUT","TEXTAREA"].includes(document.activeElement.tagName)){
        e.preventDefault(); openPalette();
      }
      if(e.key==="Escape") closePalette();
    });
    document.addEventListener("input",e=>{
      if(e.target.id==="v3-command-input") renderRoutes(e.target.value);
    });
  }

  function bindAppearance(){
    const footer=document.querySelector(".sidebar-footer-v6");
    if(!footer || document.getElementById("v3-theme-toggle")) return;
    const btn=document.createElement("button");
    btn.id="v3-theme-toggle";
    btn.className="sidebar9-action";
    btn.type="button";
    btn.title="Toggle light / dark mode";
    btn.setAttribute("aria-label","Toggle light / dark mode");
    btn.innerHTML='<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
    footer.appendChild(btn);
    const saved=localStorage.getItem("gateway-theme");
    if(saved==="dark") document.documentElement.setAttribute("data-theme","dark");
    btn.addEventListener("click",()=>{
      const dark=document.documentElement.getAttribute("data-theme")==="dark";
      document.documentElement.setAttribute("data-theme",dark?"light":"dark");
      localStorage.setItem("gateway-theme",dark?"light":"dark");
    });
  }

  function bindRipple(){
    document.addEventListener("pointerdown",e=>{
      const target=e.target.closest(".nav-item,.sidebar9-action,.sidebar-collapse-btn,.mobile-nav-link");
      if(!target || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const rect=target.getBoundingClientRect();
      const dot=document.createElement("span");
      dot.className="v3-ripple";
      dot.style.left=(e.clientX-rect.left-5)+"px";
      dot.style.top=(e.clientY-rect.top-5)+"px";
      target.appendChild(dot);
      setTimeout(()=>dot.remove(),550);
    });
  }

  function init(){
    document.body.classList.add("ui-v3-shell");
    bindSearch();
    bindAppearance();
    bindRipple();
  }

  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",init);
  else init();
})();
