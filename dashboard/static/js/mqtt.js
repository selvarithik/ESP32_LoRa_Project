(() => {
 'use strict';
 const $ = id => document.getElementById(id);
 const fields = ['profile_name','provider','host','port','mqtt_version','tls','ca_cert','username','password','client_id','keepalive_s','timeout_s','qos_default','topic_prefix','gateway_id'];
 const numbers = new Set(['port','keepalive_s','timeout_s','qos_default']);
 let state,busy=false;
 function controls(){if(!state)return;$('mqtt-test').disabled=busy||state.transaction.state!=='PENDING'||state.runtime.acl_status!=='OPERATOR_ASSERTED';$('mqtt-confirm').disabled=busy||state.transaction.state!=='READY_TO_CONFIRM'||state.runtime.state!=='connected';$('mqtt-cancel').disabled=busy||!state.pending||state.transaction.decision==='COMMIT';$('mqtt-form').querySelector('[type=submit]').disabled=busy||!!state.pending;}
 async function api(path, data) {
   const headers = {'Content-Type':'application/json'};
   headers['X-CSRF-Token'] = document.querySelector('meta[name="sensor-csrf"]')?.content || document.querySelector('meta[name="csrf-token"]')?.content || '';
   const response = await fetch(path, {method:data ? 'POST':'GET', headers, body:data ? JSON.stringify(data):undefined});
   const body = await response.json();
   if(response.status===401){location.assign('/login');throw new Error('Sign in required');}
   if (!response.ok){const error=new Error(body.error?.code || 'REQUEST_FAILED');error.field=body.error?.field;throw error;}
   return body;
 }
 async function load(preserveDraft=false) {
   const draft=preserveDraft?Object.fromEntries(fields.filter(k=>k!=='password').map(k=>[k,$('mqtt-'+k)?.value])):null;
   state = await api('/api/mqtt');
   $('mqtt-runtime').textContent = JSON.stringify(state.runtime,null,2);
   $('mqtt-comparison').textContent = state.comparison.message;
   $('mqtt-transaction').textContent = JSON.stringify(state.transaction,null,2);
   const active=state.active||{};
   $('mqtt-profile-summary').textContent='Active revision '+state.revision+' · '+(active.host||'Unconfigured')+':'+(active.port||'')+' · Client '+(active.client_id||'Unknown')+' · TLS certificate/hostname verification required · Permanent worker '+(state.runtime.last_error||state.runtime.state||'UNKNOWN');
   $('mqtt-fields').replaceChildren();
   const profile=state.pending || state.active || state.defaults || {};
   for (const key of fields) {
     const label=document.createElement('label');label.textContent=key;
     const input=document.createElement(key==='provider'?'select':key==='ca_cert'?'textarea':'input');input.name=key;input.id='mqtt-'+key;
     if(key==='provider'){for(const value of ['EMQX','HIVEMQ','MOSQUITTO','CUSTOM']){const option=document.createElement('option');option.value=value;option.textContent=value;input.append(option);}input.value=profile[key]||'EMQX';}
     else if (key==='tls') {input.type='checkbox';input.checked=true;input.disabled=true;}
     else {if(key!=='ca_cert')input.type=numbers.has(key)?'number':key==='password'?'password':'text';input.value=profile[key] ?? '';}
     if (key==='password') {input.value='';input.disabled=true;input.placeholder=state.secret_state.password_configured?'********':'Use local commissioning';}
     if (key==='mqtt_version'||key==='qos_default') input.readOnly=true;
     input.required=!['password','username'].includes(key);
     const ranges={port:[1,65535],keepalive_s:[15,300],timeout_s:[2,30]};if(ranges[key]){input.min=ranges[key][0];input.max=ranges[key][1];}
     const error=document.createElement('small');error.id='mqtt-error-'+key;error.className='access-feedback';input.setAttribute('aria-describedby',error.id);input.setAttribute('aria-invalid','false');
     label.append(input,error);$('mqtt-fields').append(label);
     if(draft&&draft[key]!==undefined&&key!=='tls')input.value=draft[key];
   }
   controls();
 }
 async function action(op, extra) {
   if(busy)return;busy=true;controls();$('mqtt-feedback').textContent='Operation pending…';
   for(const field of fields){$('mqtt-error-'+field).textContent='';$('mqtt-'+field).setAttribute('aria-invalid','false');}
   try {await api('/api/mqtt/'+op,{expected_revision:state.revision,...extra});await load();$('mqtt-feedback').textContent='State updated. Check transaction and connection evidence.';}
   catch(e){$('mqtt-feedback').textContent=e.message;if(fields.includes(e.field)){$('mqtt-error-'+e.field).textContent=e.message;$('mqtt-'+e.field).setAttribute('aria-invalid','true');$('mqtt-'+e.field).focus();}}
   finally{busy=false;controls();}
 }
 $('mqtt-form').onsubmit=e=>{e.preventDefault();const profile={};for(const key of fields){const el=$('mqtt-'+key);profile[key]=key==='tls'?true:numbers.has(key)?Number(el.value):el.value;}action('candidate',{profile});};
 $('mqtt-test').onclick=()=>action('test',{master_id:$('mqtt-master').value});
 $('mqtt-confirm').onclick=()=>action('confirm',{transaction_id:state.transaction.transaction_id});
 $('mqtt-cancel').onclick=()=>action('cancel',{transaction_id:state.transaction.transaction_id});
 $('mqtt-refresh').onclick=()=>load(true).then(()=>$('mqtt-feedback').textContent='Status refreshed; unsaved values retained. No connection or configuration operation started.').catch(e=>$('mqtt-feedback').textContent=e.message);
 load().catch(e=>$('mqtt-feedback').textContent=e.message);
})();
