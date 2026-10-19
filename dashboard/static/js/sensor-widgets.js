/* Shared sensor presentation uses existing timestamped telemetry endpoints. */
"use strict";
window.SensorUI = (() => {
 const esc = value => gateway.escape(String(value ?? ""));
 const cfg = p => {try {return typeof p.widget_config === "string" ? JSON.parse(p.widget_config) : (p.widget_config || {});} catch (_) {return {};}};
 const numeric = p => ["FLOAT","DOUBLE","INT","UINT","UINT32"].includes(p.data_type);
 const accents = [["temp","#2563EB"],["press","#0D9488"],["batt.*volt|batt_v","#16A34A"],["rssi","#7C3AED"],["snr","#0891B2"],["humid","#0284C7"]];
 function color(p) {return /^#[0-9a-f]{6}$/i.test(cfg(p).color || "") ? cfg(p).color : (accents.find(([rx]) => new RegExp(rx,"i").test([p.parameter_type,p.parameter_id,p.parameter_name].join(" ")))?.[1] || "#2563EB");}
 const paths = {
  thermometer:'<path d="M9 14.5V5a3 3 0 0 1 6 0v9.5a5 5 0 1 1-6 0Z"/><path d="M12 9v8"/>',
  gauge:'<path d="M4 17a9 9 0 1 1 16 0M12 13l4-5M6 17h12"/>',
  battery:'<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 10v4m-12-6-3 5h5l-3 5"/>',
  signal:'<path d="M4 20v-3m5 3v-7m5 7V9m5 11V4"/>',
  zap:'<path d="m13 2-9 12h7l-1 8 10-13h-8l1-7Z"/>',
  droplet:'<path d="M12 3c-2 4-7 8-7 12a7 7 0 0 0 14 0c0-4-5-8-7-12Z"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2"/>',
  activity:'<path d="M2 12h4l3-8 6 16 3-8h4"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  "map-pin":'<path d="M12 22s8-8 8-13a8 8 0 0 0-16 0c0 5 8 13 8 13Z"/><circle cx="12" cy="9" r="3"/>'
 };
 function icon(p) {
   const text = [p.parameter_type,p.parameter_id].join(" ").toLowerCase();
   const key=cfg(p).icon || (/temp/.test(text)?"thermometer":/press/.test(text)?"gauge":/batt/.test(text)?"battery":/rssi|snr/.test(text)?"signal":"activity");
   return '<svg viewBox="0 0 24 24" aria-hidden="true">'+(paths[key]||paths.activity)+'</svg>';
 }
 function value(p,v=p.value ?? p.text_value) {if(v===null||v===undefined||v==="")return "N/A";return numeric(p)&&Number.isFinite(Number(v))?Number(v).toFixed(Math.max(0,Math.min(8,Number(p.decimal_places ?? 2)))):String(v);}
 function connection(node) {
   if(node?.enabled===false || node?.enabled===0)return {online:false,reason:"Node disabled in Gateway settings."};
   if(!node?.last_seen)return {online:false,reason:"No heartbeat received from this node yet. Check node power and network."};
   const seen=new Date(node.last_seen).getTime();
   if(!Number.isFinite(seen))return {online:false,reason:"Last-seen timestamp is unavailable. Refresh Gateway status."};
   const timeout=node.device_enrolled?Number(node.heartbeat_seconds||30)*3:60;
   const age=Math.max(0,Math.floor((Date.now()-seen)/1000));
   if(age>timeout)return {online:false,reason:"No heartbeat for "+age+" s (timeout "+timeout+" s). Check node power and network."};
   if(!["online","connected","active"].includes(String(node.status).toLowerCase()))return {online:false,reason:"Gateway reports this node offline. Check node power and network."};
   return {online:true,reason:"Heartbeat received within "+timeout+" s."};
 }
 function status(p,node) {
   if(node && !connection(node).online)return "Offline";
   if(!p.timestamp)return "Unavailable";
   if(Date.now()-new Date(p.timestamp).getTime()>Number(cfg(p).stale_timeout||10)*1000)return "Stale";
   if(["HIGH","LOW","SENSOR_ERROR"].includes(p.alarm_status))return p.alarm_status.replace("_"," ");
   if(p.quality && p.quality!=="GOOD")return p.quality;
   const c=cfg(p), n=Number(p.value);
   if(numeric(p)&&((c.warning_low!=null&&n<c.warning_low)||(c.warning_high!=null&&n>c.warning_high)))return "Warning";
   return "Live";
 }
 function stamp(t) {return t && Number.isFinite(new Date(t).getTime())?new Date(t).toLocaleString():"No reading received";}
 function chart(p,rows,large=false) {
   const data=(rows||[]).filter(x=>x.timestamp&&Number.isFinite(new Date(x.timestamp).getTime())&&x.value!==null&&x.value!==""&&Number.isFinite(Number(x.value))).sort((a,b)=>new Date(a.timestamp)-new Date(b.timestamp));
   if(!numeric(p)){
     const events=(rows||[]).filter(x=>x.timestamp).sort((a,b)=>new Date(a.timestamp)-new Date(b.timestamp));
     if(!events.length)return '<div class="sensor-history-empty">No state or position readings in this time range.</div>';
     if(cfg(p).widget_type==="gps")return '<div class="sensor-history-empty">Position history · '+events.length+' recorded locations. Expand Historical readings to inspect coordinates.</div>';
     const transitions=events.filter((x,i)=>i===0||String(x.value??x.text_value)!==String(events[i-1].value??events[i-1].text_value));
     return '<div class="sensor-state-history"><small>Recorded state transitions</small><div class="sensor-state-timeline">'+transitions.map((x,i)=>'<span class="'+(i%2?'alternate':'')+'" title="'+esc(stamp(x.timestamp)+' · '+value(p,x.value??x.text_value))+'">'+esc(value(p,x.value??x.text_value))+'</span>').join("")+'</div><small>'+transitions.length+' recorded transitions · '+esc(stamp(events[0].timestamp))+' — '+esc(stamp(events.at(-1).timestamp))+'</small></div>';
   }
   if(!data.length)return '<div class="sensor-history-empty">No historical readings in this time range.</div>';
   const w=760,h=large?300:155,left=large?98:20,right=24,top=large?40:16,bottom=large?58:16;
   const vals=data.map(x=>Number(x.value));let lo=Math.min(...vals),hi=Math.max(...vals),padding=(hi-lo)*.1||Math.max(1,Math.abs(hi)*.05);lo-=padding;hi+=padding;
   const start=new Date(data[0].timestamp).getTime(),end=new Date(data.at(-1).timestamp).getTime();
   const x=t=>left+(end===start?.5:(new Date(t).getTime()-start)/(end-start))*(w-left-right);
   const y=v=>h-bottom-(Number(v)-lo)/(hi-lo)*(h-top-bottom);
   const max=large?500:120,stride=Math.max(1,Math.ceil(data.length/max)),draw=data.filter((_,i)=>i%stride===0||i===data.length-1);
   const line=draw.map((d,i)=>(i?"L":"M")+x(d.timestamp).toFixed(2)+","+y(d.value).toFixed(2)).join(" ");
   let grid="",labels="";
   if(large){
    for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4,yy=y(v);grid+='<line x1="'+left+'" x2="'+(w-right)+'" y1="'+yy+'" y2="'+yy+'"/>';labels+='<text x="'+(left-10)+'" y="'+(yy+4)+'" text-anchor="end">'+esc(value(p,v))+'</text>';}
    for(let i=0;i<4;i++){const xx=left+(w-left-right)*i/3,t=start+(end-start)*i/3;grid+='<line x1="'+xx+'" x2="'+xx+'" y1="'+top+'" y2="'+(h-bottom)+'"/>';labels+='<text x="'+xx+'" y="'+(h-bottom+24)+'" text-anchor="middle">'+esc(new Date(t).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}))+'</text>';}
    labels+='<text x="'+left+'" y="17">'+esc((p.parameter_name||p.parameter_id)+(p.unit?" ("+p.unit+")":""))+'</text><text x="'+(w/2)+'" y="'+(h-5)+'" text-anchor="middle">Time · '+esc(new Date(start).toLocaleDateString())+'</text>';
   }
   return '<svg class="sensor-history-chart" viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+esc((p.parameter_name||p.parameter_id)+' history, '+(p.unit||'value')+' versus time')+'"><g class="sensor-grid">'+grid+'</g><path class="sensor-area" d="'+line+'L'+x(draw.at(-1).timestamp)+','+(h-bottom)+'L'+x(draw[0].timestamp)+','+(h-bottom)+'Z"/><path class="sensor-line" d="'+line+'"/>'+draw.map(d=>'<circle cx="'+x(d.timestamp)+'" cy="'+y(d.value)+'" r="'+(large?3:2)+'"><title>'+esc(stamp(d.timestamp)+' · '+value(p,d.value)+' '+(p.unit||""))+'</title></circle>').join("")+'<g class="sensor-axis">'+labels+'</g></svg>';
 }
 function card(p,node,rows){
   const label=status(p,node);
   return '<article class="dashboard-sensor-card sensor-live-card" data-id="'+esc(p.parameter_id)+'" style="--sensor-accent:'+color(p)+'"><header><span class="sensor-type-icon">'+icon(p)+'</span><div><h3>'+esc(p.parameter_name||p.parameter_id)+'</h3><small>'+esc(p.sensor_id||p.parameter_id)+'</small></div><span class="sensor-freshness '+(label==="Live"?"is-live":label==="Offline"?"is-offline":label==="Stale"?"is-stale":"")+'">'+esc(label)+'</span></header><div class="sensor-current"><strong>'+esc(value(p))+'</strong><span>'+esc(p.unit||"")+'</span></div><p class="sensor-updated">'+esc(p.timestamp?(label==="Offline"?"Last stored reading ":p.timestamp_basis==="GATEWAY_RECEIPT"?"Gateway received ":"Sample time ")+stamp(p.timestamp):"Waiting for telemetry")+'</p><button type="button" class="sensor-chart-trigger" aria-label="Expand '+esc(p.parameter_name||p.parameter_id)+' graph">'+chart(p,rows)+'<span class="sensor-chart-foot"><span>History · 1 hour</span><span>Click graph to expand ↗</span></span></button><button type="button" class="sensor-remove-widget" data-sensor-remove title="Remove widget from dashboard" aria-label="Remove widget from dashboard">Remove widget</button></article>';
 }
 let active=null;
 async function open(node,parameter,getParameters){
   active?.close();
   const overlay=document.createElement("div");overlay.className="sensor-detail-overlay modal-overlay";
   const origin=document.activeElement,oldOverflow=document.body.style.overflow;
   let selected=parameter.parameter_id,hours=1,requestId=0,stopped=false;
   overlay.innerHTML='<section class="sensor-detail-dialog" role="dialog" aria-modal="true" aria-label="Sensor details"><header><div><h2>Sensor details</h2><p>'+esc((node.name||node.node_id)+" · "+node.node_id)+'</p></div><button type="button" class="btn" data-close-telemetry aria-label="Close sensor details">×</button></header><label class="sensor-select-label">Sensor<select class="input" id="sensor-detail-select"></select></label><div id="sensor-detail-body"></div></section>';
   function close(){if(stopped)return;stopped=true;requestId++;clearInterval(timer);overlay.remove();document.body.style.overflow=oldOverflow;document.removeEventListener("keydown",keys);active=null;if(origin?.isConnected)origin.focus();}
   function keys(e){
    if(e.key==="Escape"){e.preventDefault();close();}
    if(e.key==="Tab"){const f=[...overlay.querySelectorAll('button,select,summary,[tabindex="0"]')].filter(x=>x.getClientRects().length),first=f[0],last=f.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}
   }
   overlay.addEventListener("click",e=>{if(e.target===overlay||e.target.closest("[data-close-telemetry]"))close();const range=e.target.closest("[data-sensor-hours]");if(range){hours=Number(range.dataset.sensorHours);render();}});
   const select=overlay.querySelector("select");
   for(const p of getParameters())select.add(new Option((p.parameter_name||p.parameter_id)+(p.enabled===false?" (disabled)":""),p.parameter_id));
   select.value=selected;select.onchange=()=>{selected=select.value;render();};
   async function render(){
    const id=++requestId,p=getParameters().find(x=>x.parameter_id===selected),box=overlay.querySelector("#sensor-detail-body");if(!p){box.textContent="Sensor is no longer configured.";return;}
    box.style.setProperty("--sensor-accent",color(p));
    box.innerHTML='<p role="status">Loading historical readings…</p>';
    try {
     const response=await fetch('/api/nodes/'+encodeURIComponent(node.node_id)+'/telemetry/'+encodeURIComponent(selected)+'?hours='+hours);
     const data=await response.json();if(!response.ok)throw Error(data.error||"History unavailable");if(stopped||id!==requestId)return;
     const rows=data.data||[],stats=data.statistics||{},label=status(p,node);
     const ranges=[[1,"1 hour"],[6,"6 hours"],[24,"24 hours"],[168,"7 days"]].map(([n,t])=>'<button class="btn" type="button" data-sensor-hours="'+n+'" aria-pressed="'+(hours===n)+'">'+t+'</button>').join("");
     box.innerHTML='<div class="sensor-selected-summary"><span class="sensor-type-icon">'+icon(p)+'</span><div><h3>'+esc(p.parameter_name||p.parameter_id)+'</h3><small>'+esc(p.sensor_id||p.parameter_id)+'</small><p>'+esc(p.description||"")+'</p></div><div class="sensor-current"><strong>'+esc(value(p))+'</strong><span>'+esc(p.unit||"")+'</span></div><span class="sensor-freshness '+(label==="Live"?"is-live":label==="Offline"?"is-offline":label==="Stale"?"is-stale":"")+'">'+esc(label)+'</span></div><div class="sensor-trend-head"><h3>Historical trend</h3><div class="sensor-range-controls">'+ranges+'</div></div>'+chart(p,rows,true)+(data.truncated?'<p>Chart and table show the latest 10,000 records. Statistics cover the full interval.</p>':'')+(numeric(p)?'<div class="sensor-statistics">'+[["Minimum","minimum"],["Average","average"],["Maximum","maximum"]].map(([title,key])=>'<div><small>'+title+'</small><strong>'+esc(stats[key]==null?"N/A":value(p,stats[key])+" "+(p.unit||""))+'</strong></div>').join("")+'</div>':'<p>'+rows.length+' recorded state or position updates in this interval.</p>')+'<details class="sensor-readings"><summary>Historical readings ('+rows.length+')</summary><div class="table-wrap"><table><thead><tr><th>Timestamp</th><th>Value'+(p.unit?' ('+esc(p.unit)+')':'')+'</th><th>Status</th></tr></thead><tbody>'+[...rows].reverse().slice(0,1000).map(x=>'<tr><td>'+esc(stamp(x.timestamp))+'</td><td>'+esc(value(p,x.value??x.text_value))+' '+esc(p.unit||"")+'</td><td>'+esc(x.status||x.quality||"N/A")+'</td></tr>').join("")+'</tbody></table></div>'+(!rows.length?'<p>No recorded readings in this time range.</p>':rows.length>1000?'<p>Latest 1,000 rows displayed.</p>':'')+'</details><footer class="sensor-last-update">Last update · '+esc(stamp(p.timestamp))+' · '+esc(label)+'</footer>';
    }catch(error){if(!stopped&&id===requestId)box.textContent=error.message;}
   }
   const timer=setInterval(()=>{if(!document.hidden&&!overlay.querySelector("details[open]")&&!overlay.querySelector("#sensor-detail-body").contains(document.activeElement)&&document.activeElement!==select)render();},10000);
   active={close};document.body.append(overlay);document.body.style.overflow="hidden";document.addEventListener("keydown",keys);overlay.querySelector("button").focus();render();
 }
 async function chooseWidgets(nodes, after) {
   const overlay=document.createElement("div");overlay.className="sensor-detail-overlay modal-overlay";
   overlay.innerHTML='<section class="sensor-detail-dialog" role="dialog" aria-modal="true" aria-label="Add Widget"><header><h2>Add Widget</h2><button class="btn" type="button" data-close-telemetry aria-label="Close widget catalog">×</button></header><div class="management-toolbar"><input class="input" type="search" placeholder="Search configured sensors" aria-label="Search configured sensors"><select class="input" aria-label="Filter category"><option value="">All categories</option><option>core</option><option>environment</option><option>network</option><option>custom</option></select></div><p role="status"></p><div class="sensor-widget-options"></div><a class="btn" href="/sensors#sensor-management">Configure a new sensor</a></section>';
   const origin=document.activeElement,oldOverflow=document.body.style.overflow;
   const close=()=>{overlay.remove();document.body.style.overflow=oldOverflow;document.removeEventListener("keydown",keys);if(origin?.isConnected)origin.focus();};
   const keys=e=>{if(e.key==="Escape")close();};
   overlay.onclick=e=>{if(e.target===overlay||e.target.closest("[data-close-telemetry]"))close();};
   document.body.append(overlay);document.body.style.overflow="hidden";document.addEventListener("keydown",keys);
   const message=overlay.querySelector('[role="status"]'),list=overlay.querySelector(".sensor-widget-options"),search=overlay.querySelector("input"),category=overlay.querySelector("select");
   try{
     const groups=await Promise.all(nodes.map(async node=>{const r=await fetch("/api/nodes/"+encodeURIComponent(node.node_id)+"/parameters");if(!r.ok)throw Error("Unable to load sensor definitions.");const d=await r.json();return (d.parameters||[]).map(p=>({...p,node_id:node.node_id,node_name:node.name}));}));
     const items=groups.flat();
     function render(){
       list.replaceChildren();
       const selected=items.filter(p=>p.enabled&&!p.display_enabled&&(!search.value||[p.parameter_name,p.parameter_id,p.node_name].join(" ").toLowerCase().includes(search.value.toLowerCase()))&&(!category.value||cfg(p).category===category.value));
       for(const p of selected){
         const button=document.createElement("button");button.className="btn";button.type="button";button.textContent=(p.parameter_name||p.parameter_id)+" · "+(p.node_name||p.node_id)+" · Add";
         button.onclick=async()=>{button.disabled=true;try{const r=await fetch("/api/nodes/"+encodeURIComponent(p.node_id)+"/parameters/"+encodeURIComponent(p.parameter_id),{method:"PUT",headers:{"Content-Type":"application/json","X-CSRF-Token":document.querySelector('meta[name="sensor-csrf"]')?.content||""},body:JSON.stringify({display_enabled:true})});const d=await r.json();if(!r.ok)throw Error(d.error||"Unable to add widget.");p.display_enabled=true;await after();render();message.textContent="Widget added.";}catch(e){message.textContent=e.message;button.disabled=false;}};
         list.append(button);
       }
       if(!selected.length)list.textContent="No enabled hidden sensors match. Configure or enable a sensor in Sensor Management.";
     }
     search.oninput=render;category.onchange=render;render();search.focus();
   }catch(e){message.textContent=e.message;}
 }
 return {config:cfg,color,icon,value,status,connection,chart,card,open,chooseWidgets};
})();
