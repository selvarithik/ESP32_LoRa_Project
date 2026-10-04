/*
  UI V4 shell controller.
  Fixes the desktop sidebar collapse, title bar identity, tooltips and
  adds lightweight motion without changing gateway routes/APIs.
*/
(function(){
  "use strict";

  const body = document.body;

  function setPageTitle(){
    const page = document.getElementById("page-title");
    const title = (page?.textContent || "Dashboard").trim() || "Dashboard";
    document.title = title + " — SELVARITHIK'S A&D LORA GATEWAY";
    body.style.setProperty("--v4-page-title", JSON.stringify(title.toUpperCase()));
  }

  function hardApplySidebarState(){
    const btn = document.getElementById("sidebar-collapse-btn");
    const collapsed = body.classList.contains("sidebar-collapsed");
    if(btn){
      btn.setAttribute("aria-expanded", String(!collapsed));
      btn.setAttribute("aria-label", collapsed ? "Expand navigation" : "Minimize navigation");
      btn.title = collapsed ? "Expand navigation" : "Minimize navigation";
    }
    body.style.setProperty("--v4-sidebar-state", collapsed ? "collapsed" : "expanded");
  }

  function ensureSidebarPersistence(){
    const btn=document.getElementById("sidebar-collapse-btn");
    if(!btn) return;

    // app.js already owns the collapse click handler. Do not bind a second
    // listener here or one click would toggle the sidebar twice.
    if(btn.dataset.bound!=="1"){
      const key="selvarithik-sidebar-collapsed";
      let collapsed=false;
      try{ collapsed=localStorage.getItem(key)==="1"; }catch(_){}
      body.classList.toggle("sidebar-collapsed",collapsed);
    }

    hardApplySidebarState();

    window.addEventListener("resize",()=>{
      if(window.innerWidth<=780){
        body.classList.remove("sidebar-collapsed");
      }
      hardApplySidebarState();
    });
  }

  function addNavTooltips(){
    if(window.innerWidth<=780) return;
    const navItems=[...document.querySelectorAll(".sidebar9-inspired .nav-item.nav-v6")];
    const sidebar=document.querySelector(".sidebar9-inspired");
    if(!sidebar || navItems.length===0) return;

    const tip=document.createElement("div");
    tip.className="v4-nav-tooltip";
    tip.setAttribute("role","tooltip");
    document.body.appendChild(tip);

    navItems.forEach(item=>{
      const label=item.querySelector(":scope > span")?.textContent?.trim() || item.getAttribute("aria-label") || "Navigation";
      item.addEventListener("mouseenter",()=>{
        if(!body.classList.contains("sidebar-collapsed")) return;
        const r=item.getBoundingClientRect();
        tip.textContent=label;
        tip.style.left=(r.right+10)+"px";
        tip.style.top=(r.top + r.height/2)+"px";
        tip.style.transform="translateY(-50%) scale(1)";
        tip.classList.add("is-visible");
      });
      item.addEventListener("mouseleave",()=>{
        tip.classList.remove("is-visible");
      });
      item.addEventListener("focus",()=>{
        if(!body.classList.contains("sidebar-collapsed")) return;
        const r=item.getBoundingClientRect();
        tip.textContent=label;
        tip.style.left=(r.right+10)+"px";
        tip.style.top=(r.top + r.height/2)+"px";
        tip.style.transform="translateY(-50%) scale(1)";
        tip.classList.add("is-visible");
      });
      item.addEventListener("blur",()=>tip.classList.remove("is-visible"));
    });
  }

  function addButtonRipple(){
    if(window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    document.addEventListener("pointerdown",(e)=>{
      const btn=e.target.closest(".btn-primary,.btn-secondary,.btn-dispatch-command,.sidebar-collapse-btn");
      if(!btn) return;
      const r=btn.getBoundingClientRect();
      const ripple=document.createElement("span");
      ripple.className="v4-click-ripple";
      Object.assign(ripple.style,{
        position:"absolute",
        width:"10px",
        height:"10px",
        borderRadius:"50%",
        left:(e.clientX-r.left-5)+"px",
        top:(e.clientY-r.top-5)+"px",
        background:"rgba(255,255,255,.24)",
        pointerEvents:"none",
        transform:"scale(0)",
        animation:"v4-ripple .55s ease-out forwards",
        zIndex:"2"
      });
      btn.appendChild(ripple);
      window.setTimeout(()=>ripple.remove(),600);
    });
  }

  function init(){
    body.classList.add("ui-v4-shell");
    setPageTitle();
    ensureSidebarPersistence();
    addNavTooltips();
    addButtonRipple();
    hardApplySidebarState();
  }

  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",init,{once:true});
  }else{
    init();
  }
})();
