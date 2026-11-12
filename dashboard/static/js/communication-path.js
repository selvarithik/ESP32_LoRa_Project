/* Read-only display of the existing operations feed. Never sends a device command. */
(function () {
 'use strict';
 function connectionPath(data,profile) {
  const broker=data?.mqtt||{},masters=(Array.isArray(data?.devices)?data.devices:[]).filter(n=>n.device_role==='MASTER');
  const connected=broker.state==='connected'&&broker.tls_state==='VERIFIED';
  const reporting=connected&&masters.length===1&&masters[0].health==='ONLINE'&&masters[0].reported?.transport==='MQTT';
  return {provider:typeof profile?.provider==='string'?profile.provider.slice(0,40):'MQTT broker',broker:connected?'Connected · TLS verified':broker.state==='disconnected'?'Disconnected':'Connection not verified',master:masters.length===1?(masters[0].health==='ONLINE'?(reporting?'Reporting via MQTT':'Transport not verified'):'Offline / historical report'):masters.length?'Multiple Masters':'No Master report',connected,reporting,transport:profile?.tls===true?'MQTT over TLS':'Not reported',qos:profile?.qos_default===1?'QoS 1':typeof profile?.qos_default==='number'?'QoS '+profile.qos_default:'Not reported'};
 }
 if(typeof module==='object'&&module.exports)module.exports={connectionPath};
 if(typeof document==='undefined')return;
 let current=null,profile=null;
 function renderPath(){
  if(!document.getElementById('path-provider'))return;
  const path=connectionPath(current,profile);
  for(const [id,value] of Object.entries({'path-provider':path.provider,'path-broker-state':path.broker,'path-master-state':path.master,'path-transport':path.transport,'path-qos':path.qos,'path-state':'Link states · not an execution receipt'}))document.getElementById(id).textContent=value;
  document.getElementById('path-broker-line').dataset.ready=String(path.connected);
  document.getElementById('path-master-line').dataset.ready=String(path.reporting);
 }
 document.addEventListener('DOMContentLoaded',()=>{
  if(!document.getElementById('path-provider'))return;
  // Read public active-profile metadata once; never stage or change a profile.
  fetch('/api/mqtt',{cache:'no-store',signal:AbortSignal.timeout(9000)}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{const p=d.active;profile=p?{provider:p.provider,tls:p.tls,qos_default:p.qos_default}:null;renderPath();}).catch(()=>{profile=null;renderPath();});
 });
 document.addEventListener('gateway:operations',event=>{
  current=event.detail;renderPath();
 });
})();
