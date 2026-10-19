"use strict";
document.addEventListener("DOMContentLoaded", () => {
 const root=document.getElementById("sensor-management");if(!root)return;
 const $=id=>document.getElementById(id),esc=v=>gateway.escape(String(v??""));
 let nodes=[],sensors=[],templates=[],sources=[],actor=null,busy=false;
 const message=$("sensor-management-message"), csrf=()=>document.querySelector('meta[name="sensor-csrf"]')?.content||"";
 const identity=p=>p.node_id+"::"+p.parameter_id;
 async function api(url,method="GET",body){
  const response=await fetch(url,{method,cache:"no-store",signal:AbortSignal.timeout(12000),headers:{"Content-Type":"application/json","X-CSRF-Token":csrf()},body:body?JSON.stringify(body):undefined});
  const data=await response.json();if(!response.ok||data.success===false)throw Error(data.error||"Sensor request failed");return data;
 }
 const url=p=>"/api/nodes/"+encodeURIComponent(p.node_id)+"/parameters"+(p.parameter_id?"/"+encodeURIComponent(p.parameter_id):"");
 async function load(){
  const [catalog,nodeData,auth]=await Promise.all([api("/api/sensor-catalog"),api("/api/nodes"),fetch("/api/accounts").then(r=>r.ok?r.json():{}).catch(()=>({}))]);
  templates=catalog.templates;sources=catalog.sources;actor=auth.user||null;nodes=Array.isArray(nodeData)?nodeData:nodeData.nodes||[];
  const all=await Promise.all(nodes.map(async node=>{
   const [defs,latest]=await Promise.all([api("/api/nodes/"+encodeURIComponent(node.node_id)+"/parameters"),api("/api/nodes/"+encodeURIComponent(node.node_id)+"/parameters/latest")]);
   const live=latest.parameters||[];
   return (defs.parameters||[]).map(p=>({...p,...live.find(v=>v.parameter_id===p.parameter_id),node_id:node.node_id,node_name:node.name,node_status:node.status}));
  }));sensors=all.flat();render();
 }
 function filtered(){
  const q=$("sensor-management-search").value.toLowerCase(),cat=$("sensor-management-category").value,filter=$("sensor-management-filter").value,sort=$("sensor-management-sort").value;
  return sensors.filter(p=>(!q||[p.parameter_name,p.parameter_id,p.sensor_id,p.node_name].join(" ").toLowerCase().includes(q))&&(!cat||SensorUI.config(p).category===cat)&&(!filter||filter==="enabled"&&p.enabled||filter==="visible"&&p.display_enabled||filter==="unavailable"&&(!p.timestamp||!SensorUI.config(p).source_field))).sort((a,b)=>sort==="name"?a.parameter_name.localeCompare(b.parameter_name):sort==="node"?a.node_id.localeCompare(b.node_id):(SensorUI.config(a).position||0)-(SensorUI.config(b).position||0));
 }
 function render(){
  const writable=actor&&["administrator","creator"].includes(actor.role);
  $("sensor-add").disabled=!writable;
  $("sensor-management-counts").innerHTML=[["Total sensors",sensors.length],["Enabled",sensors.filter(p=>p.enabled).length],["Dashboard widgets",sensors.filter(p=>p.display_enabled&&p.enabled).length],["Unavailable / unconfigured",sensors.filter(p=>!p.timestamp||!SensorUI.config(p).source_field).length]].map(([label,n])=>'<span>'+label+' <strong>'+n+'</strong></span>').join("");
  gateway.patchHtml($("sensor-management-rows"),filtered().map(p=>{
   const node=nodes.find(n=>n.node_id===p.node_id),c=SensorUI.config(p);
   const actions=[["details","Details"],["test","Test source"],...(writable?[["edit","Edit / Data source"],["visible",p.display_enabled?"Remove from Dashboard":"Add to Dashboard"],["enable",p.enabled?"Disable":"Enable"],["up","↑"],["down","↓"],["delete","Delete"]]:[])];
   return '<tr data-id="'+esc(identity(p))+'" data-sensor-key="'+esc(identity(p))+'"><td><strong>'+esc(p.parameter_name)+'</strong><br><small>'+esc(p.sensor_id||p.parameter_id)+'</small></td><td>'+esc(p.node_name||p.node_id)+'<br><small>'+esc(c.source||"node_telemetry")+" · "+esc(c.source_field||p.parameter_id)+'</small></td><td>'+esc(p.enabled?"Enabled":"Disabled")+'<br>'+esc(p.display_enabled?"Widget selected":"Widget hidden")+'<br>'+esc(SensorUI.status(p,node))+'</td><td>'+esc(SensorUI.value(p))+" "+esc(p.unit)+'</td><td>'+actions.map(([action,label])=>'<button class="btn" type="button" data-sensor-action="'+action+'" title="'+(action==="up"?"Move widget up":action==="down"?"Move widget down":esc(label))+'">'+label+'</button>').join("")+'</td></tr>';
  }).join("")||'<tr><td colspan="5">No configured sensors match this selection.</td></tr>');
  const q=$("sensor-management-search").value.toLowerCase(),category=$("sensor-management-category").value;
  $("sensor-template-catalog").innerHTML=templates.map((p,i)=>({p,i})).filter(({p})=>(!q||p.parameter_type.toLowerCase().includes(q))&&(!category||p.category===category)).map(({p,i})=>'<button type="button" class="sensor-template" data-template="'+i+'" '+(!writable?"disabled":"")+'>'+esc(p.parameter_type)+'<small>'+esc(p.parameter_id)+" · "+esc(p.unit)+'</small></button>').join("");
  $("sensor-source-limitations").textContent="Available: normalized node telemetry. Direct MQTT subscriptions, direct Modbus polling and direct gateway diagnostic sources are unavailable in this implementation.";
  if(!writable)message.innerHTML='Viewing sensors. <a href="/accounts">Sign in as an administrator or creator</a> to configure them.';
 }
 function notify(error){message.textContent=error.message||String(error);}
 async function test(p){
  const result=await api("/api/nodes/"+encodeURIComponent(p.node_id)+"/parameters/latest");
  const field=SensorUI.config(p).source_field||p.parameter_id;
  const found=(result.parameters||[]).find(x=>x.parameter_id===field);
  return found?.timestamp?{ok:true,message:"Stored reading observed for "+field+": "+SensorUI.value(found)+" "+(found.unit||"")+" at "+new Date(found.timestamp).toLocaleString()+". "+SensorUI.status(found,nodes.find(n=>n.node_id===p.node_id))+". This does not prove a current hardware connection."}:{ok:false,message:"No stored reading found for "+field+". Waiting for the configured node to publish that field. A direct hardware connection test is unavailable."};
 }
 $("sensor-management-rows").onclick=async e=>{
  const button=e.target.closest("[data-sensor-action]");if(!button||busy)return;
  const p=sensors.find(x=>identity(x)===button.closest("tr").dataset.sensorKey);if(!p)return;
  try{
   const action=button.dataset.sensorAction;
   if(action==="details"){SensorUI.open(nodes.find(n=>n.node_id===p.node_id),p,()=>sensors.filter(x=>x.node_id===p.node_id));return;}
   if(action==="test"){message.textContent=(await test(p)).message;return;}
   if(action==="edit"){wizard(p);return;}
   if(action==="delete"&&!confirm("Delete "+p.parameter_name+"? Sensors with historical readings must be disabled instead."))return;
   busy=true;button.disabled=true;
   if(action==="delete")await api(url(p),"DELETE");
   else if(action==="visible")await api(url(p),"PUT",{display_enabled:!p.display_enabled});
   else if(action==="enable")await api(url(p)+"/enable","POST",{enabled:!p.enabled});
   else if(action==="up"||action==="down"){
    const ordered=filtered(),i=ordered.indexOf(p),other=ordered[i+(action==="up"?-1:1)];if(other){const temp=ordered[i];ordered[i]=other;ordered[i+(action==="up"?-1:1)]=temp;for(let n=0;n<ordered.length;n++)await api(url(ordered[n]),"PUT",{widget_config:{...SensorUI.config(ordered[n]),position:n}});}
   }
   await load();message.textContent="Sensor configuration saved.";
  }catch(error){notify(error);}finally{busy=false;button.disabled=false;}
 };
 for(const id of ["sensor-management-search","sensor-management-category","sensor-management-filter","sensor-management-sort"])$(id).addEventListener(id.includes("search")?"input":"change",render);
 $("sensor-template-catalog").onclick=e=>{const button=e.target.closest("[data-template]");if(button)wizard(null,templates[Number(button.dataset.template)]);};
 $("sensor-add").onclick=()=>wizard();
 function wizard(existing=null,preset=null){
  if(!nodes.length){notify("Add a node before configuring a sensor.");return;}
  preset=preset||templates[0];let step=0,editing=Boolean(existing);
  const c=existing?SensorUI.config(existing):{...preset,source:"node_telemetry",source_field:preset.parameter_id,scale:1,offset:0,stale_timeout:10,reporting_interval:2,position:sensors.length};
  const p=existing||{parameter_name:preset.parameter_type,parameter_id:preset.parameter_id,sensor_id:preset.parameter_id,parameter_type:preset.parameter_type,data_type:preset.data_type,unit:preset.unit,decimal_places:2,enabled:true,display_enabled:false,graph_enabled:true,node_id:nodes[0].node_id};
  const overlay=document.createElement("div");overlay.className="sensor-detail-overlay modal-overlay";
  const input=(name,label,value="",type="text",extra="")=>'<label>'+label+'<input class="input" name="'+name+'" type="'+type+'" value="'+esc(value??"")+'" '+extra+'></label>';
  overlay.innerHTML='<form class="sensor-detail-dialog sensor-editor"><header><h2>'+ (editing?"Edit sensor":"Add Sensor")+'</h2><button type="button" class="btn" data-close-telemetry aria-label="Close sensor editor">×</button></header><p class="wizard-progress"></p><p role="status" class="wizard-error"></p>'+
   '<fieldset data-step="0"><legend>Basic details</legend><div class="management-fields">'+input("parameter_name","Sensor name",p.parameter_name,"text","required maxlength=100")+input("parameter_id","Payload parameter ID",p.parameter_id,"text",'required pattern="[A-Za-z0-9_.-]{1,80}" '+(editing?"readonly":""))+input("sensor_id","Sensor identifier",p.sensor_id,"text","required maxlength=100")+input("parameter_type","Sensor type",p.parameter_type,"text","required")+input("description","Description",p.description,"text","maxlength=500")+input("unit","Unit",p.unit)+
   '<label>Data type<select class="input" name="data_type">'+["FLOAT","DOUBLE","INT","UINT","UINT32","TEXT","ENUM","BOOL"].map(x=>'<option '+(x===p.data_type?"selected":"")+'>'+x+'</option>').join("")+'</select></label><label>Category<select class="input" name="category">'+["core","environment","network","custom"].map(x=>'<option '+(x===(c.category||"custom")?"selected":"")+'>'+x+'</option>').join("")+'</select></label><label>Icon<select class="input" name="icon">'+["thermometer","gauge","battery","signal","zap","droplet","sun","wind","activity","map-pin","clock","network","cpu"].map(x=>'<option '+(x===c.icon?"selected":"")+'>'+x+'</option>').join("")+'</select></label>'+input("color","Accent and chart color",c.color||"#2563EB","color")+'</div></fieldset>'+
   '<fieldset data-step="1" hidden><legend>Device and data source</legend><div class="management-fields"><label>Node<select class="input" name="node_id" '+(editing?"disabled":"")+'>'+nodes.map(n=>'<option value="'+esc(n.node_id)+'" '+(n.node_id===p.node_id?"selected":"")+'>'+esc(n.name||n.node_id)+'</option>').join("")+'</select></label><label>Data source<select class="input" name="source">'+sources.map(s=>'<option value="'+esc(s.id)+'">'+esc(s.name)+'</option>').join("")+'</select></label></div><p>Transport is configured on the existing Nodes page. Direct MQTT and Modbus adapters are unavailable.</p></fieldset>'+
   '<fieldset data-step="2" hidden><legend>Telemetry field mapping</legend><div class="management-fields">'+input("source_field","Existing payload field",c.source_field||p.parameter_id,"text",'required pattern="[A-Za-z0-9_.-]{1,80}" list="sensor-source-fields"')+'<datalist id="sensor-source-fields"></datalist>'+input("scale","Scale",c.scale??1,"number",'step="any" required')+input("offset","Offset",c.offset??0,"number",'step="any" required')+'</div><p>Numeric conversion: reading × scale + offset. The source field is read from the same node payload.</p></fieldset>'+
   '<fieldset data-step="3" hidden><legend>Widget display and thresholds</legend><div class="management-fields"><label>Widget type<select class="input" name="widget_type">'+["numeric","state","gps"].map(x=>'<option '+(x===(c.widget_type||"numeric")?"selected":"")+'>'+x+'</option>').join("")+'</select></label>'+input("decimal_places","Decimal precision",p.decimal_places,"number",'min=0 max=8 required')+input("reporting_interval","Expected reporting interval (seconds)",c.reporting_interval||2,"number","min=1 max=86400 required")+input("stale_timeout","Stale timeout (seconds)",c.stale_timeout||10,"number","min=1 max=604800 required")+input("min_value","Valid minimum",p.min_value,"number",'step="any"')+input("max_value","Valid maximum",p.max_value,"number",'step="any"')+input("warning_low","Warning low",c.warning_low,"number",'step="any"')+input("warning_high","Warning high",c.warning_high,"number",'step="any"')+input("low_alarm","Critical low",p.low_alarm,"number",'step="any"')+input("high_alarm","Critical high",p.high_alarm,"number",'step="any"')+'</div>'+[["enabled","Enable sensor",p.enabled],["display_enabled","Add to dashboard",p.display_enabled],["alarm_enabled","Enable critical alarms",p.alarm_enabled]].map(([key,label,checked])=>'<label class="management-check"><input name="'+key+'" type="checkbox" '+(checked?"checked":"")+'>'+label+'</label>').join("")+'</fieldset>'+
   '<fieldset data-step="4" hidden><legend>Validate and save</legend><p class="wizard-review"></p><button type="button" class="btn" id="sensor-wizard-test">Test data source</button><p class="wizard-test-result"></p></fieldset><div class="wizard-actions"><button type="button" class="btn" id="sensor-wizard-back">Back</button><button type="button" class="btn" id="sensor-wizard-next">Next</button><button class="btn btn-primary" id="sensor-wizard-save" hidden>Save sensor</button></div></form>';
  const form=overlay.querySelector("form"),error=overlay.querySelector(".wizard-error"),origin=document.activeElement,oldOverflow=document.body.style.overflow;
  const close=()=>{document.removeEventListener("keydown",key);overlay.remove();document.body.style.overflow=oldOverflow;if(origin?.isConnected)origin.focus();};
  const key=e=>{if(e.key==="Escape")close();};
  overlay.onclick=e=>{if(e.target===overlay||e.target.closest("[data-close-telemetry]"))close();};
  function fields(){overlay.querySelector("datalist").innerHTML=sensors.filter(x=>x.node_id===form.elements.node_id.value).map(x=>'<option value="'+esc(x.parameter_id)+'">'+esc(x.parameter_name)+'</option>').join("");}
  function show(){form.querySelectorAll("[data-step]").forEach((el,i)=>{el.hidden=i!==step;el.disabled=i!==step;});form.querySelector(".wizard-progress").textContent="Step "+(step+1)+" of 5";form.querySelector("#sensor-wizard-back").disabled=step===0;form.querySelector("#sensor-wizard-next").hidden=step===4;form.querySelector("#sensor-wizard-save").hidden=step!==4;form.querySelector(".wizard-review").textContent=form.elements.parameter_name.value+" · "+form.elements.parameter_id.value+" · "+form.elements.node_id.value;fields();}
  function payload(){
   const values={};for(const el of form.elements){if(el.name)values[el.name]=el.type==="checkbox"?el.checked:el.value;}
   const data={};for(const key of ["parameter_name","parameter_id","sensor_id","parameter_type","data_type","unit","description","enabled","display_enabled","alarm_enabled"])data[key]=values[key];
   data.decimal_places=Number(values.decimal_places);data.graph_enabled=true;
   for(const key of ["min_value","max_value","low_alarm","high_alarm"])data[key]=values[key]===""?null:Number(values[key]);
   data.widget_config={category:values.category,icon:values.icon,color:values.color,widget_type:values.widget_type,source:values.source,source_field:values.source_field,scale:Number(values.scale),offset:Number(values.offset),stale_timeout:Number(values.stale_timeout),reporting_interval:Number(values.reporting_interval),position:c.position||0,warning_low:values.warning_low===""?null:Number(values.warning_low),warning_high:values.warning_high===""?null:Number(values.warning_high)};
   return data;
  }
  form.elements.node_id.onchange=fields;
  form.querySelector("#sensor-wizard-back").onclick=()=>{step=Math.max(0,step-1);show();};
  form.querySelector("#sensor-wizard-next").onclick=()=>{if(!form.reportValidity())return;step=Math.min(4,step+1);show();};
  form.querySelector("#sensor-wizard-test").onclick=async()=>{try{const data=payload();form.querySelector(".wizard-test-result").textContent=(await test({...data,node_id:form.elements.node_id.value})).message;}catch(e){error.textContent=e.message;}};
  form.onsubmit=async e=>{e.preventDefault();if(step!==4)return;const save=form.querySelector("#sensor-wizard-save");save.disabled=true;try{const data=payload(),nodeId=form.elements.node_id.value;await api("/api/nodes/"+encodeURIComponent(nodeId)+"/parameters"+(editing?"/"+encodeURIComponent(p.parameter_id):""),editing?"PUT":"POST",data);close();await load();message.textContent="Sensor saved.";}catch(e){error.textContent=e.message;}finally{save.disabled=false;}};
  document.body.append(overlay);document.body.style.overflow="hidden";document.addEventListener("keydown",key);show();form.elements.parameter_name.focus();
 }
 gateway.watch(load, {events:["connect", "node_update", "telemetry_update"], enabled:()=>!busy&&!document.querySelector(".sensor-editor")});
});
