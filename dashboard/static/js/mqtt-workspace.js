/* UI-only filtering and responsive panels; no MQTT operations. */
"use strict";
(()=>{const root=document.getElementById('mqtt-workspace');if(!root)return;
 const tabs=[...root.querySelectorAll('[data-mqtt-panel]')],narrow=matchMedia('(max-width:760px)');let active='profiles';
 function render(){for(const tab of tabs){const selected=tab.dataset.mqttPanel===active;tab.setAttribute('aria-pressed',String(selected));document.getElementById('mqtt-panel-'+tab.dataset.mqttPanel).hidden=narrow.matches&&!selected;}}
 tabs.forEach(button=>button.addEventListener('click',()=>{active=button.dataset.mqttPanel;render();}));
 narrow.addEventListener('change',render);render();
 document.getElementById('mqtt-topic-filter').addEventListener('input',event=>{const query=event.target.value.trim().toLowerCase();root.querySelectorAll('[data-topic-type]').forEach(row=>row.hidden=!row.dataset.topicType.toLowerCase().includes(query));});
})();

// Bounded in-memory view of the existing worker. No second MQTT client.
(()=>{const rows=document.getElementById('mqtt-feed-rows');if(!rows)return;
 const select=document.getElementById('mqtt-feed-topic'),state=document.getElementById('mqtt-feed-state');let cursor=0,history=[],busy=false;
 function render(){const entries=history.filter(row=>!select.value||row.message_type===select.value).slice(-60).reverse();gateway.patchHtml(rows,entries.map(row=>'<tr><td>'+gateway.escape(new Date(row.received_at*1000).toLocaleTimeString())+'</td><td title="'+gateway.escape(row.topic)+'"><strong>'+gateway.escape(row.message_type)+'</strong><small>'+gateway.escape(row.device_id)+'</small></td><td>'+gateway.escape(row.summary.status||row.summary.command_id||'Observed')+'</td></tr>').join('')||'<tr><td colspan="3">Waiting for matching validated traffic.</td></tr>');}
 async function load(){if(busy)return;busy=true;try{const data=await gateway.get('/api/mqtt/explorer?after='+cursor);if(data.sequence<cursor)history=[];cursor=data.sequence;history.push(...data.messages);history=history.slice(-200);state.textContent=data.connection_state;const selected=select.value;gateway.patchHtml(select,'<option value="">All authorized topics</option>'+Object.entries(data.topics).map(([kind,topic])=>'<option value="'+gateway.escape(kind)+'">'+gateway.escape(topic)+'</option>').join(''));select.value=selected;render();}catch(e){state.textContent=e.message;}finally{busy=false;}}
 select.onchange=render;gateway.watch(load,{interval:3000});
 document.getElementById('mqtt-explorer-probe').onclick=async()=>{const button=document.getElementById('mqtt-explorer-probe'),feedback=document.getElementById('mqtt-explorer-feedback');button.disabled=true;try{const current=await gateway.get('/api/mqtt');const result=await gateway.post('/api/mqtt/explorer/probe',{master_id:document.getElementById('mqtt-diagnostic-master').value,expected_revision:current.revision});feedback.textContent=result.state+' · '+result.message_id+' · '+result.delivery;}catch(e){feedback.textContent=e.message;}finally{button.disabled=false;}};
})();
