"use strict";
(function(){
  const ready=fn=>document.readyState==="loading"?document.addEventListener("DOMContentLoaded",fn,{once:true}):fn();
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
  const reduce=()=>window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function title(){const t=(($("#page-title")?.textContent||"Dashboard").trim()||"Dashboard");document.title=t+" — SELVARITHIK'S A&D LoRa Gateway";}
  function sidebar(){
    const b=$("#sidebar-collapse-btn"),rail=$(".sidebar9-inspired"); if(!b||!rail)return;
    let c=false; try{c=localStorage.getItem("selvarithik-sidebar-collapsed")==="1";}catch(_){}
    document.body.classList.toggle("sidebar-collapsed",c);
    const sync=()=>{const x=document.body.classList.contains("sidebar-collapsed");b.title=x?"Expand navigation":"Minimize navigation";b.setAttribute("aria-label",b.title);b.setAttribute("aria-expanded",String(!x));};
    sync();
    b.addEventListener("click",()=>setTimeout(sync,0));
    if(reduce())return;
    rail.addEventListener("pointermove",e=>{const r=rail.getBoundingClientRect();rail.style.setProperty("--rail-x",(((e.clientX-r.left)/r.width)*100)+"%");rail.style.setProperty("--rail-y",(((e.clientY-r.top)/r.height)*100)+"%");});
    rail.addEventListener("pointerleave",()=>{rail.style.setProperty("--rail-x","50%");rail.style.setProperty("--rail-y","50%");});
  }
  function tips(){
    const rail=$(".sidebar9-inspired"); if(!rail)return;
    let tip=$("#reference-nav-tip"); if(!tip){tip=document.createElement("div");tip.id="reference-nav-tip";tip.className="reference-nav-tip";document.body.appendChild(tip);}
    $$(".nav-item.nav-v6",rail).forEach(item=>{
      const show=()=>{if(!document.body.classList.contains("sidebar-collapsed"))return;const r=item.getBoundingClientRect();tip.textContent=item.dataset.tooltipTitle||item.getAttribute("aria-label")||"Navigation";tip.style.left=(r.right+10)+"px";tip.style.top=(r.top+r.height/2)+"px";tip.classList.add("show");};
      item.addEventListener("mouseenter",show); item.addEventListener("focus",show);
      item.addEventListener("mouseleave",()=>tip.classList.remove("show")); item.addEventListener("blur",()=>tip.classList.remove("show"));
    });
  }
  function user(){
    const u=$(".gateway-user-static"); if(!u||u.dataset.referenceUser)return; u.dataset.referenceUser="1";
    const p=document.createElement("div");p.className="reference-user-popup";
    p.innerHTML='<div class="reference-user-head"><b>GW</b><span><strong>Gateway</strong><small>Local access</small></span></div><button type="button" data-go="/system">Settings</button><button type="button" data-go="/logout">Log out</button>';
    document.body.appendChild(p);
    u.addEventListener("click",e=>{e.stopPropagation();const r=u.getBoundingClientRect(),w=220;p.style.left=Math.max(10,Math.min(innerWidth-w-10,r.right-w))+"px";p.style.top=(r.bottom+8)+"px";p.classList.toggle("open");});
    p.addEventListener("click",e=>{const b=e.target.closest("[data-go]");if(b)location.href=b.dataset.go;});
    document.addEventListener("click",e=>{if(!p.contains(e.target)&&!u.contains(e.target))p.classList.remove("open");});
  }
  function search(){
    const s=$("#global-nav-search"); if(!s||s.dataset.referenceSearch)return; s.dataset.referenceSearch="1";
    const routes=[["/","Dashboard"],["/nodes","Nodes"],["/sensors","Sensors"],["/command-center","Commands"],["/communication","Network"],["/firmware","Firmware & OTA"],["/logs","Logs"],["/system-overview","System Health"],["/system","System"],["/chat","Private Chat"]];
    let modal=null;
    const render=q=>{if(!modal)return;const x=String(q||"").toLowerCase().trim(),rows=routes.filter(r=>!x||(r[0]+" "+r[1]).toLowerCase().includes(x));$(".reference-search-list",modal).innerHTML=rows.map(r=>'<button class="reference-search-row" data-route="'+r[0]+'"><span><b>'+r[1]+'</b><small>'+r[0]+'</small></span><em>→</em></button>').join("")||'<div class="reference-search-empty">No gateway page found.</div>';};
    const open=()=>{if(!modal){modal=document.createElement("div");modal.className="reference-search";modal.innerHTML='<div class="reference-search-bg"></div><div class="reference-search-box" role="dialog" aria-modal="true"><div class="reference-search-head"><span>⌕</span><input type="search" placeholder="Search gateway pages…"><kbd>ESC</kbd></div><div class="reference-search-list"></div></div>';document.body.appendChild(modal);$(".reference-search-bg",modal).onclick=()=>modal.classList.remove("open");$(".reference-search-box",modal).onclick=e=>{const i=e.target.closest("[data-route]");if(i)location.href=i.dataset.route;};$(".reference-search-head input",modal).oninput=e=>render(e.target.value);}modal.classList.add("open");const i=$(".reference-search-head input",modal);i.value="";render("");setTimeout(()=>i.focus(),20);};
    s.readOnly=true;s.addEventListener("click",open);
    document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();open();}if(e.key==="Escape"&&modal)modal.classList.remove("open");});
  }
  function cards(){
    if(location.pathname!=="/"||reduce())return;
    $$(".dashboard-metric,.dashboard-visual-card,.dashboard-sensor-card,.dashboard-graph-card").forEach(card=>{
      card.addEventListener("pointermove",e=>{const r=card.getBoundingClientRect(),x=((e.clientX-r.left)/r.width-.5)*2,y=((e.clientY-r.top)/r.height-.5)*2;card.style.setProperty("--rx",(-y*1.6)+"deg");card.style.setProperty("--ry",(x*1.6)+"deg");});
      card.addEventListener("pointerleave",()=>{card.style.setProperty("--rx","0deg");card.style.setProperty("--ry","0deg");});
    });
  }
  function ripple(){
    if(reduce())return;
    document.addEventListener("pointerdown",e=>{const b=e.target.closest(".dashboard-action,.dashboard-mini-tool,.sidebar9-action,.sidebar-collapse-btn");if(!b||b.disabled)return;const r=b.getBoundingClientRect(),dot=document.createElement("i");dot.className="reference-ripple";dot.style.left=(e.clientX-r.left)+"px";dot.style.top=(e.clientY-r.top)+"px";b.appendChild(dot);setTimeout(()=>dot.remove(),600);});
  }
  ready(()=>{document.body.classList.add("ui-reference-final");title();sidebar();tips();user();search();cards();ripple();});
})();