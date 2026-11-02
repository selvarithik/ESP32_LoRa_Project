/* Read-only display of the existing operations feed. Never sends a device command. */
(function () {
 'use strict';
 function reportedFacts(data) {
  const masters=(Array.isArray(data?.devices)?data.devices:[]).filter(n=>n.device_role==='MASTER');
  if(masters.length!==1)return {gateway:masters.length?masters.length+' Masters':'Not reported',frequency:'Unverified',uptime:'Not reported',evidence:masters.length?'Select a Master in Device Management':'No Master report available'};
  const n=masters[0],r=n.reported||{},radio=n.diagnostics?.GET_RADIO_STATUS,channel=radio?.data?.observed?.channel;
  // E220-900 register mapping: channel 0 is 850.125 MHz, increments are 1 MHz.
  // A completed register read is historical evidence, not a verified RF link.
  const frequency=radio?.data?.public_settings_read===true&&Number.isInteger(channel)&&channel>=0&&channel<=83?(850.125+channel).toFixed(3)+' MHz':'Unverified';
  const seconds=r.uptime_s,valid=typeof seconds==='number'&&Number.isFinite(seconds)&&seconds>=0;
  const uptime=valid?(Math.floor(seconds/86400)?Math.floor(seconds/86400)+'d ':'')+Math.floor(seconds%86400/3600)+'h '+Math.floor(seconds%3600/60)+'m':'Not reported';
  return {gateway:n.node_id||'Not reported',frequency,uptime,evidence:n.health==='ONLINE'?'Last Master report':'Historical Master report',lastSeen:n.last_seen||'Unknown',radioTime:radio?.received_at||'Not queried'};
 }
 function connectionPath(data,profile) {
  const broker=data?.mqtt||{},masters=(Array.isArray(data?.devices)?data.devices:[]).filter(n=>n.device_role==='MASTER');
  const connected=broker.state==='connected'&&broker.tls_state==='VERIFIED';
  const reporting=connected&&masters.length===1&&masters[0].health==='ONLINE'&&masters[0].reported?.transport==='MQTT';
  return {provider:typeof profile?.provider==='string'?profile.provider.slice(0,40):'MQTT broker',broker:connected?'Connected · TLS verified':broker.state==='disconnected'?'Disconnected':'Connection not verified',master:masters.length===1?(masters[0].health==='ONLINE'?(reporting?'Reporting via MQTT':'Transport not verified'):'Offline / historical report'):masters.length?'Multiple Masters':'No Master report',connected,reporting,transport:profile?.tls===true?'MQTT over TLS':'Not reported',qos:profile?.qos_default===1?'QoS 1':typeof profile?.qos_default==='number'?'QoS '+profile.qos_default:'Not reported'};
 }
 if(typeof module==='object'&&module.exports)module.exports={reportedFacts,connectionPath};
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
  if(!document.getElementById('banner-gateway'))return;
  const facts=reportedFacts(event.detail);
  for(const key of ['gateway','frequency','uptime','evidence']){
   const element=document.getElementById('banner-'+key);element.textContent=facts[key];
   element.title=key==='frequency'?'E220 register query: '+(facts.radioTime||'Unavailable')+'. RF link not inferred.':key==='uptime'?'Last reported device uptime; last seen '+(facts.lastSeen||'Unknown'):facts[key];
  }
 });
})();
