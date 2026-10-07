(function(){
"use strict";
const body=document.body,$=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
function title(){const t=($("#page-title")?.textContent||"Dashboard").trim()||"Dashboard";document.title=t+" — SELVARITHIK'S A&D LORA GATEWAY";}
function collapse(){const b=$("#sidebar-collapse-btn");if(!b)return;const key="selvarithik-sidebar-collapsed";let c=false;try{c=localStorage.getItem(key)==="1"}catch(_){}
body.classList.toggle("sidebar-collapsed",c);
const sync=()=>{const x=body.classList.contains("sidebar-collapsed");b.title=x?"Expand navigation":"Minimize navigation";b.setAttribute("aria-label",b.title);b.setAttribute("aria-expanded",String(!x));};
sync();
if(b.dataset.v5Bound!=="1"){b.dataset.v5Bound="1";b.addEventListener("click",()=>{const x=!body.classList.contains("sidebar-collapsed");body.classList.toggle("sidebar-collapsed",x);try{localStorage.setItem(key,x?"1":"0")}catch(_){ }sync();});}}
function tooltips(){let tip=$("#v5-nav-tip");if(!tip){tip=document.createElement("div");tip.id="v5-nav-tip";tip.className="v5-nav-tip";document.body.appendChild(tip)};$$(".sidebar9-inspired .nav-item.nav-v6").forEach(i=>{const show=()=>{if(!body.classList.contains("sidebar-collapsed"))return;const r=i.getBoundingClientRect();tip.textContent=i.dataset.tooltipTitle||i.querySelector(":scope>span")?.textContent||i.getAttribute("aria-label")||"Navigation";tip.style.left=r.right+10+"px";tip.style.top=r.top+r.height/2+"px";tip.classList.add("show")};i.addEventListener("mouseenter",show);i.addEventListener("mouseleave",()=>tip.classList.remove("show"));i.addEventListener("focus",show);i.addEventListener("blur",()=>tip.classList.remove("show"))})}
function user(){const u=$(".gateway-user-static");if(!u||u.dataset.v5User==="1")return;u.dataset.v5User="1";const p=document.createElement("div");p.id="v5-user-pop";p.className="v5-user-pop";p.innerHTML='<strong style="display:block;color:var(--v5-text);font-size:12px">Gateway User</strong><span style="display:block;color:var(--v5-muted);font-size:10px;margin:3px 0 9px">Local access</span><button data-go="/system">Settings</button><button data-go="/logout">Log out</button>';p.querySelectorAll("button").forEach(b=>{b.style.cssText="display:block;width:100%;padding:9px;border:0;border-radius:8px;background:transparent;text-align:left;color:var(--v5-text);cursor:pointer";b.addEventListener("click",()=>location.href=b.dataset.go)});document.body.appendChild(p);u.addEventListener("click",e=>{e.stopPropagation();const r=u.getBoundingClientRect();p.style.left=r.left+"px";p.style.top=r.bottom+8+"px";p.classList.toggle("show")});document.addEventListener("click",()=>p.classList.remove("show"))}
function search(){const s=$("#global-nav-search");if(!s)return;const routes=[["/","Dashboard"],["/nodes","Nodes"],["/sensors","Sensors"],["/command-center","Commands"],["/communication","Network"],["/firmware","Firmware & OTA"],["/logs","Logs"],["/system-overview","System Health"],["/system","System"],["/chat","Private Chat"]];function open(){let m=$("#v5-page-search");if(!m){m=document.createElement("div");m.id="v5-page-search";m.className="v5-page-search";m.innerHTML='<div class="v5-search-bg"></div><div class="v5-search-dialog"><div class="v5-search-head"><b>⌕</b><input placeholder="Search pages..."><kbd>ESC</kbd></div><div class="v5-search-list"></div></div>';document.body.appendChild(m);m.querySelector(".v5-search-bg").onclick=()=>m.classList.remove("open");m.querySelector("input").oninput=e=>render(e.target.value);m.onclick=e=>{const i=e.target.closest("[data-route]");if(i)location.href=i.dataset.route}}m.classList.add("open");const q=m.querySelector("input");q.value="";render("");setTimeout(()=>q.focus(),20);function render(v){const x=v.toLowerCase().trim();m.querySelector(".v5-search-list").innerHTML=routes.filter(r=>!x||r.join(" ").toLowerCase().includes(x)).map(r=>'<button class="v5-search-item" data-route="'+r[0]+'"><b>'+r[1]+'</b><span>'+r[0]+'</span></button>').join("")||'<div style="padding:22px;color:var(--v5-muted)">No page found</div>'}}s.readOnly=true;s.onclick=open;s.onfocus=open;document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();open()}if(e.key==="Escape")$("#v5-page-search")?.classList.remove("open")})}
function init(){body.classList.add("ui-v5-rebuild");title();collapse();tooltips();user();search()} if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();

(function(){
  "use strict";
  function initReferenceInteractions(){
    const body=document.body;
    if(!body.classList.contains("ui-v5-rebuild")) return;

    const rail=document.querySelector(".sidebar9-inspired");
    const toggle=document.getElementById("sidebar-collapse-btn");
    const search=document.getElementById("global-nav-search");
    const user=document.querySelector(".gateway-user-static");

    const key="selvarithik-sidebar-collapsed";
    let collapsed=false;
    try{collapsed=localStorage.getItem(key)==="1"}catch(_){}

    function sync(){
      body.classList.toggle("sidebar-collapsed",collapsed);
      if(toggle){
        toggle.setAttribute("aria-label",collapsed?"Expand navigation":"Minimize navigation");
        toggle.setAttribute("title",collapsed?"Expand navigation":"Minimize navigation");
        toggle.setAttribute("aria-expanded",String(!collapsed));
      }
    }
    sync();

    if(toggle && toggle.dataset.v6Bound!=="1"){
      toggle.dataset.v6Bound="1";
      toggle.addEventListener("click",function(){
        collapsed=!body.classList.contains("sidebar-collapsed");
        try{localStorage.setItem(key,collapsed?"1":"0")}catch(_){}
        sync();
      });
    }

    // Pointer-follow highlight: subtle only, no layout movement.
    if(rail && !window.matchMedia("(prefers-reduced-motion: reduce)").matches){
      rail.addEventListener("pointermove",function(e){
        const rect=rail.getBoundingClientRect();
        rail.style.setProperty("--rail-x",((e.clientX-rect.left)/rect.width*100).toFixed(1)+"%");
        rail.style.setProperty("--rail-y",((e.clientY-rect.top)/rect.height*100).toFixed(1)+"%");
      });
    }

    // User popup using the reference-style compact account control.
    if(user && !user.dataset.v6User){
      user.dataset.v6User="1";
      const pop=document.createElement("div");
      pop.className="v6-user-popup";
      pop.innerHTML='<div class="v6-user-head"><div class="v6-user-dot">GW</div><div><strong>Gateway User</strong><span>Local access</span></div></div><button data-go="/system">Settings</button><button data-go="/logout">Log out</button>';
      document.body.appendChild(pop);
      user.addEventListener("click",function(e){
        e.stopPropagation();
        const r=user.getBoundingClientRect();
        pop.style.left=Math.max(10,Math.min(window.innerWidth-250,r.right-240))+"px";
        pop.style.top=(r.bottom+8)+"px";
        pop.classList.toggle("open");
      });
      pop.addEventListener("click",function(e){
        const b=e.target.closest("[data-go]");
        if(b) window.location.href=b.dataset.go;
      });
      document.addEventListener("click",function(e){
        if(!pop.contains(e.target) && !user.contains(e.target)) pop.classList.remove("open");
      });
    }

    // Cursor tooltips only while navigation is minimized.
    if(rail && !document.getElementById("v6-nav-tip")){
      const tip=document.createElement("div");
      tip.id="v6-nav-tip";
      tip.className="v6-nav-tip";
      document.body.appendChild(tip);
      rail.querySelectorAll(".nav-item.nav-v6").forEach(item=>{
        const show=()=>{
          if(!body.classList.contains("sidebar-collapsed")) return;
          const rect=item.getBoundingClientRect();
          tip.textContent=item.dataset.tooltipTitle || item.getAttribute("aria-label") || "Navigation";
          tip.style.left=(rect.right+9)+"px";
          tip.style.top=(rect.top+rect.height/2)+"px";
          tip.classList.add("open");
        };
        item.addEventListener("mouseenter",show);
        item.addEventListener("mouseleave",()=>tip.classList.remove("open"));
      });
    }

    // Command-style page search.
    if(search && !search.dataset.v6Search){
      search.dataset.v6Search="1";
      const routes=[["/","Dashboard"],["/nodes","Nodes"],["/sensors","Sensors"],["/command-center","Commands"],["/communication","Network"],["/firmware","Firmware & OTA"],["/logs","Logs"],["/system-overview","System Health"],["/system","System"],["/chat","Private Chat"]];
      search.readOnly=true;
      function openSearch(){
        let modal=document.getElementById("v6-search-modal");
        if(!modal){
          modal=document.createElement("div");
          modal.id="v6-search-modal";
          modal.className="v6-search-modal";
          modal.innerHTML='<div class="v6-search-backdrop"></div><div class="v6-search-dialog"><div class="v6-search-head"><span>⌕</span><input placeholder="Search pages"></div><div class="v6-search-list"></div></div>';
          document.body.appendChild(modal);
          modal.querySelector(".v6-search-backdrop").onclick=()=>modal.classList.remove("open");
          modal.querySelector("input").oninput=function(){render(this.value)};
          modal.onclick=function(e){const item=e.target.closest("[data-route]");if(item)location.href=item.dataset.route};
        }
        modal.classList.add("open");
        const input=modal.querySelector("input");
        input.value="";
        render("");
        setTimeout(()=>input.focus(),20);
        function render(q){
          q=(q||"").toLowerCase().trim();
          modal.querySelector(".v6-search-list").innerHTML=routes.filter(r=>!q||r.join(" ").toLowerCase().includes(q)).map(r=>'<button class="v6-search-row" data-route="'+r[0]+'"><b>'+r[1]+'</b><span>'+r[0]+'</span></button>').join("") || '<div class="v6-search-empty">No page found</div>';
        }
      }
      search.addEventListener("focus",openSearch);
      search.addEventListener("click",openSearch);
      document.addEventListener("keydown",function(e){
        if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openSearch()}
        if(e.key==="Escape") document.getElementById("v6-search-modal")?.classList.remove("open");
      });
    }

    // Animate visible dashboard numbers from zero to the current live value.
    if(location.pathname==="/" && !window.matchMedia("(prefers-reduced-motion: reduce)").matches){
      const animateValue=(el)=>{
        if(!el || el.dataset.animated==="1") return;
        const raw=(el.textContent||"").trim();
        const n=parseFloat(raw);
        if(!Number.isFinite(n)) return;
        el.dataset.animated="1";
        const duration=650;
        const start=performance.now();
        const step=(now)=>{
          const p=Math.min(1,(now-start)/duration);
          const eased=1-Math.pow(1-p,3);
          el.textContent=(Math.round(n*eased*100)/100).toString();
          if(p<1) requestAnimationFrame(step);
          else el.textContent=raw;
        };
        requestAnimationFrame(step);
      };
      const observer=new MutationObserver(()=>document.querySelectorAll(".dashboard-metric-value").forEach(animateValue));
      observer.observe(document.getElementById("dashboard-console")||document.body,{subtree:true,childList:true,characterData:true});
    }
  }

  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",initReferenceInteractions,{once:true});
  }else{
    initReferenceInteractions();
  }
})();
