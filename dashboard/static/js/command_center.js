/* Node conversations adapt the existing command APIs and shared Socket.IO client. */
"use strict";
document.addEventListener("DOMContentLoaded", () => {
 const root=document.getElementById("command-chat");if(!root)return;
 const $=id=>document.getElementById(id),esc=v=>gateway.escape(String(v??""));
 const nodesList=$("node-list-container"),conversation=$("command-conversation"),history=$("history-list-container"),notice=$("command-notice");
 const terminal=new Set(["COMPLETED","FAILED","TIMEOUT","CANCELLED"]);
 const caches=new Map(),socket=gateway.socket;
 let nodes=[],selected=null,nodeFilter="all",sending=false,actionBusy=new Set(),timer=null,stopped=false,pollBusy=false;
 const cache=id=>{if(!caches.has(id))caches.set(id,{commands:new Map(),events:new Map(),offset:0,more:true,busy:false,loaded:false,eventRequests:new Set(),forceBottom:false});return caches.get(id);};
 const time=v=>v?gateway.time(v):"—";
 const online=n=>n&&n.enabled!==false&&["online","connected"].includes(String(n.status).toLowerCase())&&n.last_seen&&Date.now()-new Date(n.last_seen).getTime()<60000;
 const current=()=>nodes.find(n=>n.node_id===selected);
 const entries=()=>selected?[...cache(selected).commands.values()]:[];
 const active=()=>entries().filter(c=>!terminal.has(c.state)).sort((a,b)=>new Date(b.created_at)-new Date(a.created_at))[0];
 const nearBottom=()=>conversation.scrollHeight-conversation.clientHeight-conversation.scrollTop<90;
 function feedback(text,error=true){notice.textContent=text;notice.style.color=error?"var(--m-red)":"var(--m-muted)";}
 function safe(value){
  if(Array.isArray(value))return value.map(safe);
  if(value&&typeof value==="object")return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,/password|secret|token|credential/i.test(k)?"[redacted]":safe(v)]));
  return value;
 }
 function json(value){return JSON.stringify(safe(value),null,2)??"";}
 function chip(state){return '<span class="command-state '+esc(String(state||"unknown").toLowerCase())+'">'+esc(String(state||"Unknown").replaceAll("_"," "))+'</span>';}
 async function loadNodes(){
  try{
   const data=await gateway.get("/api/nodes");if(stopped)return;
   nodes=Array.isArray(data)?data:data.nodes||[];
   if(selected&&!nodes.some(n=>n.node_id===selected))selected=null;
   renderNodes();renderHeader();
   if(!selected&&!nodes.length)render();
   if(!selected&&nodes.length&&matchMedia("(min-width:701px)").matches)selectNode(nodes[0].node_id);
  }catch(e){feedback("Unable to load nodes: "+e.message);}
 }
 function renderNodes(){
  const q=$("node-search-input").value.toLowerCase().trim();
  $("node-count-badge").textContent=nodes.length+" registered";
  const filtered=nodes.filter(n=>(!q||[n.node_id,n.name].join(" ").toLowerCase().includes(q))&&(nodeFilter==="all"||nodeFilter==="online"&&online(n)||nodeFilter==="offline"&&!online(n)));
  const html=filtered.map(n=>'<button type="button" class="command-node-item" data-id="'+esc(n.node_id)+'" data-node-id="'+esc(n.node_id)+'" aria-pressed="'+(selected===n.node_id)+'"><span class="command-node-avatar" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4"/></svg></span><span class="command-node-info"><strong>'+esc(n.name||n.node_id)+'</strong><small>'+esc(n.node_id)+'</small><span class="command-node-state '+(online(n)?"online":"")+'"><i></i>'+ (online(n)?"Online":"Offline")+'</span><small>FW '+esc(n.firmware_version||"Unknown")+' · Seen '+esc(time(n.last_seen))+'</small></span></button>').join("");
  gateway.patchHtml(nodesList,html||'<p class="command-empty">No registered nodes match this filter.</p>');
 }
 function renderHeader(){
  const n=current();
  $("banner-node-name").textContent=n?.name||n?.node_id||"Select a node";
  $("banner-node-details").textContent=n?[n.node_id,n.mcu_family,n.communication_type,n.firmware_version?"FW "+n.firmware_version:"FW unknown"].filter(Boolean).join(" · "):"No node selected";
  $("banner-connection-badge").textContent=n?(online(n)?"ONLINE":"OFFLINE")+" · Last seen: "+time(n.last_seen):"";
  $("banner-connection-badge").style.color=online(n)?"var(--m-green)":"var(--m-muted)";
  renderComposer();
 }
 function renderComposer(){
  const n=current(),running=active();
  $("btn-send-command").disabled=!n||n.enabled===false||sending||Boolean(running)||!cache(selected).loaded;
  $("btn-send-command").querySelector("span").textContent=sending?"Sending…":"Send";
  $("command-active-status").textContent=running?running.command_id+" · "+running.state.replaceAll("_"," "):n?(!online(n)?"Node offline · dispatch creates a queued command only after confirmation.":"No active command"):"Select a registered node";
 }
 function selectNode(id){
  selected=id;root.classList.add("conversation-open");feedback("",false);
  renderNodes();renderHeader();render(true);loadHistory(id,false,true);
 }
 async function loadEvents(cmd,force=false){
  const c=cache(cmd.node_id),old=c.events.get(cmd.command_id);
  const fingerprint=[cmd.state,cmd.updated_at,cmd.retry_count,cmd.ack_at,cmd.response_at].join("|");
  if(c.eventRequests.has(cmd.command_id)||(!force&&old?.fingerprint===fingerprint))return;
  c.eventRequests.add(cmd.command_id);
  try{
   const data=await gateway.get("/api/commands/"+encodeURIComponent(cmd.command_id)+"/events");
   if(stopped)return;
   const unique=new Map((data.events||[]).map(e=>[e.event_id||e.id,e]));
   c.events.set(cmd.command_id,{fingerprint,items:[...unique.values()]});
   if(selected===cmd.node_id)render();
  }catch(e){if(selected===cmd.node_id)feedback("Audit events unavailable: "+e.message);}
  finally{
   c.eventRequests.delete(cmd.command_id);
   const latest=c.commands.get(cmd.command_id),stored=c.events.get(cmd.command_id);
   if(latest&&stored&&stored.fingerprint!==[latest.state,latest.updated_at,latest.retry_count,latest.ack_at,latest.response_at].join("|"))loadEvents(latest);
  }
 }
 async function loadHistory(id,older=false,forceBottom=false){
  const c=cache(id);if(c.busy)return;c.busy=true;
  let succeeded=false;
  const oldHeight=conversation.scrollHeight,oldTop=conversation.scrollTop;
  try{
   const data=await gateway.get("/api/commands?node_id="+encodeURIComponent(id)+"&limit=30&offset="+(older?c.offset:0));
   if(stopped)return;
   const commands=data.commands||[];
   for(const cmd of commands){
    const previous=c.commands.get(cmd.command_id);
    if(previous?.updated_at&&cmd.updated_at&&new Date(previous.updated_at)>new Date(cmd.updated_at))continue;
    c.commands.set(cmd.command_id,{...previous,...cmd});
   }
   if(older)c.offset+=commands.length;else if(!c.loaded)c.offset=commands.length;
   if(older||!c.loaded)c.more=commands.length===30;
   c.loaded=true;
   succeeded=true;
   if(selected===id){render(forceBottom);if(older)conversation.scrollTop=oldTop+conversation.scrollHeight-oldHeight;renderComposer();}
   await Promise.allSettled(commands.map(cmd=>loadEvents(cmd)));
  }catch(e){if(selected===id)feedback("Unable to load command history: "+e.message);}
  finally{
   c.busy=false;
   if(selected===id){
    $("command-older").disabled=false;
    if(succeeded&&c.more&&conversation.scrollTop<12)queueMicrotask(()=>loadHistory(id,true));
   }
  }
 }
 function render(forceBottom=false){
  if(!selected){history.innerHTML='<p class="command-empty">Select a node to view commands and responses.</p>';return;}
  const c=cache(selected),follow=forceBottom||nearBottom(),top=conversation.scrollTop;
  const anchor=[...history.querySelectorAll("[data-id]")].find(e=>e.getBoundingClientRect().bottom>conversation.getBoundingClientRect().top);
  const anchorId=anchor?.dataset.id,anchorY=anchor?.getBoundingClientRect().top;
  const opened=new Set([...history.querySelectorAll("details[open]")].map(e=>e.dataset.detail));
  const filter=$("history-filter-select").value;
  const commands=[...c.commands.values()].filter(cmd=>filter==="ALL"||filter==="ACTIVE"&&!terminal.has(cmd.state)||cmd.state===filter);
  const rows=[];
  for(const cmd of commands){
   rows.push({kind:"command",key:cmd.command_id,at:cmd.created_at,cmd});
   if(cmd.response_at)rows.push({kind:"response",key:cmd.command_id+"-response",at:cmd.response_at,cmd});
   for(const event of c.events.get(cmd.command_id)?.items||[])rows.push({kind:"event",key:event.event_id||String(event.id),at:event.created_at,cmd,event});
  }
  rows.sort((a,b)=>new Date(a.at||0)-new Date(b.at||0)||a.key.localeCompare(b.key));
  let lastDay="",html="";
  for(const row of rows){
   const cmd=row.cmd,cid=esc(cmd.command_id);
   const day=row.at?new Date(row.at).toLocaleDateString():"Unknown date";
   if(day!==lastDay){html+='<div class="command-day">'+esc(day)+'</div>';lastDay=day;}
   if(row.kind==="event"){
    const e=row.event;html+='<div class="command-system" data-id="'+esc(row.key)+'" data-command-event="'+esc(row.key)+'"><time>'+esc(time(e.created_at))+'</time>'+chip(e.state)+' · '+esc(e.event_type)+' · <code>'+cid+'</code>'+ (e.error?' · '+esc(e.error):'')+'</div>';continue;
   }
   if(row.kind==="response"){
    const elapsed=cmd.sent_at&&cmd.response_at?new Date(cmd.response_at)-new Date(cmd.sent_at):null;
    html+='<article class="command-message incoming" data-id="'+esc(row.key)+'" data-response-command="'+cid+'"><div class="command-bubble"><div class="command-bubble-head"><span>DEVICE RESPONSE</span>'+chip(cmd.state)+'</div><h3>'+esc(cmd.command_type)+'</h3><code>'+cid+'</code><dl><div><dt>ACK status</dt><dd>'+esc(cmd.ack_status||(cmd.ack_at?"Received":"Not recorded"))+'</dd></div><div><dt>Response status</dt><dd>'+esc(cmd.result?.status||cmd.state)+'</dd></div>'+(elapsed!==null&&elapsed>=0?'<div><dt>Response duration</dt><dd>'+esc((elapsed/1000).toFixed(3))+' s</dd></div>':'')+'</dl><details data-detail="'+cid+'-response" '+(opened.has(cmd.command_id+"-response")?"open":"")+'><summary>Response payload</summary><pre>'+esc(cmd.result==null?"No response payload recorded.":json(cmd.result))+'</pre></details><div class="command-message-actions"><button class="btn" type="button" data-copy="'+cid+'" '+(cmd.result==null?"disabled":"")+'>Copy JSON</button></div>'+(cmd.error?'<p class="command-message-error">'+esc(cmd.error)+'</p>':'')+'</div><time>'+esc(time(cmd.response_at))+'</time></article>';continue;
   }
   const isTerminal=terminal.has(cmd.state),retry=["FAILED","TIMEOUT"].includes(cmd.state)&&Number(cmd.retry_count)<Number(cmd.max_retries);
   html+='<article class="command-message outgoing" data-id="'+cid+'" data-command-id="'+cid+'"><div class="command-bubble"><div class="command-bubble-head"><span>GATEWAY COMMAND</span>'+chip(cmd.state)+'</div><h3>'+esc(cmd.command_type)+'</h3><code>'+cid+'</code><dl>'+[["Target",cmd.node_id],["Priority",cmd.priority],["Timeout",cmd.timeout_seconds+" s"],["Retries",cmd.retry_count+" / "+cmd.max_retries],["Dispatch",cmd.sent_at?"Sent "+time(cmd.sent_at):"Not yet sent"],["ACK",cmd.ack_status||(cmd.ack_at?"Received":"Not recorded")],["Execution",cmd.state],["Created",time(cmd.created_at)]].map(([k,v])=>'<div><dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd></div>').join("")+'</dl><details data-detail="'+cid+'-payload" '+(opened.has(cmd.command_id+"-payload")?"open":"")+'><summary>Configured parameters</summary><pre>'+esc(json(cmd.payload||{}))+'</pre></details>'+(cmd.error?'<p class="command-message-error">'+esc(cmd.error)+'</p>':'')+'<div class="command-message-actions">'+(!isTerminal?'<button class="btn" type="button" data-action="cancel" data-command="'+cid+'" '+(actionBusy.has(cmd.command_id)?"disabled":"")+'>Cancel</button>':'')+(retry?'<button class="btn" type="button" data-action="retry" data-command="'+cid+'" '+(actionBusy.has(cmd.command_id)||Boolean(active())?"disabled":"")+'>Retry</button>':'')+'</div></div><time>'+esc(time(cmd.sent_at||cmd.created_at))+'</time></article>';
  }
  gateway.patchHtml(history,html||'<p class="command-empty">'+(c.loaded?"No command history for this filter.":"Loading command history…")+'</p>');
  $("command-older").hidden=!c.more||!c.loaded;
  if(follow)conversation.scrollTop=conversation.scrollHeight;
  else{
   conversation.scrollTop=top;
   const retained=[...history.querySelectorAll("[data-id]")].find(e=>e.dataset.id===anchorId);
   if(retained&&anchorY!=null)conversation.scrollTop+=retained.getBoundingClientRect().top-anchorY;
  }
  renderComposer();
 }
 function merge(cmd){
  if(!cmd?.node_id||!cmd.command_id)return;
  const c=cache(cmd.node_id);
  const previous=c.commands.get(cmd.command_id);
  if(previous?.updated_at&&cmd.updated_at&&new Date(previous.updated_at)>new Date(cmd.updated_at))return;
  c.commands.set(cmd.command_id,{...previous,...cmd});
  if(selected===cmd.node_id){render();renderComposer();}
  loadEvents(c.commands.get(cmd.command_id));
 }
 function switchType(){
  const type=$("cmd-type-select").value;
  root.querySelectorAll(".param-pane").forEach(pane=>pane.classList.toggle("active",pane.id==="pane-"+type));
  $("command-quick-input").hidden=type!=="PING";
  if(type==="PING")$("command-quick-input").value=$("param-ping-msg").value;
 }
 function integer(id,min,max){
  const input=$(id),value=Number(input.value);
  if(!Number.isInteger(value)||value<min||value>max)throw Error(input.labels?.[0]?.textContent+" must be an integer between "+min+" and "+max+".");
  return value;
 }
 async function send(){
  if(sending||active())return;
  const node=current();if(!node||node.enabled===false||!cache(selected).loaded)return;
  const type=$("cmd-type-select").value;let commandType=type,payload={};
  try{
   const priority=integer("cmd-priority-select",1,10),timeout=integer("cmd-timeout-input",1,3600),retries=integer("cmd-retries-input",0,10);
   if(type==="PING")payload={echo:$("command-quick-input").value.trim()||$("param-ping-msg").value.trim()||"PING"};
   if(type==="WIFI_SCAN")payload={band:$("param-scan-band").value,limit:integer("param-scan-limit",1,50)};
   if(type==="WIFI_CONNECT"){const ssid=$("param-wifi-ssid").value.trim();if(!ssid)throw Error("Wi-Fi SSID is required.");payload={ssid,password:$("param-wifi-pass").value,save:$("param-wifi-save").value==="true"};}
   if(type==="RESTART")payload={delay_seconds:integer("param-reboot-delay",0,60),reason:$("param-reboot-reason").value.trim()||"Operator reboot"};
   if(type==="GET_CONFIG")payload={section:$("param-config-section").value.trim()||"all"};
   if(type==="SET_INTERVAL")payload={interval_ms:integer("param-interval-ms",500,3600000)};
   if(type==="CUSTOM"){commandType=$("param-custom-name").value.trim();if(!/^[A-Za-z0-9_.-]{1,64}$/.test(commandType))throw Error("Enter a valid custom command name.");payload=JSON.parse($("param-custom-json").value.trim()||"{}");if(!payload||Array.isArray(payload)||typeof payload!=="object")throw Error("Custom payload must be a JSON object.");}
   if(!online(node)&&!confirm("This node is offline. The existing backend will create a QUEUED command; delivery is not confirmed. Continue?"))return;
   sending=true;renderComposer();feedback("",false);
   const result=await gateway.post("/api/commands",{node_id:node.node_id,command_type:commandType,payload,priority,timeout_seconds:timeout,max_retries:retries});
   merge(result.command);
   if(selected===node.node_id){$("history-filter-select").value="ALL";render(true);}
  }catch(e){feedback(e.message);}
  finally{sending=false;renderComposer();}
 }
 async function commandAction(action,id){
  const cmd=cache(selected).commands.get(id);if(!cmd||actionBusy.has(id))return;
  if(action==="retry"&&active()){feedback("Wait for the active command before retrying.");return;}
  actionBusy.add(id);render();
  try{const response=await gateway.post("/api/commands/"+encodeURIComponent(id)+"/"+action,action==="cancel"?{reason:"Cancelled via Command Center"}:{});merge(response.command);}
  catch(e){feedback(e.message);}
  finally{actionBusy.delete(id);render();}
 }
 async function refresh(){await loadNodes();if(selected)await loadHistory(selected);}
 nodesList.onclick=e=>{const button=e.target.closest("[data-node-id]");if(button)selectNode(button.dataset.nodeId);};
 $("node-search-input").oninput=renderNodes;
 root.querySelectorAll("[data-node-filter]").forEach(button=>button.onclick=()=>{nodeFilter=button.dataset.nodeFilter;root.querySelectorAll("[data-node-filter]").forEach(b=>b.setAttribute("aria-pressed",String(b===button)));renderNodes();});
 $("history-filter-select").onchange=()=>render(true);
 $("cmd-refresh-btn").onclick=refresh;
 $("command-latest").onclick=()=>{conversation.scrollTop=conversation.scrollHeight;};
 $("command-back").onclick=()=>{root.classList.remove("conversation-open");$("node-search-input").focus();};
 $("command-older").onclick=()=>{if(selected){$("command-older").disabled=true;loadHistory(selected,true);}};
 conversation.addEventListener("scroll",()=>{if(selected&&conversation.scrollTop<12&&cache(selected).more&&cache(selected).loaded&&!cache(selected).busy)loadHistory(selected,true);},{passive:true});
 $("cmd-type-select").onchange=switchType;
 $("param-ping-msg").oninput=()=>{$("command-quick-input").value=$("param-ping-msg").value;};
 $("command-quick-input").oninput=()=>{$("param-ping-msg").value=$("command-quick-input").value;};
 $("command-quick-input").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();send();}};
 $("command-config-toggle").onclick=()=>{const panel=$("command-configuration");panel.hidden=!panel.hidden;$("command-config-toggle").setAttribute("aria-expanded",String(!panel.hidden));};
 $("btn-send-command").onclick=send;
 history.onclick=async e=>{
  const action=e.target.closest("[data-action]");if(action){commandAction(action.dataset.action,action.dataset.command);return;}
  const copy=e.target.closest("[data-copy]");if(copy){try{const cmd=cache(selected).commands.get(copy.dataset.copy);await navigator.clipboard.writeText(json(cmd.result));feedback("Response JSON copied.",false);}catch(_){feedback("Clipboard unavailable. Expand and select the response payload to copy.");}}
 };
 const update=payload=>{const cmd=payload?.command||payload;if(cmd?.command_id&&cmd.node_id)merge(cmd);};
 const nodeUpdate=payload=>{if(payload?.node_id){const index=nodes.findIndex(n=>n.node_id===payload.node_id);if(index>=0)nodes[index]={...nodes[index],...payload};else loadNodes();renderNodes();renderHeader();}};
 const connection=()=>{$("socket-status-text").textContent=socket?.connected?"Live command updates":"Polling command updates";};
 const reconnect=()=>{connection();refresh();};
 socket?.on("command_update",update);socket?.on("node_update",nodeUpdate);socket?.on("connect",reconnect);socket?.on("disconnect",connection);
 timer=setInterval(async()=>{if(document.hidden||pollBusy)return;pollBusy=true;try{await loadNodes();if(!socket?.connected&&selected)await loadHistory(selected);}finally{pollBusy=false;}},8000);
 const visible=()=>{if(!document.hidden)refresh();};document.addEventListener("visibilitychange",visible);
 window.addEventListener("pagehide",()=>{stopped=true;clearInterval(timer);socket?.off("command_update",update);socket?.off("node_update",nodeUpdate);socket?.off("connect",reconnect);socket?.off("disconnect",connection);document.removeEventListener("visibilitychange",visible);},{once:true});
 connection();switchType();loadNodes();
});

